"""
app/services/session_store.py
──────────────────────────────
Central in-memory & persistent session repository for Live Classroom sessions.
Associates session_id with audio files, live transcripts, AI summaries, and NLP insights.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("app.services.session_store")


class SessionData:
    def __init__(self, session_id: str, title: str = "Live Classroom Session"):
        self.session_id: str = session_id
        self.title: str = title
        self.status: str = "active"  # "active" | "completed"
        self.transcript: str = ""
        self.raw_transcript: str = ""
        self.transcript_entries: List[Dict[str, Any]] = []
        self.raw_transcript_entries: List[Dict[str, Any]] = []
        self.summary: Optional[Dict[str, Any]] = None
        self.nlp: Optional[Dict[str, Any]] = None
        self.recording_id: Optional[str] = None
        self.recording_file: Optional[str] = None
        self.duration: float = 0.0
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "status": self.status,
            "transcript": self.transcript,
            "raw_transcript": self.raw_transcript,
            "transcript_entries": self.transcript_entries,
            "raw_transcript_entries": self.raw_transcript_entries,
            "summary": self.summary,
            "nlp": self.nlp,
            "recording_id": self.recording_id,
            "recording_file": self.recording_file,
            "duration": self.duration,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SessionStoreManager:
    """
    Singleton in-memory store for classroom sessions with helper methods
    for updating transcripts, AI summaries, and NLP insights.
    """
    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}

    def get_or_create(self, session_id: str, title: Optional[str] = None) -> SessionData:
        sess_id = str(session_id)
        if sess_id not in self._sessions:
            logger.info(f"[Session] Initializing session store for session_id='{sess_id}'")
            self._sessions[sess_id] = SessionData(session_id=sess_id, title=title or f"Lecture Session #{sess_id}")
        elif title and title != "Live Classroom Session":
            self._sessions[sess_id].title = title
        return self._sessions[sess_id]

    def reset_session(self, session_id: str, title: Optional[str] = None) -> SessionData:
        sess_id = str(session_id)
        sess = SessionData(session_id=sess_id, title=title or f"Lecture Session #{sess_id}")
        self._sessions[sess_id] = sess
        logger.info(f"[Session] Reset session store for session_id='{sess_id}'")
        return sess

    def get_session(self, session_id: str) -> Optional[SessionData]:
        sess_id = str(session_id)
        return self._sessions.get(sess_id)

    def append_transcript_entry(
        self,
        session_id: str,
        speaker: str,
        text: str,
        is_teacher: bool = True,
        timestamp: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> None:
        sess = self.get_or_create(session_id)
        now_ts = timestamp or datetime.now(timezone.utc).isoformat()
        entry = {
            "speaker": speaker,
            "text": text,
            "raw_text": raw_text or text,
            "is_teacher": is_teacher,
            "timestamp": now_ts
        }
        sess.transcript_entries.append(entry)
        if raw_text:
            sess.raw_transcript_entries.append({
                "speaker": speaker,
                "text": raw_text,
                "is_teacher": is_teacher,
                "timestamp": now_ts
            })
        
        # Build full text representations
        lines = [f"{e['speaker']}: {e['text']}" for e in sess.transcript_entries]
        sess.transcript = "\n".join(lines)
        if sess.raw_transcript_entries:
            raw_lines = [f"{e['speaker']}: {e['text']}" for e in sess.raw_transcript_entries]
            sess.raw_transcript = "\n".join(raw_lines)
        else:
            sess.raw_transcript = sess.transcript
            
        sess.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[Session] [{session_id}] Transcript updated ({len(sess.transcript_entries)} entries)")

    def set_transcript_text(self, session_id: str, transcript: str) -> None:
        sess = self.get_or_create(session_id)
        sess.transcript = transcript.strip()
        sess.updated_at = datetime.now(timezone.utc).isoformat()

    def set_nlp_and_summary(
        self,
        session_id: str,
        transcript: str,
        summary: Any,
        nlp: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        recording_id: Optional[str] = None
    ) -> SessionData:
        sess = self.get_or_create(session_id)
        if transcript:
            sess.transcript = transcript.strip()
        if summary:
            sess.summary = summary if isinstance(summary, dict) else {"summary": str(summary), "status": "completed"}
        if nlp:
            sess.nlp = nlp
        if duration > 0:
            sess.duration = duration
        if recording_id:
            sess.recording_id = recording_id
        sess.status = "completed"
        sess.updated_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[Session] Saving session: session_id='{session_id}', status='completed'")
        return sess

    async def persist_transcript_entry(
        self,
        session_id: str,
        speaker: str,
        text: str,
        is_teacher: bool = True,
        chunk_id: Optional[str] = None,
        sequence: int = 0,
        raw_text: Optional[str] = None
    ) -> None:
        """
        Appends transcript entry in memory AND persists immediately to PostgreSQL transcripts table.
        Saves both the assembled/cleaned text and the unaltered raw Whisper output (Requirement 9).
        """
        self.append_transcript_entry(session_id, speaker, text, is_teacher, raw_text=raw_text)
        
        logger.info(f"[Transcript] Persisting transcript")
        logger.info(f"[Transcript] Session ID: {session_id}")
        
        try:
            import uuid
            from app.database.database import SessionLocal
            from app.models.transcript import LectureSession, Transcript
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                # Ensure lecture_session exists
                res = await db.execute(select(LectureSession).where(LectureSession.id == str(session_id)))
                sess_record = res.scalar_one_or_none()
                now = datetime.now(timezone.utc)
                if not sess_record:
                    sess_record = LectureSession(
                        id=str(session_id),
                        title=f"Lecture Session #{session_id}",
                        status="LIVE",
                        started_at=now,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(sess_record)
                    await db.flush()
                
                t_record = Transcript(
                    id=uuid.uuid4(),
                    lecture_session_id=str(session_id),
                    speaker=speaker,
                    transcript_text=text,
                    raw_transcript_text=raw_text or text,
                    is_teacher=is_teacher,
                    sequence=sequence,
                    chunk_id=chunk_id,
                    status="finalized",
                    created_at=now,
                    updated_at=now
                )
                db.add(t_record)
                await db.commit()
                logger.info(f"[Transcript] Transcript persisted successfully (clean='{text}', raw='{raw_text or text}')")
                logger.info(f"[Transcript] Session ID: {session_id}")
        except Exception as err:
            logger.warning(f"[Transcript] DB persistence error for session '{session_id}': {err}")

    async def persist_finalized_session(
        self,
        session_id: str,
        transcript: str,
        summary: Any,
        nlp: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        recording_id: Optional[str] = None,
        title: Optional[str] = None,
        teacher_id: Optional[Any] = None,
        teacher_name: Optional[str] = None
    ) -> None:
        """
        Persists finalized session, transcript, and AI summary to PostgreSQL.
        """
        self.set_nlp_and_summary(session_id, transcript, summary, nlp, duration, recording_id)
        
        logger.info(f"[Transcript] Persisting finalized session")
        logger.info(f"[Transcript] Session ID: {session_id}")
        
        try:
            import uuid
            from app.database.database import SessionLocal
            from app.models.transcript import LectureSession, Transcript, LectureSummary
            from sqlalchemy import select, delete
            
            async with SessionLocal() as db:
                now = datetime.now(timezone.utc)
                sess_id_str = str(session_id)
                
                # Validate teacher_id FK against users table
                valid_teacher_id = None
                if teacher_id:
                    try:
                        from app.models.user import User
                        tid = teacher_id if isinstance(teacher_id, uuid.UUID) else uuid.UUID(str(teacher_id))
                        u_res = await db.execute(select(User.id).where(User.id == tid))
                        if u_res.scalar_one_or_none():
                            valid_teacher_id = tid
                    except Exception:
                        valid_teacher_id = None

                # 1. Upsert LectureSession
                res = await db.execute(select(LectureSession).where(LectureSession.id == sess_id_str))
                sess_record = res.scalar_one_or_none()
                if not sess_record:
                    sess_record = LectureSession(
                        id=sess_id_str,
                        title=title or f"Finalized Lecture Session #{sess_id_str}",
                        teacher_id=valid_teacher_id,
                        teacher_name=teacher_name or "Instructor",
                        status="FINALIZED",
                        started_at=now,
                        ended_at=now,
                        duration=duration,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(sess_record)
                else:
                    sess_record.status = "FINALIZED"
                    sess_record.ended_at = now
                    sess_record.duration = duration
                    if valid_teacher_id:
                        sess_record.teacher_id = valid_teacher_id
                    if title:
                        sess_record.title = title
                    if teacher_name:
                        sess_record.teacher_name = teacher_name
                    sess_record.updated_at = now
                
                await db.flush()

                # 2. If full transcript text provided and no transcripts in DB yet, add it
                if transcript and transcript.strip():
                    t_res = await db.execute(select(Transcript).where(Transcript.lecture_session_id == sess_id_str))
                    existing_t = t_res.scalars().all()
                    if not existing_t:
                        # Split by lines if speaker attributed or add full block
                        lines = [line.strip() for line in transcript.strip().split("\n") if line.strip()]
                        for seq, line in enumerate(lines, 1):
                            speaker = "Teacher"
                            line_text = line
                            if ": " in line:
                                parts = line.split(": ", 1)
                                speaker = parts[0].strip()
                                line_text = parts[1].strip()
                            db.add(Transcript(
                                id=uuid.uuid4(),
                                lecture_session_id=sess_id_str,
                                speaker=speaker,
                                transcript_text=line_text,
                                is_teacher=True,
                                sequence=seq,
                                status="finalized",
                                created_at=now,
                                updated_at=now
                            ))

                # 3. Upsert LectureSummary
                summary_text_val = ""
                if summary:
                    summary_text_val = summary.get("summary") if isinstance(summary, dict) else str(summary)
                
                if summary_text_val:
                    s_res = await db.execute(select(LectureSummary).where(LectureSummary.lecture_session_id == sess_id_str))
                    existing_s = s_res.scalar_one_or_none()
                    if not existing_s:
                        db.add(LectureSummary(
                            id=uuid.uuid4(),
                            lecture_session_id=sess_id_str,
                            summary_text=summary_text_val,
                            nlp_insights=nlp,
                            status="completed",
                            created_at=now,
                            updated_at=now
                        ))
                    else:
                        existing_s.summary_text = summary_text_val
                        existing_s.nlp_insights = nlp
                        existing_s.status = "completed"
                        existing_s.updated_at = now
                
                await db.commit()
                logger.info(f"[Transcript] Transcript and session persisted successfully for session {session_id}")
        except Exception as err:
            logger.warning(f"[Transcript] Finalized session DB persistence error: {err}")

    async def get_session_from_db_or_memory(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieves session data from PostgreSQL, falling back to in-memory store.
        """
        sess_id_str = str(session_id)
        
        # 1. Check in-memory store first
        mem_sess = self.get_session(sess_id_str)
        if mem_sess and mem_sess.transcript:
            return mem_sess

        # 2. Query PostgreSQL
        try:
            from app.database.database import SessionLocal
            from app.models.transcript import LectureSession, Transcript, LectureSummary
            from sqlalchemy import select
            
            async with SessionLocal() as db:
                sess_res = await db.execute(select(LectureSession).where(LectureSession.id == sess_id_str))
                db_sess = sess_res.scalar_one_or_none()
                
                t_res = await db.execute(
                    select(Transcript)
                    .where(Transcript.lecture_session_id == sess_id_str)
                    .order_by(Transcript.created_at.asc())
                )
                db_transcripts = t_res.scalars().all()
                
                s_res = await db.execute(select(LectureSummary).where(LectureSummary.lecture_session_id == sess_id_str))
                db_summary = s_res.scalar_one_or_none()
                
                if db_sess or db_transcripts:
                    sess_data = self.get_or_create(sess_id_str, title=db_sess.title if db_sess else f"Lecture Session #{sess_id_str}")
                    if db_sess:
                        sess_data.status = db_sess.status.lower()
                        sess_data.duration = db_sess.duration
                    
                    if db_transcripts:
                        sess_data.transcript_entries = [
                            {
                                "speaker": t.speaker,
                                "text": t.transcript_text,
                                "is_teacher": t.is_teacher,
                                "timestamp": t.created_at.isoformat() if t.created_at else None
                            }
                            for t in db_transcripts
                        ]
                        lines = [f"{t.speaker}: {t.transcript_text}" for t in db_transcripts]
                        sess_data.transcript = "\n".join(lines)
                    
                    if db_summary:
                        sess_data.summary = {"summary": db_summary.summary_text, "status": db_summary.status}
                        sess_data.nlp = db_summary.nlp_insights
                    
                    return sess_data
        except Exception as err:
            logger.warning(f"[SessionStore] Error querying PostgreSQL for session '{session_id}': {err}")

        return mem_sess


# Global singleton instance
session_store = SessionStoreManager()

