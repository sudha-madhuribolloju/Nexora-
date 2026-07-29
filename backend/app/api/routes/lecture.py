import os
import uuid
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
from app.schemas.recording import RecordingResponse
from app.services.lecture_summary_service import LectureSummaryService

router = APIRouter()

RECORDINGS_DIR = os.path.join(os.getcwd(), "uploads", "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)


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
async def _execute_start_lecture(lecture_id: str, title: str, room_id: str, current_user: User) -> dict:
    try:
        from app.api.routes.websocket import manager
        await manager.broadcast(room_id, {
            "type": "lecture_status",
            "status": True,
            "event": "lecture_started",
            "title": title,
            "started_by": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Lecture started successfully",
        "lecture_id": lecture_id,
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
    room_id = payload.room_id if payload and payload.room_id else lecture_id
    duration = payload.duration if payload else 0.0
    recording_id = payload.recording_id if payload and payload.recording_id else str(uuid.uuid4())
    transcript_text = payload.transcript if payload and payload.transcript else "Standard lecture transcript text."

    filename = f"rec_{lecture_id}_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

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

    recording_record = Recording(
        id=rec_uuid,
        lecture_id=lecture_uuid,
        teacher_id=current_user.id,
        filename=filename,
        duration=duration,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        storage_path=storage_path
    )
    db.add(recording_record)
    await db.commit()
    await db.refresh(recording_record)

    ai_summary_res = await LectureSummaryService.summarize_lecture(
        db=db,
        lecture_text=f"Lecture ID: {lecture_id}. Transcript: {transcript_text}"
    )

    attendance_summary = {
        "status": "finalized",
        "total_participants": 1,
        "finalized_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        from app.api.routes.websocket import manager
        await manager.broadcast(room_id, {
            "type": "lecture_status",
            "status": False,
            "event": "lecture_ended",
            "summary": ai_summary_res,
            "attendance": attendance_summary,
            "stopped_by": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Lecture stopped and processed successfully",
        "lecture_id": lecture_id,
        "recording": {
            "id": str(recording_record.id),
            "filename": recording_record.filename,
            "duration": recording_record.duration
        },
        "transcript": transcript_text,
        "ai_summary": ai_summary_res,
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
    recording_id: str = Form(...),
    duration: float = Form(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Finalize default recording session and save metadata in PostgreSQL."""
    filename = f"rec_default_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

    rec_uuid = None
    try:
        rec_uuid = uuid.UUID(recording_id)
    except Exception:
        rec_uuid = uuid.uuid4()

    recording_record = Recording(
        id=rec_uuid,
        lecture_id=None,
        teacher_id=current_user.id,
        filename=filename,
        duration=duration,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        storage_path=storage_path
    )

    db.add(recording_record)
    await db.commit()
    await db.refresh(recording_record)
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
    recording_id: str = Form(...),
    duration: float = Form(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_lecture_control_permission),
) -> Any:
    """Finalize recording by lecture ID and save metadata in PostgreSQL."""
    filename = f"rec_{lecture_id}_{recording_id}.webm"
    storage_path = os.path.join(RECORDINGS_DIR, filename)

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

    recording_record = Recording(
        id=rec_uuid,
        lecture_id=lecture_uuid,
        teacher_id=current_user.id,
        filename=filename,
        duration=duration,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        storage_path=storage_path
    )

    db.add(recording_record)
    await db.commit()
    await db.refresh(recording_record)
    return recording_record


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


@router.get("/recordings", response_model=List[RecordingResponse], summary="List all lecture recordings")
async def list_recordings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """Retrieve all recordings stored in PostgreSQL."""
    stmt = select(Recording).order_by(Recording.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/recordings/{recording_id}/stream", summary="Stream a lecture recording video file")
async def stream_recording(
    recording_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Stream a stored recording file."""
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()

    if not rec or not os.path.exists(rec.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording file not found"
        )

    return FileResponse(rec.storage_path, media_type="video/webm", filename=rec.filename)
