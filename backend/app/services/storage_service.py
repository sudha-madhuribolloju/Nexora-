"""
app/services/storage_service.py
────────────────────────────────
Abstract Storage Service for NEXORA AI Classroom.
Handles local disk media storage and Range-header enabled video streaming.
Designed for seamless future migration to AWS S3, Azure Blob, or OCI Object Storage.
"""

import os
import math
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Generator, BinaryIO
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

logger = logging.getLogger("app.services.storage_service")

RECORDINGS_DIR = os.path.join(os.getcwd(), "uploads", "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)


class BaseStorageProvider(ABC):
    @abstractmethod
    def save_file(self, content: bytes, filename: str) -> Tuple[str, int]:
        pass

    @abstractmethod
    def get_file_stream_response(
        self, storage_path: str, filename: str, range_header: Optional[str] = None
    ) -> StreamingResponse:
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        pass


class LocalStorageProvider(BaseStorageProvider):
    """
    Local filesystem storage provider with HTTP 206 Range Request streaming support.
    """

    def save_file(self, content: bytes, filename: str) -> Tuple[str, int]:
        storage_path = os.path.join(RECORDINGS_DIR, filename)
        with open(storage_path, "wb") as f:
            f.write(content)
        file_size = os.path.getsize(storage_path) if os.path.exists(storage_path) else len(content)
        return storage_path, file_size

    def get_file_stream_response(
        self, storage_path: str, filename: str, range_header: Optional[str] = None
    ) -> StreamingResponse:
        if not os.path.exists(storage_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording video file not found on disk."
            )

        file_size = os.path.getsize(storage_path)
        media_type = "video/webm" if filename.endswith(".webm") else "video/mp4"

        if not range_header:
            def iterfile():
                with open(storage_path, "rb") as f:
                    yield from f

            headers = {
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Content-Disposition": f'inline; filename="{filename}"'
            }
            return StreamingResponse(
                iterfile(),
                media_type=media_type,
                headers=headers,
                status_code=status.HTTP_200_OK
            )

        # Parse HTTP Range header (e.g., bytes=0-1024 or bytes=1024-)
        try:
            range_unit, range_val = range_header.strip().split("=")
            if range_unit != "bytes":
                raise ValueError("Invalid range unit")

            start_str, end_str = range_val.split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except Exception:
            start = 0
            end = file_size - 1

        if start >= file_size or start > end:
            raise HTTPException(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail=f"Requested range [{range_header}] out of bounds for file of size {file_size} bytes.",
                headers={"Content-Range": f"bytes */{file_size}"}
            )

        end = min(end, file_size - 1)
        chunk_size = (end - start) + 1

        def range_generator(path: str, offset: int, bytes_to_read: int, buffer_size: int = 64 * 1024):
            with open(path, "rb") as f:
                f.seek(offset)
                remaining = bytes_to_read
                while remaining > 0:
                    read_len = min(buffer_size, remaining)
                    data = f.read(read_len)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Disposition": f'inline; filename="{filename}"'
        }

        return StreamingResponse(
            range_generator(storage_path, start, chunk_size),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type=media_type,
            headers=headers
        )

    def delete_file(self, storage_path: str) -> bool:
        if os.path.exists(storage_path):
            try:
                os.remove(storage_path)
                return True
            except Exception as e:
                logger.error(f"Failed to delete file {storage_path}: {e}")
                return False
        return False


class StorageService:
    """
    Singleton StorageService proxy. Defaults to LocalStorageProvider.
    """
    _provider: BaseStorageProvider = LocalStorageProvider()

    @classmethod
    def save_file(cls, content: bytes, filename: str) -> Tuple[str, int]:
        return cls._provider.save_file(content, filename)

    @classmethod
    def get_file_stream_response(
        cls, storage_path: str, filename: str, range_header: Optional[str] = None
    ) -> StreamingResponse:
        return cls._provider.get_file_stream_response(storage_path, filename, range_header)

    @classmethod
    def delete_file(cls, storage_path: str) -> bool:
        return cls._provider.delete_file(storage_path)
