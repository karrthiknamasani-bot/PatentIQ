import logging
from fastapi import APIRouter, HTTPException, status
from app.services.readiness.types import ReadinessAssessmentRequest, ReadinessAssessmentResponse
from app.services.readiness.readiness_engine import readiness_engine

logger = logging.getLogger("patentiq.api.readiness")

router = APIRouter()


@router.post(
    "/assess",
    response_model=ReadinessAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute deterministic EB-PRE patent readiness assessment",
    description="Constructs an Evidence Matrix and scores six transparent dimensions to compute an early-stage patent readiness indication.",
)
async def assess_patent_readiness(request: ReadinessAssessmentRequest) -> ReadinessAssessmentResponse:
    """Execute evidence-based patent readiness assessment."""
    try:
        response = readiness_engine.assess_readiness(
            project_id=request.project_id,
            features=request.features,
            mappings=request.mappings,
            weights=request.weights,
            thresholds=request.thresholds,
        )
        return response
    except ValueError as e:
        logger.warning("Validation error in readiness assessment: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Unexpected error during readiness assessment: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal readiness assessment error: {str(e)}",
        )
