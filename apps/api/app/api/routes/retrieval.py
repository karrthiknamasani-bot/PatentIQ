from fastapi import APIRouter, HTTPException, status
from app.services.retrieval.types import SearchRequest, SearchResponse
from app.services.retrieval.retrieval_service import retrieval_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse, summary="Execute Prior-Art Retrieval")
async def search_prior_art(request: SearchRequest) -> SearchResponse:
    """Performs sparse (BM25) and/or dense (BGE + Qdrant) prior-art retrieval

    against the indexed patent corpus.
    Returns distinct result groups without RRF fusion.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    valid_methods = {"sparse", "bm25", "dense", "vector"}
    chosen_methods = {m.lower().strip() for m in request.methods}
    if not chosen_methods.intersection(valid_methods):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid retrieval method ('sparse' or 'dense') must be specified.",
        )

    if request.rerank:
        has_sparse = bool(chosen_methods.intersection({"sparse", "bm25"}))
        has_dense = bool(chosen_methods.intersection({"dense", "vector"}))
        if not (has_sparse and has_dense) and "hybrid" not in chosen_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reranking requires hybrid retrieval candidates (both 'sparse' and 'dense' methods must be specified).",
            )

    try:
        response = retrieval_service.search(request)
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prior-art retrieval failed: {str(exc)}",
        ) from exc
