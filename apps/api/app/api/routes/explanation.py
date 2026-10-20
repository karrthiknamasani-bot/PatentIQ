import logging
from fastapi import APIRouter, HTTPException, status
from app.services.explanation.types import ExplanationRequest, ExplanationResponse
from app.services.explanation.grounded_explainer import grounded_explainer

logger = logging.getLogger("patentiq.api.explanation")

router = APIRouter()


@router.post(
    "/generate",
    response_model=ExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate grounded AI explanation and structured assessment report",
    description="Transforms deterministic EB-PRE assessment into an auditable, evidence-grounded report using Gemini 3.1 Pro Preview or deterministic fallback.",
)
async def generate_explanation(request: ExplanationRequest) -> ExplanationResponse:
    """Execute grounded explanation pipeline."""
    try:
        if not request.project_id or not request.project_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_id must not be empty",
            )
        if not request.features:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="features list must not be empty",
            )

        response = await grounded_explainer.explain_assessment(request)
        return response
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Validation error in explanation endpoint: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Unexpected error during explanation generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal explanation error: {str(e)}",
        )
