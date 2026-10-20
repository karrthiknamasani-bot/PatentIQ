from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.document import DocumentProcessResponse
from app.services.document_processing.pipeline import document_pipeline

router = APIRouter()


@router.post("/process", response_model=DocumentProcessResponse, summary="Process Invention Document")
async def process_document(
    file: UploadFile = File(..., description="Uploaded PDF, DOCX, or TXT document"),
) -> DocumentProcessResponse:
    """Validates, extracts, sanitizes, identifies sections, and chunks an invention document

    using patent-aware structure heuristics.
    Does not persist to database or storage in this step.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must be provided in the upload request.",
        )

    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file stream.",
        ) from exc

    result = document_pipeline.process(
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=file.content_type,
    )

    if not result.success:
        err_msg = result.error or "Document processing failed."
        # Map validation and extraction errors to appropriate HTTP status codes
        if "exceeds maximum allowed limit" in err_msg:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=err_msg)
        if "empty" in err_msg.lower() or "unsupported" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        # Extraction/parsing errors (corrupted or non-text files)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=err_msg)

    # Compile unique detected sections in order of occurrence
    detected_sections = list(dict.fromkeys(
        c.section for c in result.chunks if c.section and c.section != "unknown"
    ))

    # Return sample chunks (up to 3) to keep response concise
    sample_chunks = result.chunks[:3]

    return DocumentProcessResponse(
        success=True,
        filename=result.metadata.filename,
        file_type=result.metadata.source_type,
        page_count=result.metadata.page_count,
        detected_sections=detected_sections,
        chunk_count=len(result.chunks),
        sample_chunks=sample_chunks,
        warnings=result.warnings,
        processing_status="completed",
        error=None,
    )
