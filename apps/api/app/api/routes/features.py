from fastapi import APIRouter, HTTPException, status
from app.services.features.feature_schema import (
    FeatureExtractionRequest,
    FeatureExtractionResponse,
)
from app.services.features.feature_service import patent_feature_service

router = APIRouter()


@router.post(
    "/extract",
    response_model=FeatureExtractionResponse,
    summary="Extract Technical Features from Document Chunks",
)
async def extract_technical_features(
    request: FeatureExtractionRequest,
) -> FeatureExtractionResponse:
    """Transforms processed invention document chunks into a structured,

    provenance-grounded set of technical features.
    Does not infer novelty, patentability, or calculate EB-PRE scores.
    """
    if not request.project_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id cannot be empty.",
        )

    if not request.chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one document chunk must be provided for feature extraction.",
        )

    try:
        response = patent_feature_service.extract_features(
            project_id=request.project_id,
            chunks=request.chunks,
            method=request.method,
        )
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Technical feature extraction failed: {str(exc)}",
        ) from exc
