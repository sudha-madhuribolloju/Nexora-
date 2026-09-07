"""
app/services/transcript_assembler.py
────────────────────────────────────
Intelligent transcript assembly engine for Live Classroom speech-to-text.

Key capabilities:
1. Overlap Deduplication:
   Detects suffix-to-prefix word overlap between consecutive Whisper chunk transcripts
   (arising from 0.5-1.0s audio overlap) and eliminates duplicate tokens.
2. Cut-Word Reconciliation:
   If a word was cut off at the chunk boundary in chunk N, but resolved cleanly in chunk N+1,
   replaces the cut fragment with the complete word.
3. Raw vs Cleaned Transcript Preservation:
   Always preserves the original raw Whisper output while building the cohesive cleaned transcript.
4. Session Isolation:
   Maintains separate assembly state keyed strictly by session_id.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("app.services.transcript_assembler")


def _normalize_token(token: str) -> str:
    """Strip punctuation and lowercase for comparison."""
    return re.sub(r"[^\w\s]", "", token).lower().strip()


class SessionAssemblyState:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.accumulated_text: str = ""
        self.last_chunk_tokens: List[str] = []
        self.last_raw_chunk: str = ""
        self.chunks_assembled: int = 0

    def reset(self):
        self.accumulated_text = ""
        self.last_chunk_tokens = []
        self.last_raw_chunk = ""
        self.chunks_assembled = 0


class TranscriptAssembler:
    """
    Singleton assembler that reconciles overlapping Whisper chunk transcripts per session.
    """
    def __init__(self):
        self._sessions: Dict[str, SessionAssemblyState] = {}

    def get_or_create_session(self, session_id: str) -> SessionAssemblyState:
        sess_id = str(session_id)
        if sess_id not in self._sessions:
            self._sessions[sess_id] = SessionAssemblyState(sess_id)
        return self._sessions[sess_id]

    def reset_session(self, session_id: str):
        sess_id = str(session_id)
        if sess_id in self._sessions:
            self._sessions[sess_id].reset()
            logger.info(f"[Assembler] Reset assembly state for session '{sess_id}'")

    def assemble_chunk(
        self,
        session_id: str,
        raw_chunk_text: str,
        max_overlap_words: int = 8
    ) -> Tuple[str, str]:
        """
        Assembles an incoming raw Whisper transcript chunk into the running session transcript.

        Args:
            session_id: Active session identifier.
            raw_chunk_text: Unprocessed output string from Whisper.
            max_overlap_words: Maximum trailing words from previous chunk to check for overlap.

        Returns:
            Tuple of:
              - cleaned_incremental_text: Cleaned text contributed by THIS chunk (overlap stripped, cut words fixed).
              - full_assembled_text: Complete accumulated transcript for the session so far.
        """
        clean_new = raw_chunk_text.strip()
        if not clean_new:
            state = self.get_or_create_session(session_id)
            return "", state.accumulated_text

        state = self.get_or_create_session(session_id)

        # First chunk in session — nothing to reconcile
        if not state.accumulated_text or not state.last_chunk_tokens:
            state.accumulated_text = clean_new
            state.last_chunk_tokens = clean_new.split()
            state.last_raw_chunk = clean_new
            state.chunks_assembled += 1
            return clean_new, clean_new

        prev_words = state.last_chunk_tokens
        new_words = clean_new.split()

        # Window of trailing words from previous chunk to check
        window_size = min(len(prev_words), max_overlap_words)
        prev_window = prev_words[-window_size:]
        prev_norm = [_normalize_token(w) for w in prev_window]
        new_norm = [_normalize_token(w) for w in new_words]

        best_overlap_len = 0
        cut_word_repaired = False

        # Search for exact or fuzzy suffix-to-prefix overlap
        # Check from longest possible overlap down to 1 word
        max_check = min(len(prev_norm), len(new_norm))
        for overlap_len in range(max_check, 0, -1):
            prev_slice = prev_norm[-overlap_len:]
            new_slice = new_norm[:overlap_len]
            if prev_slice == new_slice:
                best_overlap_len = overlap_len
                break

        # Check for cut word at boundary (e.g. prev ended with "import" and new starts with "important")
        if best_overlap_len == 0 and prev_norm and new_norm:
            last_prev = prev_norm[-1]
            first_new = new_norm[0]
            if len(last_prev) >= 3 and first_new.startswith(last_prev):
                cut_word_repaired = True
                best_overlap_len = 1
                logger.info(f"[Assembler] Repaired cut word: '{prev_words[-1]}' -> '{new_words[0]}'")
            elif len(first_new) >= 3 and last_prev.startswith(first_new):
                cut_word_repaired = True
                best_overlap_len = 1
                logger.info(f"[Assembler] Repaired cut word: '{prev_words[-1]}' -> '{new_words[0]}'")

        if best_overlap_len > 0:
            logger.info(
                f"[Assembler] [session={session_id}] Detected {best_overlap_len}-word overlap "
                f"between chunks: '{' '.join(new_words[:best_overlap_len])}'"
            )
            # Incremental words are the words in new_words beyond the overlap
            incremental_words = new_words[best_overlap_len:]

            if cut_word_repaired:
                # Replace the incomplete trailing word in accumulated_text with the complete word
                accum_words = state.accumulated_text.split()
                if accum_words:
                    accum_words[-1] = new_words[0]  # Use complete word
                    state.accumulated_text = " ".join(accum_words)

            if incremental_words:
                incremental_text = " ".join(incremental_words)
                state.accumulated_text = f"{state.accumulated_text} {incremental_text}".strip()
            else:
                incremental_text = ""
        else:
            # No overlap detected: append directly
            incremental_text = clean_new
            state.accumulated_text = f"{state.accumulated_text} {clean_new}".strip()

        # Update state for next chunk
        state.last_chunk_tokens = new_words
        state.last_raw_chunk = clean_new
        state.chunks_assembled += 1

        return incremental_text, state.accumulated_text


# Global singleton instance
transcript_assembler = TranscriptAssembler()
