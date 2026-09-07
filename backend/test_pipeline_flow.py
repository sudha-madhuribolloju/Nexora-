"""
Test the Live Classroom -> Whisper -> Transcript -> NLP -> Summary pipeline.
"""
import asyncio
import os
import sys

# Add backend to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.session_store import session_store
from app.services.ai_service import AIService
from app.services.whisper_service import WhisperSTTService


async def test_pipeline():
    print("=== 1. Testing Session Store ===")
    sess_id = "test_session_101"
    session_store.get_or_create(sess_id, title="Quantum Computing Fundamentals")
    session_store.append_transcript_entry(
        session_id=sess_id,
        speaker="Dr. Sarah Jenkins",
        text="Today we are studying quantum physics and wave mechanics."
    )
    session_store.append_transcript_entry(
        session_id=sess_id,
        speaker="Dr. Sarah Jenkins",
        text="The wave function represents the state of a quantum system across Hilbert space."
    )

    sess = session_store.get_session(sess_id)
    assert sess is not None, "Session not found in store"
    assert "Today we are studying quantum physics" in sess.transcript
    assert len(sess.transcript_entries) == 2
    print("PASS: Session Store initialization and transcript accumulation")

    print("\n=== 2. Testing NLP Analysis ===")
    nlp_res = await AIService.analyze_nlp(sess.transcript)
    print("NLP Output:", nlp_res)
    assert "topics" in nlp_res, "NLP response missing topics"
    assert "definitions" in nlp_res, "NLP response missing definitions"
    assert "actionItems" in nlp_res, "NLP response missing actionItems"
    assert "sentiment" in nlp_res, "NLP response missing sentiment"
    print("PASS: NLP analysis extraction")

    print("\n=== 3. Testing AI Summarization ===")
    summary_res = await AIService.summarize(sess.transcript)
    ascii_preview = summary_res[:150].encode('ascii', 'replace').decode('ascii')
    print("Summary Output Preview:", ascii_preview, "...")
    assert len(summary_res) > 20, "Summary output is empty"
    print("PASS: Summary generation")


    print("\n=== 4. Testing Session Finalization in Store ===")
    session_store.set_nlp_and_summary(
        session_id=sess_id,
        transcript=sess.transcript,
        summary={"summary": summary_res, "status": "completed"},
        nlp=nlp_res,
        duration=45.0
    )
    final_sess = session_store.get_session(sess_id)
    assert final_sess.status == "completed"
    assert final_sess.summary is not None
    assert final_sess.nlp is not None
    print("PASS: Session finalization and persistence")

    print("\n=== 5. Testing Whisper Service Availability ===")
    model = WhisperSTTService.transcribe_audio_file("non_existent_file.webm")
    assert model is None, "Should handle missing file gracefully"
    print("PASS: WhisperSTTService error handling")

    print("\nALL PIPELINE TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
