import logging
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token
from app.core.rbac import verify_lecture_control_role_string
from app.database.database import SessionLocal
from app.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

CONTROL_EVENT_TYPES = {
    "lecture_status",
    "recording_status",
    "start_lecture",
    "stop_lecture",
    "start_recording",
    "stop_recording",
}


class ConnectionManager:
    """
    Manages active WebSocket connections for live classrooms with room-level broadcasting.
    """
    def __init__(self):
        # Maps room_id -> list of WebSockets
        self.active_rooms: Dict[str, List[WebSocket]] = {}
        # Maps room_id -> list of participant info dicts
        self.room_participants: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_info: Optional[dict] = None):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
            self.room_participants[room_id] = []
        self.active_rooms[room_id].append(websocket)
        
        if user_info:
            # Avoid duplicate user entry
            self.room_participants[room_id] = [p for p in self.room_participants[room_id] if p.get("id") != user_info.get("id")]
            self.room_participants[room_id].append(user_info)

        logger.info(f"WebSocket client connected to room '{room_id}'. Total in room: {len(self.active_rooms[room_id])}")
        
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
                del self.active_rooms[room_id]
                
        if room_id in self.room_participants and user_id:
            self.room_participants[room_id] = [p for p in self.room_participants[room_id] if p.get("id") != user_id]
            if not self.room_participants[room_id]:
                del self.room_participants[room_id]

        logger.info(f"WebSocket client disconnected from room '{room_id}'.")

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            disconnected_sockets = []
            for connection in self.active_rooms[room_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending message on socket: {e}")
                    disconnected_sockets.append(connection)
            for ws in disconnected_sockets:
                self.disconnect(ws, room_id)


manager = ConnectionManager()


@router.websocket("/classroom/{room_id}")
async def websocket_classroom_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time classroom updates, chat, hand-raising, and recording status.
    Enforces RBAC permissions for lecture control events.
    """
    user_info = None
    user_role = "Student"

    if token:
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            user_id_str = payload.get("sub")
            user_role = payload.get("role", "Student")
            
            # Retrieve updated user role directly from PostgreSQL database if available
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
                logger.warning(f"Failed to lookup DB user for WS token: {e}")

            if not user_info:
                user_info = {
                    "id": user_id_str,
                    "email": payload.get("email", "User"),
                    "role": user_role
                }

    await manager.connect(websocket, room_id, user_info)
    user_id = user_info.get("id") if user_info else None

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            # Validate lecture control authorization for restricted events
            if event_type in CONTROL_EVENT_TYPES:
                if not verify_lecture_control_role_string(user_role):
                    logger.warning(f"Unauthorized WS control event '{event_type}' attempted by user role '{user_role}'.")
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
                await manager.broadcast(room_id, {
                    "type": "lecture_status",
                    "status": data.get("status", True if event_type == "start_lecture" else False),
                    "event": data.get("event", event_type),
                    "title": data.get("title"),
                    "slide": data.get("slide")
                })
            elif event_type in ("recording_status", "start_recording", "stop_recording"):
                await manager.broadcast(room_id, {
                    "type": "recording_status",
                    "isRecording": data.get("isRecording", True if event_type == "start_recording" else False),
                    "recordingId": data.get("recordingId")
                })
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
    except Exception as exc:
        logger.error(f"WebSocket error in room {room_id}: {exc}")
        manager.disconnect(websocket, room_id, user_id)
