"""
app/api/routes/websocket.py
────────────────────────────
Real-time WebSocket endpoint for Live Classroom.

Audio chunk processing guarantees:
  - Per-room asyncio.Lock: only one Whisper call runs per room at a time
  - chunk_id deduplication: recently processed chunk IDs are cached (ring buffer of 20)
    to reject accidental re-submissions from network retries or race conditions
  - sequence numbering: each transcript event carries a monotonic sequence number per room
  - Minimum audio size guard: chunks < 8 KB are silently rejected
  - is_final: True on every transcript (all events are final — no interim streaming)
"""
import asyncio
import base64
import collections
import logging
import os
import subprocess
import tempfile
import uuid
import wave
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token
from app.core.rbac import verify_lecture_control_role_string
from app.database.database import SessionLocal
from app.models.user import User
from app.services.whisper_service import WhisperSTTService
from app.services.session_store import session_store
from app.services.transcript_assembler import transcript_assembler
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

def _save_and_append_debug_audio(room_id: str, chunk_id: str, audio_bytes: bytes, mime_type: str):
    """Saves raw audio received from the microphone before STT (Requirement 5)."""
    try:
        debug_base = os.path.join(os.getcwd(), "uploads", "debug_audio")
        os.makedirs(debug_base, exist_ok=True)
        sess_dir = os.path.join(debug_base, room_id)
        os.makedirs(sess_dir, exist_ok=True)
        
        ext = ".wav" if "wav" in mime_type else ".webm"
        chunk_file = os.path.join(sess_dir, f"chunk_{chunk_id}{ext}")
        with open(chunk_file, "wb") as f:
            f.write(audio_bytes)
            
        master_wav = os.path.join(debug_base, f"{room_id}_microphone_audio.wav")
        converted_fd, temp_wav = tempfile.mkstemp(suffix=".wav")
        os.close(converted_fd)
        
        cmd = [
            "ffmpeg", "-y", "-i", chunk_file,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            temp_wav
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        
        if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 100:
            with wave.open(temp_wav, "rb") as wf_in:
                frames = wf_in.readframes(wf_in.getnframes())
                params = wf_in.getparams()
                
            if not os.path.exists(master_wav):
                with wave.open(master_wav, "wb") as wf_out:
                    wf_out.setparams(params)
                    wf_out.writeframes(frames)
            else:
                with wave.open(master_wav, "rb") as wf_exist:
                    existing_frames = wf_exist.readframes(wf_exist.getnframes())
                    existing_params = wf_exist.getparams()
                with wave.open(master_wav, "wb") as wf_out:
                    wf_out.setparams(existing_params)
                    wf_out.writeframes(existing_frames + frames)
            
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        logger.info(f"[DebugAudio] Raw microphone audio saved: {chunk_file} | Master WAV: {master_wav}")
    except Exception as e:
        logger.warning(f"[DebugAudio] Notice saving debug audio: {e}")


CONTROL_EVENT_TYPES = {
    "lecture_status",
    "recording_status",
    "start_lecture",
    "stop_lecture",
    "start_recording",
    "stop_recording",
}

# Minimum bytes to forward to Whisper (valid WebM container + audio header is ~500 bytes)
_MIN_AUDIO_BYTES = 500

# Number of recent chunk IDs to remember per room for deduplication
_CHUNK_ID_CACHE_SIZE = 20


class ConnectionManager:
    """
    Manages active WebSocket connections for live classrooms with room-level broadcasting.

    Per-room state:
      active_rooms       : websocket list
      room_participants  : participant info list
      room_locks         : asyncio.Lock — one Whisper call per room at a time
      room_sequences     : monotonic transcript sequence counter per room
      room_chunk_ids     : deque of recently seen chunk IDs (ring buffer)
    """

    def __init__(self):
        self.active_rooms: Dict[str, List[WebSocket]] = {}
        self.room_participants: Dict[str, List[dict]] = {}
        self.room_locks: Dict[str, asyncio.Lock] = {}
        self.room_sequences: Dict[str, int] = {}
        self.room_chunk_ids: Dict[str, collections.deque] = {}
        self.room_tail_pcm: Dict[str, bytes] = {}

    def _ensure_room(self, room_id: str):
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
            self.room_participants[room_id] = []
            self.room_locks[room_id] = asyncio.Lock()
            self.room_sequences[room_id] = 0
            self.room_chunk_ids[room_id] = collections.deque(maxlen=_CHUNK_ID_CACHE_SIZE)

    async def connect(self, websocket: WebSocket, room_id: str, user_info: Optional[dict] = None):
        await websocket.accept()
        self._ensure_room(room_id)

        if websocket not in self.active_rooms[room_id]:
            self.active_rooms[room_id].append(websocket)

        if user_info:
            # Avoid duplicate user entry
            self.room_participants[room_id] = [
                p for p in self.room_participants[room_id]
                if p.get("id") != user_info.get("id")
            ]
            self.room_participants[room_id].append(user_info)

        logger.info(
            f"[WebSocket] Client connected to room '{room_id}'. "
            f"Total in room: {len(self.active_rooms[room_id])}"
        )
        logger.info(f"[LiveAudio] websocket connected: session_id={room_id}")
        logger.info("[Backend] Audio WebSocket connected")
        logger.info(f"[Backend] Session: {room_id}")
        logger.info("[AudioWS] Client connected")
        logger.info(f"[AudioWS] Session ID: {room_id}")

        # Broadcast updated participants list
        await self.broadcast(room_id, {
            "type": "room_state",
            "participants": self.room_participants[room_id],
            "count": len(self.active_rooms[room_id])
        })

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: Optional[str] = None):
        if room_id in self.active_rooms:
            if websocket in self.active_rooms[room_id]:
                self.active_rooms[room_id].remove(websocket)
            if not self.active_rooms[room_id]:
                # Clean up active room connections and locks
                del self.active_rooms[room_id]
                self.room_locks.pop(room_id, None)
                self.room_chunk_ids.pop(room_id, None)

        if room_id in self.room_participants and user_id:
            self.room_participants[room_id] = [
                p for p in self.room_participants[room_id]
                if p.get("id") != user_id
            ]
            if not self.room_participants[room_id]:
                del self.room_participants[room_id]

        logger.info(f"[WebSocket] Client disconnected from room '{room_id}'.")

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            disconnected_sockets = []
            active_connections = list(self.active_rooms[room_id])
            for connection in active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"[WebSocket] Error sending to socket in room '{room_id}': {e}")
                    disconnected_sockets.append(connection)
            for ws in disconnected_sockets:
                self.disconnect(ws, room_id)

    def is_duplicate_chunk(self, room_id: str, chunk_id: str) -> bool:
        """Returns True if this chunk_id was already processed for this room."""
        self._ensure_room(room_id)
        if chunk_id in self.room_chunk_ids[room_id]:
            return True
        self.room_chunk_ids[room_id].append(chunk_id)
        return False

    def next_sequence(self, room_id: str) -> int:
        """Returns next monotonic sequence number for this room."""
        self._ensure_room(room_id)
        self.room_sequences[room_id] += 1
        return self.room_sequences[room_id]

    def get_room_lock(self, room_id: str) -> asyncio.Lock:
        """Returns the asyncio.Lock for this room."""
        self._ensure_room(room_id)
        return self.room_locks[room_id]

    def get_tail_pcm(self, room_id: str) -> Optional[bytes]:
        """Gets the trailing ~1.0s PCM frames of the previous chunk for overlap."""
        return self.room_tail_pcm.get(room_id)

    def set_tail_pcm(self, room_id: str, pcm: Optional[bytes]):
        """Sets or clears the trailing PCM frames for room overlap."""
        if pcm:
            self.room_tail_pcm[room_id] = pcm
        else:
            self.room_tail_pcm.pop(room_id, None)

    def reset_room_stt_state(self, room_id: str):
        """Cleans STT overlap buffer and transcript assembly state for new session."""
        self.room_tail_pcm.pop(room_id, None)
        transcript_assembler.reset_session(room_id)
        logger.info(f"[ConnectionManager] Reset STT state & assembler for room '{room_id}'")


