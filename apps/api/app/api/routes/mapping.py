import math
from fastapi import APIRouter, HTTPException, status
from app.services.mapping.types import (
    FeatureEvidenceMappingRequest,
    FeatureEvidenceMappingResponse,
)
from app.services.mapping.mapping_service import patent_mapping_service

router = APIRouter()


@router.post(
    "/feature-evidence",
    response_model=FeatureEvidenceMappingResponse,
    summary="Map Technical Features to Prior-Art Evidence",
)
async def map_features_to_evidence(
    request: FeatureEvidenceMappingRequest,
) -> FeatureEvidenceMappingResponse:
    """Connects technical features to retrieved prior-art passages using combined lexical-semantic similarity

    and deterministic relationship classification.
    Does NOT calculate patentability, novelty, or EB-PRE readiness scores.
    """
    if not request.project_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id cannot be empty.",
        )

    if not request.features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one technical feature must be provided for mapping.",
        )

    if not request.evidence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one prior-art evidence candidate must be provided for mapping.",
        )

    if request.lexical_weight is not None and request.semantic_weight is not None:
        if not math.isclose(request.lexical_weight + request.semantic_weight, 1.0, rel_tol=1e-3):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"lexical_weight ({request.lexical_weight}) + semantic_weight ({request.semantic_weight}) must sum to 1.0.",
            )

    try:
        response = patent_mapping_service.map_features_to_evidence(
            project_id=request.project_id,
            features=request.features,
            evidence=request.evidence,
            top_k=request.top_k,
            lexical_weight=request.lexical_weight,
            semantic_weight=request.semantic_weight,
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
            detail=f"Feature-to-evidence mapping failed: {str(exc)}",
        ) from exc
