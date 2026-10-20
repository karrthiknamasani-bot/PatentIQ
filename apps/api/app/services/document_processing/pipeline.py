import os
from typing import Optional, List
from app.schemas.document import (
    DocumentMetadata,
    DocumentProcessingResult,
    DocumentChunk,
    ExtractedSegment,
)
from app.services.document_processing.validator import DocumentValidator
from app.services.document_processing.pdf_parser import PDFParser
from app.services.document_processing.docx_parser import DOCXParser
from app.services.document_processing.txt_parser import TXTParser
from app.services.document_processing.chunker import PatentAwareChunker


class DocumentProcessingPipeline:
    """Orchestrates end-to-end document validation, text extraction, cleaning,

    section detection, and patent-aware chunking.
    Independent of HTTP layer.
    """

    def __init__(
        self,
        chunk_max_chars: Optional[int] = None,
        chunk_overlap_chars: Optional[int] = None,
    ) -> None:
        self.chunker = PatentAwareChunker(
            max_chars=chunk_max_chars,
            overlap_chars=chunk_overlap_chars,
        )

    def process(
        self,
        filename: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> DocumentProcessingResult:
        """Processes raw document bytes into clean, traceable patent-aware chunks."""
        _, ext = os.path.splitext(filename.lower())
        file_size = len(file_bytes)

        # 1. Validation
        is_valid, validation_err = DocumentValidator.validate(filename, file_bytes, content_type)
        if not is_valid:
            return DocumentProcessingResult(
                success=False,
                metadata=DocumentMetadata(
                    filename=filename,
                    extension=ext,
                    mime_type=content_type,
                    file_size=file_size,
                    source_type=ext.lstrip(".") or "unknown",
                ),
                error=validation_err,
            )

        # 2. Extraction & Parsing based on file format
        source_type = ext.lstrip(".")
        warnings: List[str] = []
        segments: List[ExtractedSegment] = []
        meta_dict = {}

        try:
            if ext == ".pdf":
                segments, meta_dict, warnings = PDFParser.parse(file_bytes)
            elif ext == ".docx":
                segments, meta_dict, warnings = DOCXParser.parse(file_bytes)
            elif ext == ".txt":
                segments, meta_dict, warnings = TXTParser.parse(file_bytes)
            else:
                return DocumentProcessingResult(
                    success=False,
                    metadata=DocumentMetadata(
                        filename=filename,
                        extension=ext,
                        mime_type=content_type,
                        file_size=file_size,
                        source_type=source_type,
                    ),
                    error=f"No parser available for extension '{ext}'",
                )
        except Exception as exc:
            return DocumentProcessingResult(
                success=False,
                metadata=DocumentMetadata(
                    filename=filename,
                    extension=ext,
                    mime_type=content_type,
                    file_size=file_size,
                    source_type=source_type,
                ),
                error=str(exc),
                warnings=warnings,
            )

        # 3. Patent-Aware Chunking
        chunks: List[DocumentChunk] = self.chunker.chunk_document(segments)

        # 4. Construct Metadata
        metadata = DocumentMetadata(
            filename=filename,
            extension=ext,
            mime_type=content_type,
            file_size=file_size,
            title=meta_dict.get("title"),
            page_count=meta_dict.get("page_count"),
            source_type=source_type,
        )

        return DocumentProcessingResult(
            success=True,
            metadata=metadata,
            extracted_segments=segments,
            chunks=chunks,
            warnings=warnings,
            error=None,
        )


# Global singleton instance with default settings
document_pipeline = DocumentProcessingPipeline()
