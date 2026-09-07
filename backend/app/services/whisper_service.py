"""
app/services/whisper_service.py
────────────────────────────────
Real-time Speech-to-Text using faster-whisper.
Configured for accurate, hallucination-resistant streaming transcription.

Key anti-hallucination parameters:
  - beam_size=1          : Greedy decoding — faster, fewer hallucinations on short chunks
  - temperature=0        : Deterministic, no stochastic sampling
  - condition_on_previous_text=False : Prevents hallucinating continuations of previous audio
  - no_speech_prob > 0.6 : Discard silence / non-speech segments
  - compression_ratio_threshold=2.0  : Discard repeated/hallucinated text
  - log_prob_threshold=-1.0          : Discard very low-confidence segments
  - vad_filter=True                  : Voice activity detection removes silence pre-pass
"""
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_whisper_model = None


def get_whisper_model():
    """
    Lazily initialize and return the faster-whisper model instance.
    Uses 'base.en' (English-specialized, 74M params) for high accuracy on technical terms
    like Terraform, NEXORA, while remaining fast on CPU with int8 quantization.
    Falls back gracefully to 'tiny.en' or 'tiny' if needed.
    """
    global _whisper_model
    if _whisper_model is None:
        model_candidates = ["small.en", "base.en", "tiny.en", "base", "tiny"]
        for candidate in model_candidates:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"[Whisper] Initializing faster-whisper model '{candidate}' on CPU (int8)...")
                try:
                    _whisper_model = WhisperModel(candidate, device="cpu", compute_type="int8")
                except Exception as e_int8:
                    logger.warning(f"[Whisper] int8 failed for {candidate}, trying float32: {e_int8}")
                    _whisper_model = WhisperModel(candidate, device="cpu", compute_type="float32")
                logger.info(f"[Whisper] Model '{candidate}' loaded successfully.")
                break
            except Exception as err:
                logger.warning(f"[Whisper] Failed loading '{candidate}': {err}")
                continue
        if _whisper_model is None:
            logger.error("[Whisper] All faster-whisper model candidates failed to load.")
            _whisper_model = False
    return _whisper_model if _whisper_model is not False else None


# Minimum audio bytes to attempt transcription (valid WebM container is ~500 bytes)
_MIN_AUDIO_BYTES = 500

# Clean academic prompt without domain-forcing bias (strictly avoids hallucinating MCP, DevOps, etc.)
_CLASSROOM_INITIAL_PROMPT = (
    "Classroom educational lecture. Clear technical, mathematical, and academic speech."
)


