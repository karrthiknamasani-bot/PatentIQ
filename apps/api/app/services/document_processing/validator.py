import os
from typing import Optional, Tuple
from app.core.config import settings


class DocumentValidationError(Exception):
    """Raised when an uploaded document fails validation checks."""
    pass


class DocumentValidator:
    """Validates file extension, size, and content validity before processing."""

    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    ALLOWED_MIME_PREFIXES = {"application/pdf", "application/vnd.openxmlformats-officedocument", "text/plain"}

    @classmethod
    def validate(
        cls,
        filename: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validates filename, size, and content.

        Returns (True, None) if valid, or (False, error_message) if invalid.
        """
        # 1. Filename presence
        if not filename or not filename.strip():
            return False, "Filename cannot be empty."

        # 2. Extension validation
        _, ext = os.path.splitext(filename.lower())
        if ext not in cls.ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(cls.ALLOWED_EXTENSIONS))
            return False, f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_list}"

        # 3. Empty file check
        file_size = len(file_bytes)
        if file_size == 0:
            return False, "Uploaded file is empty (0 bytes)."

        # 4. Maximum size validation
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, (
                f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed "
                f"limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # 5. Basic MIME type validation if explicitly provided
        if content_type:
            ct = content_type.lower().split(";")[0].strip()
            # Allow common generic streams if extension is valid
            generic_types = {"application/octet-stream", "binary/octet-stream"}
            if ct not in generic_types:
                if ext == ".pdf" and not ("pdf" in ct):
                    return False, f"MIME type '{content_type}' does not match .pdf extension."
                if ext == ".docx" and not ("officedocument" in ct or "word" in ct or "zip" in ct):
                    return False, f"MIME type '{content_type}' does not match .docx extension."
                if ext == ".txt" and not ("text" in ct or "plain" in ct):
                    return False, f"MIME type '{content_type}' does not match .txt extension."

        return True, None
