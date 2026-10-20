"""Pydantic schemas package."""
from app.schemas.health import HealthResponse, DatabaseHealthResponse
from app.schemas.user import CurrentUser
from app.schemas.document import (
    DocumentMetadata,
    ExtractedSegment,
    DocumentChunk,
    DocumentProcessingResult,
    DocumentProcessResponse,
)

from app.schemas.patent import (
    PatentDocumentBase,
    PatentDocumentCreate,
    PatentDocument,
    PatentChunkBase,
    PatentChunkCreate,
    PatentChunk,
    PatentProvenance,
    CorpusManifest,
    CorpusValidationReport,
    CorpusQualityStats,
    ValidationIssue,
)

__all__ = [
    "HealthResponse",
    "DatabaseHealthResponse",
    "CurrentUser",
    "DocumentMetadata",
    "ExtractedSegment",
    "DocumentChunk",
    "DocumentProcessingResult",
    "DocumentProcessResponse",
    "PatentDocumentBase",
    "PatentDocumentCreate",
    "PatentDocument",
    "PatentChunkBase",
    "PatentChunkCreate",
    "PatentChunk",
    "PatentProvenance",
    "CorpusManifest",
    "CorpusValidationReport",
    "CorpusQualityStats",
    "ValidationIssue",
]
