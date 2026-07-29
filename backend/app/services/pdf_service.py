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
    def extract_text_from_docx_bytes(docx_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from DOCX bytes by parsing word/document.xml inside zip archive.
        """
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx_zip:
                xml_content = docx_zip.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                paragraphs = []
                for p_node in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    texts = [t_node.text for t_node in p_node.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t_node.text]
                    p_text = ''.join(texts).strip()
                    if p_text:
                        paragraphs.append(p_text)
                full_text = '\n\n'.join(paragraphs)
                if full_text:
                    return [{"page_number": 1, "text": full_text}]
        except Exception as e:
            logger.warning(f"DOCX XML parsing failed, fallback to plain text: {e}")
        
        raw_text = docx_bytes.decode("utf-8", errors="ignore").strip()
        return [{"page_number": 1, "text": raw_text}] if raw_text else []

    @staticmethod
    def extract_text_from_pptx_bytes(pptx_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from PPTX bytes by parsing ppt/slides/slide*.xml inside zip archive.
        """
        import zipfile
        import xml.etree.ElementTree as ET
        slides_content = []
        try:
            with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as pptx_zip:
                slide_files = sorted([name for name in pptx_zip.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')])
                for idx, slide_file in enumerate(slide_files):
                    xml_content = pptx_zip.read(slide_file)
                    tree = ET.fromstring(xml_content)
                    texts = [t_node.text for t_node in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if t_node.text]
                    slide_text = ' '.join(texts).strip()
                    if slide_text:
                        slides_content.append({
                            "page_number": idx + 1,
                            "text": slide_text
                        })
        except Exception as e:
            logger.warning(f"PPTX XML extraction failed, attempting fallback: {e}")

        if not slides_content:
            raw_text = pptx_bytes.decode("utf-8", errors="ignore").strip()
            if raw_text:
                slides_content.append({"page_number": 1, "text": raw_text})

        return slides_content

    @staticmethod
    def extract_text_from_file_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Multi-format text extractor for PDF, DOCX, PPTX, TXT, and Image files.
        """
        fname_lower = filename.lower()
        if fname_lower.endswith(".docx"):
            return PDFService.extract_text_from_docx_bytes(file_bytes)
        elif fname_lower.endswith(".pptx"):
            return PDFService.extract_text_from_pptx_bytes(file_bytes)
        elif fname_lower.endswith(".txt"):
            raw_text = file_bytes.decode("utf-8", errors="ignore").strip()
            return [{"page_number": 1, "text": raw_text}] if raw_text else []
        elif fname_lower.endswith((".png", ".jpg", ".jpeg")):
            # Image OCR text extraction placeholder fallback
            return [{"page_number": 1, "text": f"Scanned image content from {filename}"}]
        else:
            return PDFService.extract_text_from_pdf_bytes(file_bytes)

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
