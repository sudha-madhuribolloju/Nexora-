import io
import logging
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger("app.services.pdf_service")


class PDFService:
    """
    Service responsible for extracting text and page numbers from PDF files and chunking content.
    """

    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text page by page from raw PDF bytes.
        Returns a list of dicts with 'page_number' (1-indexed) and 'text'.
        """
        pages_content = []
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                cleaned = extracted.strip()
                if cleaned:
                    pages_content.append({
                        "page_number": idx + 1,
                        "text": cleaned
                    })
        except Exception as e:
            logger.warning(f"pypdf extraction failed, attempting plain text fallback: {e}")
            try:
                raw_text = pdf_bytes.decode("utf-8", errors="ignore").strip()
                if raw_text:
                    pages_content.append({
                        "page_number": 1,
                        "text": raw_text
                    })
            except Exception:
                raise ValueError(f"Failed to process PDF content: {str(e)}")

        return pages_content

    @staticmethod
    def chunk_pdf_pages(
        pages_content: List[Dict[str, Any]],
        chunk_size: int = 800,
        chunk_overlap: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Split extracted PDF pages into text chunks with page number tracking.
        """
        chunks = []
        global_chunk_index = 0

        for page in pages_content:
            page_num = page["page_number"]
            text = page["text"]

            if len(text) <= chunk_size:
                chunks.append({
                    "chunk_index": global_chunk_index,
                    "chunk_text": text,
                    "page_number": page_num
                })
                global_chunk_index += 1
            else:
                start = 0
                while start < len(text):
                    end = min(start + chunk_size, len(text))
                    chunk_str = text[start:end].strip()
                    if chunk_str:
                        chunks.append({
                            "chunk_index": global_chunk_index,
                            "chunk_text": chunk_str,
                            "page_number": page_num
                        })
                        global_chunk_index += 1
                    if end == len(text):
                        break
                    start += (chunk_size - chunk_overlap)

        return chunks
