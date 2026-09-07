import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db, get_current_user, require_lecture_control_permission
from app.models.user import User
from app.models.recording import Recording
from app.models.transcript import LectureSession, Transcript, LectureSummary
from app.schemas.recording import RecordingResponse
from app.services.lecture_summary_service import LectureSummaryService
from app.services.whisper_service import WhisperSTTService
from app.services.ai_service import AIService
from app.services.session_store import session_store

logger = logging.getLogger(__name__)
router = APIRouter()

RECORDINGS_DIR = os.path.join(os.getcwd(), "uploads", "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)
DEBUG_AUDIO_DIR = os.path.join(os.getcwd(), "uploads", "debug_audio")
os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)


class LectureStartRequest(BaseModel):
    title: Optional[str] = "Live Classroom Session"
    course_id: Optional[str] = None
    room_id: Optional[str] = "default"


class LectureStopRequest(BaseModel):
    recording_id: Optional[str] = None
    duration: float = 0.0
    transcript: Optional[str] = None
    room_id: Optional[str] = "default"


class LectureSummarizeRequest(BaseModel):
    document_id: Optional[uuid.UUID] = None
    lecture_text: Optional[str] = None


# Helper function to execute lecture start logic
async def _execute_start_lecture(lecture_id: str, title: str, room_id: str, current_user: User, db: Optional[AsyncSession] = None) -> dict:
    sess_id = lecture_id if (lecture_id and lecture_id not in ("default", "start")) else f"sess_{uuid.uuid4().hex[:8]}"
    
    # Initialize session in SessionStore strictly for this session
    session_store.get_or_create(sess_id, title=title)
    logger.info(f"[SESSION] CREATED session_id={sess_id}")
    logger.info(f"[SESSION] ACTIVE session_id={sess_id}")
    logger.info(f"[SESSION] ACTIVE_SESSION_ID={sess_id}")

    teacher_name_str = getattr(current_user, "full_name", None) or (current_user.email.split("@")[0] if current_user and current_user.email else "Instructor")
    teacher_id_val = getattr(current_user, "id", None) if current_user else None

    # Persist or update LectureSession in PostgreSQL
    try:
        from app.database.database import SessionLocal
        async with SessionLocal() as async_db:
            now = datetime.now(timezone.utc)
            valid_tid = None
            if teacher_id_val:
                try:
                    u_chk = await async_db.execute(select(User.id).where(User.id == teacher_id_val))
                    if u_chk.scalar_one_or_none():
                        valid_tid = teacher_id_val
                except Exception:
                    valid_tid = None

            res = await async_db.execute(select(LectureSession).where(LectureSession.id == sess_id))
            db_sess = res.scalar_one_or_none()
            if not db_sess:
                db_sess = LectureSession(
                    id=sess_id,
                    title=title,
                    teacher_id=valid_tid,
                    teacher_name=teacher_name_str,
                    status="LIVE",
                    started_at=now,
                    created_at=now,
                    updated_at=now
                )
                async_db.add(db_sess)
            else:
                db_sess.status = "LIVE"
                db_sess.title = title
                if valid_tid:
                    db_sess.teacher_id = valid_tid
                db_sess.teacher_name = teacher_name_str
                db_sess.updated_at = now
            await async_db.commit()
    except Exception as db_err:
        logger.warning(f"[Lecture] LectureSession start DB persistence notice: {db_err}")

    logger.info(f"[Recording] Started: session_id='{sess_id}', title='{title}', user='{current_user.email}'")

    try:
        from app.api.routes.websocket import manager
        await manager.broadcast(room_id, {
            "type": "lecture_status",
            "status": True,
            "event": "lecture_started",
            "title": title,
            "classroom_session_id": sess_id,
            "session_id": sess_id,
            "started_by": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as ws_err:
        logger.warning(f"[WebSocket] Broadcast lecture_started notice: {ws_err}")

    return {
        "status": "success",
        "message": "Lecture started successfully",
        "lecture_id": sess_id,
        "classroom_session_id": sess_id,
        "session_id": sess_id,
        "title": title,
        "is_active": True,
        "started_by": current_user.email,
        "start_time": datetime.now(timezone.utc).isoformat()
    }


# Helper function to execute lecture stop logic
async def _execute_stop_lecture(
    lecture_id: str,
    payload: Optional[LectureStopRequest],
    db: AsyncSession,
    current_user: User
) -> dict:
    sess_id = lecture_id if (lecture_id and lecture_id not in ("default", "stop")) else (payload.room_id if payload and payload.room_id not in ("default", "stop") else "default")
    room_id = payload.room_id if payload and payload.room_id else lecture_id
    duration = payload.duration if payload else 0.0
    recording_id = payload.recording_id if payload and payload.recording_id else str(uuid.uuid4())

    logger.info(f"[RECORDING] STOPPED session_id='{sess_id}'")
    logger.info(f"[SESSION] ACTIVE_SESSION_ID={sess_id}")
    logger.info(f"[TRANSCRIPT] RECORDING_SESSION_ID={sess_id}")

    # 1. Retrieve session strictly for THIS session from store or database (no default fallback)
    stored_sess = await session_store.get_session_from_db_or_memory(sess_id) or await session_store.get_session_from_db_or_memory(lecture_id)

    # 2. Determine actual transcript for THIS session
    transcript_text = ""
    if payload and payload.transcript and payload.transcript.strip():
        transcript_text = payload.transcript.strip()
    elif stored_sess and stored_sess.transcript and stored_sess.transcript.strip():
        transcript_text = stored_sess.transcript.strip()

    # 3. Check if an audio recording file exists on disk strictly for this lecture and recording
    filename = f"rec_{lecture_id}_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    file_size_val = 0
    if os.path.exists(storage_path):
        try:
            file_size_val = os.path.getsize(storage_path)
        except Exception:
            file_size_val = 0

    # 4. If transcript is empty and audio file exists (>1KB), transcribe with Whisper
    if not transcript_text and os.path.exists(storage_path) and file_size_val > 1000:
        logger.info(f"[STT] Transcribing audio recording file on disk: '{storage_path}'")
        try:
            audio_transcript = WhisperSTTService.transcribe_audio_file(storage_path, session_id=sess_id)
            if audio_transcript:
                transcript_text = audio_transcript
                logger.info(f"[STT] File transcription complete: length={len(transcript_text)}")
        except Exception as stt_err:
            logger.warning(f"[STT] Audio file transcription notice: {stt_err}")

    # 5. Process AI Summary & NLP Insights
    ai_summary_text = ""
    ai_nlp_data: dict = {
        "sentiment": "Engaging & Academic",
        "topics": [],
        "definitions": [],
        "actionItems": []
    }

    if transcript_text:
        logger.info(f"[NLP] Processing transcript for session '{sess_id}'...")
        logger.info(f"[NLP] TRANSCRIPT_SESSION_ID={sess_id}")
        logger.info(f"[NLP] CURRENT_SESSION_ID={sess_id}")
        try:
            ai_nlp_data = await AIService.analyze_nlp(transcript_text)
        except Exception as nlp_err:
            logger.warning(f"[NLP] Analysis fallback: {nlp_err}")

        logger.info(f"[SUMMARY] SOURCE_SESSION_ID={sess_id}")
        try:
            ai_summary_text = await AIService.summarize(transcript=transcript_text, session_id=sess_id)
            logger.info(f"[SUMMARY] GENERATED session_id={sess_id}")
        except Exception as sum_err:
            logger.warning(f"[Summary] Generation fallback: {sum_err}")

    ai_summary_res = {
        "summary": ai_summary_text if ai_summary_text else "No summary available for this session yet.",
        "status": "completed" if ai_summary_text else "pending"
    }

    teacher_id_val = getattr(current_user, "id", None) if current_user else None
    user_email = getattr(current_user, "email", "teacher@nexora.school") if current_user else "teacher@nexora.school"
    teacher_name_val = getattr(current_user, "full_name", None) or user_email.split("@")[0]

    # 6. Persist to PostgreSQL (transcripts, lecture_sessions, lecture_summaries) & SessionStore strictly for sess_id
    await session_store.persist_finalized_session(
        session_id=sess_id,
        transcript=transcript_text,
        summary=ai_summary_res,
        nlp=ai_nlp_data,
        duration=duration,
        recording_id=recording_id,
        title=f"Finalized Lecture Session #{sess_id}",
        teacher_id=teacher_id_val,
        teacher_name=teacher_name_val
    )
    logger.info(f"[TRANSCRIPT] SAVED SESSION_ID={sess_id}")

    # 7. Persist Recording to PostgreSQL recordings table
    lecture_uuid = None
    try:
        lecture_uuid = uuid.UUID(lecture_id)
    except Exception:
        lecture_uuid = None

    rec_uuid = None
    try:
        rec_uuid = uuid.UUID(recording_id)
    except Exception:
        rec_uuid = uuid.uuid4()

    recording_data = {
        "id": str(rec_uuid),
        "filename": filename,
        "duration": duration,
        "file_size": file_size_val,
        "recording_status": "ready"
    }

    now = datetime.now(timezone.utc)

    try:
        recording_record = Recording(
            id=rec_uuid,
            lecture_id=lecture_uuid,
            teacher_id=teacher_id_val,
            filename=filename,
            duration=duration,
            start_time=now,
            end_time=now,
            storage_path=storage_path,
            summary=ai_summary_res,
            created_at=now,
            updated_at=now
        )
        db.add(recording_record)
        await db.commit()
        await db.refresh(recording_record)
        recording_data = {
            "id": str(recording_record.id),
            "filename": recording_record.filename,
            "duration": recording_record.duration,
            "file_size": file_size_val,
            "recording_status": "ready"
        }
    except Exception as db_err:
        logger.warning(f"[Session] Recording DB persistence fallback: {db_err}")
        try:
            await db.rollback()
        except Exception:
            pass

    attendance_summary = {
        "status": "finalized",
        "total_participants": 1,
        "finalized_at": datetime.now(timezone.utc).isoformat()
    }

    # 8. Broadcast stopped state to classroom WebSocket
    try:
        from app.api.routes.websocket import manager
        await manager.broadcast(room_id, {
            "type": "lecture_status",
            "status": False,
            "event": "lecture_ended",
            "summary": ai_summary_res,
            "nlp": ai_nlp_data,
            "transcript": transcript_text,
            "attendance": attendance_summary,
            "stopped_by": user_email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as ws_stop_err:
        logger.warning(f"[WebSocket] Broadcast lecture_ended notice: {ws_stop_err}")

    logger.info(f"[Session] Saving session complete: session_id='{sess_id}', transcript_len={len(transcript_text)}, summary_len={len(ai_summary_text)}")

    return {
        "status": "success",
        "message": "Lecture stopped and processed successfully",
        "session_id": sess_id,
        "lecture_id": sess_id,
        "recording": recording_data,
        "transcript": transcript_text,
        "ai_summary": ai_summary_res,
        "summary": ai_summary_text,
        "nlp": ai_nlp_data,
        "attendance": attendance_summary
    }



# ── Static routes declared BEFORE parameterized routes ────────────────────────

@router.post("/start", summary="Start default lecture session")
async def start_lecture(
    payload: Optional[LectureStartRequest] = None,
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Start default lecture session. Requires Teacher, Institute Admin, or Super Admin role."""
    title = payload.title if payload and payload.title else "Live Classroom Session"
    room_id = payload.room_id if payload and payload.room_id else "default"
    return await _execute_start_lecture("default", title, room_id, current_user)


@router.post("/stop", summary="Stop default lecture session")
async def stop_lecture(
    payload: Optional[LectureStopRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Stop default lecture session. Requires Teacher, Institute Admin, or Super Admin role."""
    return await _execute_stop_lecture("default", payload, db, current_user)


@router.post("/recording/start", summary="Start default recording session")
async def start_recording_default(
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Initialize a default lecture recording session file."""
    recording_id = uuid.uuid4()
    filename = f"rec_default_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    with open(storage_path, "wb") as f:
        pass

    return {
        "status": "success",
        "recording_id": str(recording_id),
        "filename": filename,
        "storage_path": storage_path,
        "start_time": datetime.now(timezone.utc).isoformat()
    }


@router.post("/recording/stop", response_model=RecordingResponse, summary="Stop default recording session")
async def stop_recording_default(
    recording_id: Optional[str] = Form(None),
    duration: Optional[float] = Form(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Finalize default recording session and save metadata in PostgreSQL."""
    rec_id = recording_id if recording_id else str(uuid.uuid4())
    filename = f"rec_default_{rec_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    rec_uuid = None
    try:
        rec_uuid = uuid.UUID(rec_id)
    except Exception:
        rec_uuid = uuid.uuid4()

    teacher_id_val = getattr(current_user, "id", None) if current_user else None
    
    file_size_val = 0
    if os.path.exists(storage_path):
        try:
            file_size_val = os.path.getsize(storage_path)
        except Exception:
            file_size_val = 0

    now = datetime.now(timezone.utc)
    recording_record = Recording(
        id=rec_uuid,
        lecture_id=None,
        teacher_id=teacher_id_val,
        filename=filename,
        duration=duration or 0.0,
        start_time=now,
        end_time=now,
        storage_path=storage_path,
        created_at=now,
        updated_at=now
    )

    try:
        db.add(recording_record)
        await db.commit()
        await db.refresh(recording_record)
        return recording_record
    except Exception as db_err:
        logger.warning(f"Database commit notice in stop_recording_default: {db_err}")
        await db.rollback()
        return recording_record


# ── Parameterized routes declared AFTER static routes ─────────────────────────

@router.post("/{lecture_id}/start", summary="Start a specific lecture session")
async def start_lecture_by_id(
    lecture_id: str,
    payload: Optional[LectureStartRequest] = None,
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Start specific lecture session by ID. Requires Teacher, Institute Admin, or Super Admin role."""
    title = payload.title if payload and payload.title else f"Lecture Session {lecture_id}"
    room_id = payload.room_id if payload and payload.room_id else lecture_id
    return await _execute_start_lecture(lecture_id, title, room_id, current_user)


@router.post("/{lecture_id}/stop", summary="Stop a specific lecture session")
async def stop_lecture_by_id(
    lecture_id: str,
    payload: Optional[LectureStopRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Stop specific lecture session by ID. Requires Teacher, Institute Admin, or Super Admin role."""
    return await _execute_stop_lecture(lecture_id, payload, db, current_user)


@router.post("/{lecture_id}/recording/start", summary="Start recording for specific lecture")
async def start_recording_by_id(
    lecture_id: str,
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Initialize a lecture recording session file by lecture ID."""
    recording_id = uuid.uuid4()
    filename = f"rec_{lecture_id}_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    with open(storage_path, "wb") as f:
        pass

    return {
        "status": "success",
        "recording_id": str(recording_id),
        "filename": filename,
        "storage_path": storage_path,
        "start_time": datetime.now(timezone.utc).isoformat()
    }


@router.post("/{lecture_id}/recording/chunk", summary="Upload a MediaRecorder chunk")
async def upload_recording_chunk(
    lecture_id: str = "default",
    recording_id: str = Form(...),
    chunk: UploadFile = File(...),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Append binary MediaRecorder chunks to the recording file on disk."""
    filename = f"rec_{lecture_id}_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    content = await chunk.read()
    with open(storage_path, "ab") as f:
        f.write(content)

    return {
        "status": "success",
        "chunk_bytes": len(content),
        "recording_id": recording_id
    }


@router.post("/{lecture_id}/recording/stop", response_model=RecordingResponse, summary="Stop recording for specific lecture")
async def stop_recording_by_id(
    lecture_id: str,
    recording_id: Optional[str] = Form(None),
    duration: Optional[float] = Form(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Finalize recording by lecture ID and save metadata in PostgreSQL."""
    rec_id = recording_id if recording_id else str(uuid.uuid4())
    filename = f"rec_{lecture_id}_{rec_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    lecture_uuid = None
    try:
        lecture_uuid = uuid.UUID(lecture_id)
    except Exception:
        lecture_uuid = None

    rec_uuid = None
    try:
        rec_uuid = uuid.UUID(rec_id)
    except Exception:
        rec_uuid = uuid.uuid4()

    teacher_id_val = getattr(current_user, "id", None) if current_user else None

    file_size_val = 0
    if os.path.exists(storage_path):
        try:
            file_size_val = os.path.getsize(storage_path)
        except Exception:
            file_size_val = 0

    now = datetime.now(timezone.utc)
    
    # Check if session exists or needs transcription from recording file
    stored_sess = session_store.get_session(lecture_id)
    transcript_text = stored_sess.transcript if stored_sess else ""
    if not transcript_text and os.path.exists(storage_path) and file_size_val > 1000:
        logger.info(f"[STT] Processing audio recording for stop_recording_by_id: '{storage_path}'")
        try:
            transcript_text = WhisperSTTService.transcribe_audio_file(storage_path, session_id=lecture_id) or ""
        except Exception as err:
            logger.warning(f"[STT] Transcription error: {err}")

    ai_summary_res = None
    ai_nlp_data = None
    if transcript_text:
        try:
            ai_nlp_data = await AIService.analyze_nlp(transcript_text)
            ai_sum_text = await AIService.summarize(transcript=transcript_text, session_id=lecture_id)
            ai_summary_res = {"summary": ai_sum_text, "status": "completed"}
        except Exception as e:
            logger.warning(f"AI processing notice in stop_recording_by_id: {e}")

    session_store.set_nlp_and_summary(
        session_id=lecture_id,
        transcript=transcript_text,
        summary=ai_summary_res or {"summary": "No summary available yet.", "status": "pending"},
        nlp=ai_nlp_data or {"sentiment": "Academic", "topics": [], "definitions": [], "actionItems": []},
        duration=duration or 0.0,
        recording_id=rec_id
    )

    recording_record = Recording(
        id=rec_uuid,
        lecture_id=lecture_uuid,
        teacher_id=teacher_id_val,
        filename=filename,
        duration=duration or 0.0,
        start_time=now,
        end_time=now,
        storage_path=storage_path,
        summary=ai_summary_res,
        created_at=now,
        updated_at=now
    )

    try:
        db.add(recording_record)
        await db.commit()
        await db.refresh(recording_record)
        return recording_record
    except Exception as db_err:
        logger.warning(f"Database commit notice in stop_recording_by_id: {db_err}")
        await db.rollback()
        return recording_record


# ── Session Query Endpoints for NLP & Summary Page ────────────────────────────

@router.get("/sessions/active", summary="List active and recent classroom sessions")
async def list_active_sessions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """Return all active and recently completed classroom sessions."""
    sessions = session_store.list_all_sessions()
    
    # Also fetch recent sessions from PostgreSQL
    try:
        res = await db.execute(select(LectureSession).order_by(LectureSession.created_at.desc()).limit(20))
        db_sessions = res.scalars().all()
        existing_ids = {s.get("session_id") for s in sessions}
        for dbs in db_sessions:
            if dbs.id not in existing_ids:
                sessions.append({
                    "session_id": dbs.id,
                    "title": dbs.title,
                    "status": dbs.status.lower(),
                    "duration": dbs.duration,
                    "created_at": dbs.created_at.isoformat() if dbs.created_at else None,
                    "updated_at": dbs.updated_at.isoformat() if dbs.updated_at else None
                })
    except Exception as e:
        logger.warning(f"[NLP API] DB sessions list notice: {e}")

    return {
        "status": "success",
        "data": sessions,
        "count": len(sessions)
    }


@router.get("/sessions/{session_id}", summary="Get all session data (transcript, summary, NLP)")
async def get_session_all_data(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve combined transcript, AI summary, and NLP insights for session_id."""
    sess_id_str = str(session_id)
    user_email = getattr(current_user, "email", "authenticated_user")
    logger.info(f"[NLP] FETCHING TRANSCRIPT session_id={sess_id_str}")
    logger.info(f"[TRANSCRIPT] FETCH_SESSION_ID={sess_id_str}")
    logger.info(f"[SUMMARY] SOURCE_SESSION_ID={sess_id_str}")
    logger.info(f"[NLP API] Request session_id={sess_id_str}")
    logger.info(f"[NLP API] Authenticated user={user_email}")
    logger.info(f"[NLP API] Querying transcript for session_id={sess_id_str}")

    try:
        # 1. Query PostgreSQL lecture_sessions strictly for this session_id
        res = await db.execute(select(LectureSession).where(LectureSession.id == sess_id_str))
        db_sess = res.scalar_one_or_none()

        # 2. Query PostgreSQL transcripts strictly for this session_id (chronological order)
        t_res = await db.execute(
            select(Transcript)
            .where(Transcript.lecture_session_id == sess_id_str)
            .order_by(Transcript.created_at.asc())
        )
        db_transcripts = t_res.scalars().all()
        transcript_count = len(db_transcripts)
        logger.info(f"[NLP API] Transcript records found={transcript_count}")

        # 3. Query PostgreSQL lecture_summaries strictly for this session_id
        s_res = await db.execute(select(LectureSummary).where(LectureSummary.lecture_session_id == sess_id_str))
        db_summary = s_res.scalar_one_or_none()

        # Format transcript strictly from records belonging to this session
        transcript_text = ""
        if db_transcripts:
            lines = [f"{t.speaker}: {t.transcript_text}" if not t.transcript_text.startswith(f"{t.speaker}:") else t.transcript_text for t in db_transcripts]
            transcript_text = "\n".join(lines)
            logger.info(f"[NLP API] Returning transcript for session {sess_id_str} ({len(lines)} lines)")
        else:
            # Check in-memory session_store strictly for this session_id
            mem_sess = session_store.get_session(sess_id_str)
            if mem_sess and mem_sess.transcript:
                transcript_text = mem_sess.transcript
                logger.info(f"[NLP API] Transcript recovered from in-memory session store: length={len(transcript_text)}")
            else:
                logger.info(f"[NLP API] No transcript found for session_id={sess_id_str}")

        summary_val = db_summary.summary_text if db_summary else None
        nlp_val = db_summary.nlp_insights if db_summary else None

        if not db_sess and not transcript_text and not db_summary:
            return {
                "session_id": sess_id_str,
                "title": f"Lecture Session #{sess_id_str}",
                "status": "not_found",
                "transcript": "",
                "summary": None,
                "nlp": None,
                "message": f"Lecture session #{sess_id_str} not found."
            }

        return {
            "status": "success",
            "session_id": sess_id_str,
            "title": db_sess.title if db_sess else f"Lecture Session #{sess_id_str}",
            "session_status": db_sess.status if db_sess else "FINALIZED",
            "transcript": transcript_text,
            "summary": summary_val,
            "nlp": nlp_val,
            "duration": db_sess.duration if db_sess else 0.0,
            "created_at": db_sess.created_at.isoformat() if (db_sess and db_sess.created_at) else datetime.now(timezone.utc).isoformat(),
            "updated_at": db_sess.updated_at.isoformat() if (db_sess and db_sess.updated_at) else datetime.now(timezone.utc).isoformat()
        }
    except Exception as err:
        logger.error(f"[NLP API] Transcript query failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed for session '{sess_id_str}': {str(err)}"
        )


@router.get("/sessions/{session_id}/transcript", summary="Get lecture transcript by session_id")
async def get_session_transcript(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve actual recognized transcript for session_id from PostgreSQL."""
    sess_id_str = str(session_id)
    user_email = getattr(current_user, "email", "authenticated_user")
    logger.info(f"[TRANSCRIPT] FETCH_SESSION_ID={sess_id_str}")
    logger.info(f"[NLP API] Request session_id={sess_id_str}")
    logger.info(f"[NLP API] Authenticated user={user_email}")
    logger.info(f"[NLP API] Querying transcript for session_id={sess_id_str}")

    try:
        t_res = await db.execute(
            select(Transcript)
            .where(Transcript.lecture_session_id == sess_id_str)
            .order_by(Transcript.created_at.asc())
        )
        db_transcripts = t_res.scalars().all()
        transcript_count = len(db_transcripts)
        logger.info(f"[NLP API] Transcript records found={transcript_count}")

        transcript_text = ""
        if db_transcripts:
            lines = [f"{t.speaker}: {t.transcript_text}" if not t.transcript_text.startswith(f"{t.speaker}:") else t.transcript_text for t in db_transcripts]
            transcript_text = "\n".join(lines)
            logger.info(f"[NLP API] Returning transcript")
        else:
            mem_sess = session_store.get_session(sess_id_str)
            if mem_sess and mem_sess.transcript:
                transcript_text = mem_sess.transcript
            else:
                logger.info(f"[NLP API] No transcript found for session_id={sess_id_str}")

        return {
            "session_id": sess_id_str,
            "transcript": transcript_text,
            "status": "completed" if transcript_text else "not_available"
        }
    except Exception as err:
        logger.error(f"[NLP API] Transcript query failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed for session '{sess_id_str}': {str(err)}"
        )


@router.get("/sessions/{session_id}/summary", summary="Get lecture summary by session_id")
async def get_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve AI-generated lecture summary for session_id from PostgreSQL."""
    sess_id_str = str(session_id)
    logger.info(f"[SUMMARY] SOURCE_SESSION_ID={sess_id_str}")
    try:
        s_res = await db.execute(select(LectureSummary).where(LectureSummary.lecture_session_id == sess_id_str))
        db_summary = s_res.scalar_one_or_none()
        summary_val = db_summary.summary_text if db_summary else None

        if not summary_val:
            mem_sess = session_store.get_session(sess_id_str)
            if mem_sess and mem_sess.summary:
                summary_val = mem_sess.summary.get("summary") if isinstance(mem_sess.summary, dict) else str(mem_sess.summary)

        return {
            "session_id": sess_id_str,
            "summary": summary_val,
            "status": "completed" if summary_val else "not_available"
        }
    except Exception as err:
        logger.error(f"[NLP API] Summary query failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed for session '{sess_id_str}': {str(err)}"
        )


@router.get("/sessions/{session_id}/nlp", summary="Get lecture NLP insights by session_id")
async def get_session_nlp(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve real-time NLP insights for session_id from PostgreSQL."""
    sess_id_str = str(session_id)
    try:
        s_res = await db.execute(select(LectureSummary).where(LectureSummary.lecture_session_id == sess_id_str))
        db_summary = s_res.scalar_one_or_none()
        nlp_data = db_summary.nlp_insights if (db_summary and db_summary.nlp_insights) else None

        if not nlp_data:
            mem_sess = session_store.get_session(sess_id_str)
            if mem_sess and mem_sess.nlp:
                nlp_data = mem_sess.nlp

        if not nlp_data:
            nlp_data = {
                "sentiment": "No transcript data available",
                "topics": [],
                "definitions": [],
                "actionItems": []
            }

        return {
            "session_id": sess_id_str,
            **nlp_data,
            "status": "completed" if (db_summary and db_summary.nlp_insights) else "not_available"
        }
    except Exception as err:
        logger.error(f"[NLP API] NLP query failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed for session '{sess_id_str}': {str(err)}"
        )


@router.get("/sessions/{session_id}/debug-audio", summary="Download/play raw microphone audio received for STT")
async def get_session_debug_audio(
    session_id: str,
    _: User = Depends(get_current_user),
) -> Any:
    """Returns the raw recorded audio received from the microphone before STT for verification."""
    sess_id_str = str(session_id)
    candidate_paths = [
        os.path.join(DEBUG_AUDIO_DIR, f"{sess_id_str}_microphone_audio.wav"),
        os.path.join(DEBUG_AUDIO_DIR, f"{sess_id_str}_microphone_audio.webm"),
    ]
    for p in candidate_paths:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            media_type = "audio/wav" if p.endswith(".wav") else "audio/webm"
            return FileResponse(
                path=p,
                filename=os.path.basename(p),
                media_type=media_type,
                headers={"Content-Disposition": f'inline; filename="{os.path.basename(p)}"'}
            )

    # Check if a recording file exists in RECORDINGS_DIR
    rec_matches = [f for f in os.listdir(RECORDINGS_DIR) if sess_id_str in f]
    if rec_matches:
        rec_path = os.path.join(RECORDINGS_DIR, rec_matches[0])
        return FileResponse(
            path=rec_path,
            filename=rec_matches[0],
            media_type="audio/webm",
            headers={"Content-Disposition": f'inline; filename="{rec_matches[0]}"'}
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No debug audio recording found for session '{sess_id_str}'."
    )


# ── Read-only / summary endpoints accessible to all authenticated users ────────

@router.post("/summarize", summary="Generate Lecture Summary using Gemini")
async def summarize_lecture(
    payload: LectureSummarizeRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """Generate structured lecture summary using Gemini."""
    result = await LectureSummaryService.summarize_lecture(
        db=db,
        document_id=payload.document_id,
        lecture_text=payload.lecture_text
    )
    return {
        "status": "success",
        "data": result
    }


@router.get("/summary/{summary_id}", summary="Get Lecture Summary by ID")
async def get_lecture_summary(
    summary_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """Get structured lecture summary by ID."""
    return {
        "status": "success",
        "summary_id": summary_id,
        "summary": "Lecture summary data"
    }


@router.get("/history", summary="Get Lecture History")
async def get_lecture_history(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """Get history of recorded lectures and active sessions."""
    return {
        "status": "success",
        "lectures": []
    }

