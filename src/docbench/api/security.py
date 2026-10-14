"""
Security, validation, and temporary file isolation utilities for PDF upload handling.
"""

import os
import re
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Tuple, Optional
from fastapi import UploadFile, HTTPException, status

from docbench.api.config import api_settings

PDF_MAGIC_BYTES = b"%PDF-"
MAX_FILENAME_LENGTH = 120


def sanitize_filename(filename: str) -> str:
    """
    Sanitize user-supplied filename to prevent directory traversal or filesystem injection.
    Strips path separators, null bytes, parent directory references, and control characters.
    """
    if not filename:
        return "uploaded_document.pdf"

    # Remove path components
    base = os.path.basename(filename)
    # Strip null bytes and control chars
    base = re.sub(r"[\x00-\x1f\x7f]", "", base)
    # Strip dangerous characters, retain alphanumerics, underscores, hyphens, periods
    cleaned = re.sub(r"[^\w\.\-]", "_", base)
    # Remove leading dots to prevent hidden files
    cleaned = cleaned.lstrip(".")

    if not cleaned or not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned.rstrip('.')}.pdf" if cleaned else "document.pdf"

    if len(cleaned) > MAX_FILENAME_LENGTH:
        stem = cleaned[:-4][: MAX_FILENAME_LENGTH - 4]
        cleaned = f"{stem}.pdf"

    return cleaned


def validate_pdf_content_type(upload_file: UploadFile):
    """
    Validate that the incoming upload specifies a PDF filename and media type.
    """
    filename = upload_file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Only PDF files (.pdf) are permitted. Received: '{filename}'",
        )

    content_type = (upload_file.content_type or "").lower().strip()
    allowed_types = {"application/pdf", "application/x-pdf", "application/octet-stream"}
    if content_type and content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported Content-Type '{content_type}'. Must be 'application/pdf'.",
        )


@asynccontextmanager
async def bounded_temp_pdf(
    upload_file: UploadFile,
    max_size_bytes: int = None,
) -> AsyncGenerator[Tuple[Path, str, int], None]:
    """
    Asynchronously stream UploadFile in bounded chunks to an isolated temporary file on disk.
    Enforces maximum size limit and validates PDF magic header without retaining files.
    Ensures temporary file is unconditionally deleted in finally block.
    """
    if max_size_bytes is None:
        max_size_bytes = api_settings.max_upload_size_bytes
    validate_pdf_content_type(upload_file)
    api_settings.ensure_temp_dir()

    sanitized_name = sanitize_filename(upload_file.filename or "document.pdf")
    unique_suffix = f"_{uuid.uuid4().hex[:12]}.pdf"
    temp_path = api_settings.temp_dir / f"upload{unique_suffix}"

    total_bytes = 0
    chunk_size = 64 * 1024  # 64 KB read buffer
    first_chunk = True

    try:
        with open(temp_path, "wb") as out_f:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    max_mb = max_size_bytes / (1024 * 1024)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeded maximum permitted file size limit of {max_mb:.1f} MB.",
                    )

                if first_chunk:
                    # Check for PDF magic bytes within the first 1024 bytes
                    # (Note: PDF magic bytes confirm format header, but do not guarantee safety against all exploits)
                    if PDF_MAGIC_BYTES not in chunk[:1024]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid PDF signature. File does not contain '%PDF-' header.",
                        )
                    first_chunk = False

                out_f.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file received. Uploaded PDF must contain valid binary content.",
            )

        yield temp_path, sanitized_name, total_bytes

    finally:
        # Unconditionally remove temporary file from disk
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
