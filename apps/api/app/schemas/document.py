from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata describing the uploaded input document."""

    filename: str = Field(..., description="Original name of the uploaded file")
    extension: str = Field(..., description="File extension (e.g. .pdf, .docx, .txt)")
    mime_type: Optional[str] = Field(None, description="Reported or detected MIME type")
    file_size: int = Field(..., description="File size in bytes")
    title: Optional[str] = Field(None, description="Extracted or inferred document title")
    page_count: Optional[int] = Field(None, description="Number of pages if available")
    source_type: str = Field(..., description="Format category: pdf, docx, or txt")


class ExtractedSegment(BaseModel):
    """A discrete unit of text extracted from the document (e.g. a page or section block)."""

    text: str = Field(..., description="Raw text of the segment")
    section: str = Field(default="unknown", description="Identified document section name")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    source_reference: Optional[str] = Field(None, description="Traceable reference (e.g. page:1, para:4)")


class DocumentChunk(BaseModel):
    """Patent-aware chunk with traceability metadata for vector indexing and evidence mapping."""

    chunk_index: int = Field(..., description="Sequential index of the chunk in the document")
    text: str = Field(..., description="Chunk content")
    section: str = Field(default="unknown", description="Document section (e.g. claims, abstract)")
    page_number: Optional[int] = Field(None, description="Origin page number if known")
    claim_number: Optional[int] = Field(None, description="Claim number if this chunk is a claim")
    source_reference: Optional[str] = Field(None, description="Origin span or paragraph reference")
    start_character: int = Field(..., description="Start character offset in full cleaned text")
    end_character: int = Field(..., description="End character offset in full cleaned text")
    token_estimate: int = Field(..., description="Estimated token count (approx. 4 chars per token)")


class DocumentProcessingResult(BaseModel):
    """Full internal result object returned by the document processing pipeline."""

    success: bool = Field(..., description="Whether processing completed without fatal error")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    extracted_segments: List[ExtractedSegment] = Field(default_factory=list, description="Extracted segments")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="Generated patent-aware chunks")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings (e.g. scanned pages)")
    error: Optional[str] = Field(None, description="Fatal error description if success is False")


class DocumentProcessResponse(BaseModel):
    """Safe, concise HTTP API response summarizing processing without returning gigantic text."""

    success: bool
    filename: str
    file_type: str
    page_count: Optional[int] = None
    detected_sections: List[str] = Field(default_factory=list)
    chunk_count: int = 0
    sample_chunks: List[DocumentChunk] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_status: str
    error: Optional[str] = None