class WhisperSTTService:
    """
    Real-time Speech-to-Text service using faster-whisper.
    Converts audio chunks into clean transcribed speech text.
    NO mock or simulated fallback text.
    """

    @staticmethod
    def transcribe_audio_chunk(
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        chunk_id: Optional[str] = None,
        session_id: Optional[str] = None,
        sequence_number: Optional[int] = None,
        overlap_prefix_pcm: Optional[bytes] = None,
    ) -> Tuple[Optional[str], Optional[bytes]]:
        request_id = chunk_id or str(uuid.uuid4())[:8]
        sess_label = session_id or "default"
        seq_label = sequence_number if sequence_number is not None else 0
        now_iso = datetime.now(timezone.utc).isoformat()

        if not audio_bytes or len(audio_bytes) == 0:
            logger.warning(f"[Whisper] [session={sess_label}] [{request_id}] Empty audio bytes received — skipping.")
            return None, None

        byte_count = len(audio_bytes)
        if byte_count < _MIN_AUDIO_BYTES:
            logger.info(
                f"[Whisper] [session={sess_label}] [{request_id}] Audio chunk too small "
                f"({byte_count} bytes < {_MIN_AUDIO_BYTES} minimum) — skipping."
            )
            return None, None

        # Map MIME type to file extension
        ext = ".webm"
        if "wav" in mime_type:
            ext = ".wav"
        elif "mp3" in mime_type:
            ext = ".mp3"
        elif "ogg" in mime_type:
            ext = ".ogg"

        temp_path = None
        converted_wav_path = None
        final_wav_path = None
        start_ts = time.monotonic()
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            # Convert input container to 16kHz mono PCM WAV via FFmpeg
            import subprocess
            converted_fd, converted_wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(converted_fd)
            cmd = [
                "ffmpeg", "-y", "-i", temp_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                converted_wav_path
            ]
            conv_res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)

            target_audio_path = converted_wav_path if (conv_res.returncode == 0 and os.path.exists(converted_wav_path) and os.path.getsize(converted_wav_path) > 100) else temp_path

            # Read converted 16kHz mono PCM frames
            pcm_frames = b""
            duration_sec = 0.0
            rate_val = 16000
            channels_cnt = 1
            try:
                import wave
                with wave.open(target_audio_path, "rb") as wf_in:
                    frames_cnt = wf_in.getnframes()
                    rate_val = wf_in.getframerate()
                    channels_cnt = wf_in.getnchannels()
                    duration_sec = round(frames_cnt / float(rate_val), 2)
                    pcm_frames = wf_in.readframes(frames_cnt)
            except Exception as read_err:
                logger.debug(f"[Whisper] Notice reading PCM frames: {read_err}")

            # Keep last 1.0s of PCM frames (16000 * 2 bytes = 32000 bytes) for next chunk's overlap
            tail_bytes_count = int(1.0 * rate_val * 2)
            chunk_tail_pcm = pcm_frames[-tail_bytes_count:] if len(pcm_frames) >= tail_bytes_count else pcm_frames

            # If overlap_prefix_pcm is provided, stitch it before current frames to preserve boundary phonemes
            if overlap_prefix_pcm and len(overlap_prefix_pcm) > 0 and len(pcm_frames) > 0:
                final_fd, final_wav_path = tempfile.mkstemp(suffix=".wav")
                os.close(final_fd)
                combined_frames = overlap_prefix_pcm + pcm_frames
                import wave
                with wave.open(final_wav_path, "wb") as wf_out:
                    wf_out.setnchannels(1)
                    wf_out.setsampwidth(2)
                    wf_out.setframerate(rate_val)
                    wf_out.writeframes(combined_frames)
                target_audio_path = final_wav_path
                duration_sec = round(len(combined_frames) / (rate_val * 2.0), 2)
                logger.info(
                    f"[Whisper Overlap] Prepended {len(overlap_prefix_pcm)} bytes ({round(len(overlap_prefix_pcm)/(rate_val*2.0), 2)}s) "
                    f"to chunk {request_id} -> total duration {duration_sec}s"
                )

            # VAD & Audio Silence Check via RMS energy
            rms = 0.05  # default active
            is_silence = False
            if pcm_frames:
                try:
                    import numpy as np
                    samples = np.frombuffer(pcm_frames, dtype=np.int16)
                    if len(samples) > 0:
                        rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)) / 32768.0)
                        if rms < 0.006:
                            is_silence = True
                except Exception as e_rms:
                    logger.debug(f"RMS calculation error: {e_rms}")

            vad_label = "SILENCE" if is_silence else "SPEECH"

            # Comprehensive Phase 3 Diagnostic Log
            logger.info(
                f"[STT_DIAGNOSTIC] session_id={sess_label} chunk_id={request_id} sequence_number={seq_label} "
                f"timestamp={now_iso} duration={duration_sec}s sample_rate={rate_val} channels={channels_cnt} "
                f"audio_format=pcm_s16le byte_size={byte_count} VAD detected={vad_label} "
                f"STT request sent={'NO' if is_silence else 'YES'}"
            )

            if is_silence:
                logger.info(
                    f"[Whisper] [session={sess_label}] [{request_id}] Audio chunk is silence "
                    f"(RMS={rms:.5f} < 0.006) — skipping Whisper inference."
                )
                return "", chunk_tail_pcm

            model = get_whisper_model()
            if model is None:
                logger.error(f"[Whisper] [session={sess_label}] [{request_id}] Whisper model unavailable.")
                raise RuntimeError("Whisper speech-to-text model unavailable or failed to load")

            # Save exact audio sent to Whisper for developer inspection (Phase 3 requirement)
            try:
                debug_dir = os.path.join(os.getcwd(), "uploads", "debug_audio", sess_label)
                os.makedirs(debug_dir, exist_ok=True)
                whisper_debug_file = os.path.join(debug_dir, f"whisper_chunk_{seq_label}_{request_id}.wav")
                import shutil
                shutil.copyfile(target_audio_path, whisper_debug_file)
            except Exception as deb_err:
                logger.debug(f"Debug audio copy notice: {deb_err}")

            # Transcribe with beam_size=3, explicit language='en', and domain prompt
            segments, info = model.transcribe(
                target_audio_path,
                language="en",
                beam_size=3,
                temperature=0,
                condition_on_previous_text=False,
                initial_prompt=_CLASSROOM_INITIAL_PROMPT,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=250,
                    speech_pad_ms=250,
                ),
                compression_ratio_threshold=2.2,
                log_prob_threshold=-1.0,
            )

            accepted_parts = []
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue

                # Discard segments where Whisper indicates no-speech with moderate probability
                if segment.no_speech_prob > 0.60:
                    logger.info(
                        f"[Whisper] [session={sess_label}] [{request_id}] Segment discarded "
                        f"(no_speech_prob={segment.no_speech_prob:.2f}): '{text}'"
                    )
                    continue

                # Discard segments with high compression ratio (repetition hallucination)
                if segment.compression_ratio > 2.2:
                    logger.info(
                        f"[Whisper] [session={sess_label}] [{request_id}] Segment discarded "
                        f"(compression_ratio={segment.compression_ratio:.2f}): '{text}'"
                    )
                    continue

                # Reject repetitive token loops (e.g. "Okay. Okay. Okay." or "work, so we have to...")
                words = text.lower().split()
                if len(words) >= 4:
                    word_counts = {}
                    for w in words:
                        w_clean = w.strip(".,!?;:")
                        word_counts[w_clean] = word_counts.get(w_clean, 0) + 1
                    max_freq = max(word_counts.values()) if word_counts else 0
                    if max_freq / len(words) > 0.5 and max_freq >= 4:
                        logger.info(
                            f"[Whisper] [session={sess_label}] [{request_id}] Segment discarded "
                            f"(repetitive loop detected: max_freq={max_freq}/{len(words)}): '{text}'"
                        )
                        continue

                accepted_parts.append(text)

            transcribed_text = " ".join(accepted_parts).strip()
            elapsed = round(time.monotonic() - start_ts, 3)

            # Filter known Whisper silence hallucination artifacts
            if transcribed_text:
                lower_text = transcribed_text.lower().strip()
                known_hallucinations = [
                    "give a special thank you",
                    "you have your...",
                    "subtitles by",
                    "watching",
                    "please subscribe",
                    "thank you for watching",
                    "see you next time",
                    "so we have to do a little bit of work"
                ]
                if any(h in lower_text for h in known_hallucinations):
                    logger.info(f"[Whisper] [session={sess_label}] Filtered out hallucination artifact: '{transcribed_text}'")
                    transcribed_text = ""

            # Phase 3 Log: STT response received & transcript text
            logger.info(
                f"[STT_DIAGNOSTIC] session_id={sess_label} chunk_id={request_id} sequence_number={seq_label} "
                f"STT response received=YES transcript text=\"{transcribed_text}\" (elapsed={elapsed}s)"
            )
            logger.info(f"[LiveAudio] STT result received: \"{transcribed_text}\" (chunk_id={request_id})")

            return transcribed_text, chunk_tail_pcm

        except Exception as whisper_err:
            logger.error(f"[Whisper] [{request_id}] Transcription error: {whisper_err}", exc_info=True)
            raise whisper_err
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            if converted_wav_path and os.path.exists(converted_wav_path):
                try:
                    os.remove(converted_wav_path)
                except Exception:
                    pass

    @staticmethod
    def transcribe_audio_file(
        file_path: str,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe an entire audio recording file from disk using faster-whisper.
        """
        sess_label = session_id or "default"
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"[Whisper] Audio file not found: {file_path}")
            return None

        converted_wav = None
        target_path = file_path
        try:
            file_size = os.path.getsize(file_path)
            if file_size < _MIN_AUDIO_BYTES:
                logger.info(f"[Whisper] File {file_path} too small ({file_size} bytes) — skipping.")
                return None

            # Convert non-WAV formats (like multi-header WebM) to clean 16kHz PCM WAV via FFmpeg
            if not file_path.lower().endswith(".wav"):
                try:
                    import subprocess
                    fd, converted_wav = tempfile.mkstemp(suffix=".wav")
                    os.close(fd)
                    res = subprocess.run(
                        ["ffmpeg", "-y", "-i", file_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", converted_wav],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30
                    )
                    if res.returncode == 0 and os.path.exists(converted_wav) and os.path.getsize(converted_wav) > 100:
                        target_path = converted_wav
                except Exception as ff_err:
                    logger.warning(f"[Whisper] FFmpeg pre-conversion notice for {file_path}: {ff_err}")

            logger.info(f"[STT] Processing audio file '{target_path}' ({file_size} bytes) for session_id='{sess_label}'")
            model = get_whisper_model()
            if model is None:
                raise RuntimeError("Whisper model unavailable")

            segments, info = model.transcribe(
                target_path,
                language="en",
                beam_size=1,
                temperature=0,
                condition_on_previous_text=False,
                initial_prompt=_CLASSROOM_INITIAL_PROMPT,
                vad_filter=True,
                compression_ratio_threshold=2.0,
                log_prob_threshold=-1.0,
            )

            parts = []
            for seg in segments:
                t = seg.text.strip()
                if t and seg.no_speech_prob <= 0.60 and seg.compression_ratio <= 2.0:
                    # Filter out repetition loop hallucinations
                    words = t.lower().split()
                    if len(words) >= 4:
                        word_counts = {}
                        for w in words:
                            w_clean = w.strip(".,!?;:")
                            word_counts[w_clean] = word_counts.get(w_clean, 0) + 1
                        max_freq = max(word_counts.values()) if word_counts else 0
                        if max_freq / len(words) > 0.5 and max_freq >= 4:
                            continue
                    parts.append(t)

            final_text = " ".join(parts).strip()
            if final_text:
                logger.info(f"[STT] Transcript generated from file: \"{final_text[:100]}...\" (total length={len(final_text)})")
                return final_text
            return None
        except Exception as err:
            logger.error(f"[Whisper] Failed to transcribe audio file {file_path}: {err}", exc_info=True)
            return None
        finally:
            if converted_wav and os.path.exists(converted_wav):
                try:
                    os.remove(converted_wav)
                except Exception:
                    pass