manager = ConnectionManager()


@router.websocket("/classroom/{room_id}")
@router.websocket("/live-classroom/{room_id}/audio")
async def websocket_classroom_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time classroom updates, chat, hand-raising, and STT audio streaming.
    Enforces RBAC permissions for lecture control events.
    """
    user_info = None
    user_role = "Student"

    if token:
        try:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                user_id_str = payload.get("sub")
                user_role = payload.get("role", "Student")

                # Retrieve updated user role directly from PostgreSQL if available
                try:
                    user_uuid = uuid.UUID(user_id_str)
                    async with SessionLocal() as session:
                        res = await session.execute(select(User).where(User.id == user_uuid))
                        user_record = res.scalar_one_or_none()
                        if user_record:
                            user_role = user_record.role
                            user_info = {
                                "id": str(user_record.id),
                                "email": user_record.email,
                                "role": user_record.role
                            }
                except Exception as e:
                    logger.warning(f"[WebSocket] Failed to lookup DB user for WS token: {e}")

                if not user_info:
                    user_info = {
                        "id": user_id_str,
                        "email": payload.get("email", "User"),
                        "role": user_role
                    }
        except Exception as err:
            logger.warning(f"[WebSocket] Error validating WebSocket token: {err}")

    await manager.connect(websocket, room_id, user_info)
    user_id = user_info.get("id") if user_info else None

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            # Validate lecture control authorization for restricted events
            if event_type in CONTROL_EVENT_TYPES:
                if not verify_lecture_control_role_string(user_role):
                    logger.warning(
                        f"[WebSocket] Unauthorized control event '{event_type}' "
                        f"by role '{user_role}'."
                    )
                    await websocket.send_json({
                        "type": "error",
                        "status": 403,
                        "detail": "Only Teachers or Administrators can control lectures."
                    })
                    continue

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif event_type == "chat":
                await manager.broadcast(room_id, {
                    "type": "chat",
                    "id": data.get("id"),
                    "sender": data.get("sender", "Anonymous"),
                    "content": data.get("content", ""),
                    "time": data.get("time"),
                    "isTeacher": data.get("isTeacher", False)
                })

            elif event_type == "hand_raise":
                await manager.broadcast(room_id, {
                    "type": "hand_raise",
                    "userId": data.get("userId"),
                    "userName": data.get("userName"),
                    "handRaised": data.get("handRaised", False)
                })

            elif event_type in ("lecture_status", "start_lecture", "stop_lecture"):
                if event_type == "start_lecture":
                    manager.reset_room_stt_state(room_id)
                await manager.broadcast(room_id, {
                    "type": "lecture_status",
                    "status": data.get("status", event_type == "start_lecture"),
                    "event": data.get("event", event_type),
                    "title": data.get("title"),
                    "slide": data.get("slide")
                })

            elif event_type in ("recording_status", "start_recording", "stop_recording"):
                if event_type == "start_recording" or (event_type == "recording_status" and data.get("isRecording")):
                    manager.reset_room_stt_state(room_id)
                await manager.broadcast(room_id, {
                    "type": "recording_status",
                    "isRecording": data.get("isRecording", event_type == "start_recording"),
                    "recordingId": data.get("recordingId")
                })

            elif event_type == "audio_chunk":
                base64_data = data.get("data")
                mime_type = data.get("mimeType", "audio/webm")
                chunk_id = data.get("chunk_id") or str(uuid.uuid4())
                speaker = data.get("speaker") or (
                    user_info.get("email", "Teacher").split("@")[0]
                    if user_info else "Teacher"
                )
                is_teacher = data.get("isTeacher", True)

                if not base64_data:
                    continue

                # ── Deduplication: reject already-processed chunk IDs ──────────
                if manager.is_duplicate_chunk(room_id, chunk_id):
                    logger.warning(
                        f"[WebSocket] Duplicate chunk_id='{chunk_id}' received for "
                        f"room '{room_id}' — skipping."
                    )
                    continue

                try:
                    if "," in base64_data:
                        base64_data = base64_data.split(",", 1)[1]
                    audio_bytes = base64.b64decode(base64_data)
                    byte_count = len(audio_bytes)

                    logger.info(f"[SESSION] ACTIVE_SESSION_ID={room_id}")
                    logger.info(f"[TRANSCRIPT] RECORDING_SESSION_ID={room_id}")
                    logger.info(f"[STT] AUDIO_RECEIVED session_id={room_id} bytes={byte_count}")
                    logger.info(f"[STT] AUDIO_SIZE: {byte_count}")
                    logger.info(f"[STT] SESSION_ID: {room_id}")
                    logger.info(f"[LiveAudio] audio received: {byte_count} bytes (chunk_id={chunk_id}, session_id={room_id})")

                    # ── Minimum size guard (discards empty corrupted packets < 500 bytes) ──
                    if byte_count < _MIN_AUDIO_BYTES:
                        logger.info(
                            f"[WebSocket] chunk_id={chunk_id} too small ({byte_count} bytes < {_MIN_AUDIO_BYTES}) "
                            f"— skipping."
                        )
                        continue

                    # Send status update so frontend knows audio reached backend STT
                    try:
                        await websocket.send_json({
                            "type": "stt_status",
                            "status": "transcribing",
                            "session_id": room_id,
                            "chunk_id": chunk_id,
                        })
                    except Exception:
                        pass

                    # ── Save/export raw audio received from microphone before STT (Requirement 5) ──
                    loop = asyncio.get_running_loop()
                    loop.run_in_executor(None, _save_and_append_debug_audio, room_id, chunk_id, audio_bytes, mime_type)

                    seq = manager.next_sequence(room_id)
                    overlap_pcm = manager.get_tail_pcm(room_id)

                    # ── Per-room lock: one Whisper call at a time per room ────
                    room_lock = manager.get_room_lock(room_id)

                    logger.info(f"[STT] TRANSCRIPTION_STARTED session_id={room_id} seq={seq}")
                    logger.info(f"[LiveAudio] sending audio to STT: chunk_id={chunk_id}")
                    async with room_lock:
                        whisper_res = await loop.run_in_executor(
                            None,
                            WhisperSTTService.transcribe_audio_chunk,
                            audio_bytes,
                            mime_type,
                            chunk_id,
                            room_id,
                            seq,
                            overlap_pcm,
                        )

                    raw_transcribed_text = None
                    new_tail_pcm = None
                    if isinstance(whisper_res, tuple):
                        raw_transcribed_text, new_tail_pcm = whisper_res
                    elif isinstance(whisper_res, str):
                        raw_transcribed_text = whisper_res

                    if new_tail_pcm:
                        manager.set_tail_pcm(room_id, new_tail_pcm)

                    if raw_transcribed_text and raw_transcribed_text.strip():
                        # Intelligent transcript assembly: deduplicate overlap and repair cut words
                        cleaned_incremental_text, full_assembled_text = transcript_assembler.assemble_chunk(
                            room_id, raw_transcribed_text
                        )
                        text_to_broadcast = cleaned_incremental_text or raw_transcribed_text

                        logger.info(f"[STT] RAW_WHISPER_TEXT=\"{raw_transcribed_text}\"")
                        logger.info(f"[STT] CLEANED_ASSEMBLED_TEXT=\"{text_to_broadcast}\"")
                        logger.info(f"[STT] FULL_SESSION_TRANSCRIPT=\"{full_assembled_text}\"")
                        logger.info(f"[STT] TRANSCRIPTION_COMPLETED text=\"{text_to_broadcast}\"")
                        logger.info(f"[STT] TRANSCRIPT_TEXT: {text_to_broadcast}")
                        logger.info("[STT] TRANSCRIPT_TYPE: final")
                        logger.info("[STT] TRANSCRIPT_SENT_TO_FRONTEND type=final")
                        logger.info(f"[LiveAudio] STT result received: \"{text_to_broadcast}\" (chunk_id={chunk_id})")
                        
                        # Persist transcript entry to PostgreSQL & in-memory session store (Requirement 9: both raw & cleaned)
                        await session_store.persist_transcript_entry(
                            session_id=room_id,
                            speaker=speaker,
                            text=text_to_broadcast,
                            is_teacher=is_teacher,
                            chunk_id=chunk_id,
                            sequence=seq,
                            raw_text=raw_transcribed_text
                        )
                        logger.info(f"[TRANSCRIPT] SAVED SESSION_ID={room_id}")
                        transcript_msg = {
                            "type": "transcript",
                            "transcript_type": "final",
                            "lecture_session_id": room_id,
                            "session_id": room_id,
                            "id": str(uuid.uuid4()),
                            "chunk_id": chunk_id,
                            "sequence": seq,
                            "speaker": speaker,
                            "timestamp": datetime.now().isoformat(),
                            "time": datetime.now().strftime("%I:%M %p"),
                            "text": text_to_broadcast,
                            "raw_text": raw_transcribed_text,
                            "assembled_text": full_assembled_text,
                            "isTeacher": is_teacher,
                            "is_final": True,
                        }
                        logger.info(
                            f"TRANSCRIPT_EVENT_SENT session_id={room_id} seq={seq} "
                            f"text_length={len(text_to_broadcast)} is_final=True speaker='{speaker}'"
                        )
                        logger.info(f"[LiveAudio] transcript sent to client: \"{text_to_broadcast}\" (seq={seq})")
                        await manager.broadcast(room_id, transcript_msg)
                        logger.info(f"[WebSocket] Transcript seq={seq} broadcasted to room '{room_id}'")
                    else:
                        try:
                            await websocket.send_json({
                                "type": "stt_status",
                                "status": "listening",
                                "session_id": room_id,
                                "chunk_id": chunk_id,
                            })
                        except Exception:
                            pass

                except Exception as audio_err:
                    logger.error(
                        f"[WebSocket] Error processing audio chunk_id={chunk_id} "
                        f"in room '{room_id}': {audio_err}"
                    )
                    try:
                        await websocket.send_json({
                            "type": "stt_error",
                            "chunk_id": chunk_id,
                            "message": f"Speech-to-text processing failed: {str(audio_err)}"
                        })
                    except Exception:
                        pass

            else:
                # Broadcast non-control events to room
                await manager.broadcast(room_id, data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)
        await manager.broadcast(room_id, {
            "type": "user_left",
            "userId": user_id,
            "participants": manager.room_participants.get(room_id, [])
        })
    except Exception as e:
        logger.error(f"[WebSocket] Unhandled error in room '{room_id}': {e}", exc_info=True)
        manager.disconnect(websocket, room_id, user_id)
