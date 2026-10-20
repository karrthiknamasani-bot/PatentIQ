import logging
import uuid
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from app.core.config import settings
from app.api.deps import get_current_user
from app.schemas.user import CurrentUser
from app.schemas.pipeline import PipelineAnalysisResponse
from app.services.document_processing.pipeline import document_pipeline
from app.services.features.feature_service import patent_feature_service
from app.services.retrieval.retrieval_service import retrieval_service
from app.services.retrieval.types import SearchRequest, RRFResult
from app.services.reranking.types import RerankedResult
from app.services.mapping.mapping_service import patent_mapping_service
from app.services.readiness.readiness_engine import readiness_engine
from app.services.explanation.grounded_explainer import grounded_explainer
from app.services.explanation.types import ExplanationRequest
from app.services.persistence.models import ProjectCreate
from app.services.persistence.repository import SupabaseRepository

logger = logging.getLogger("patentiq.api.pipeline")

router = APIRouter()
repository = SupabaseRepository()


@router.post("/analyze", response_model=PipelineAnalysisResponse, summary="Execute Full Patent Readiness Pipeline")
async def analyze_document_pipeline(
    file: UploadFile = File(..., description="Invention disclosure document (PDF, DOCX, TXT)"),
    title: Optional[str] = Form(None, description="Project title"),
    description: Optional[str] = Form(None, description="Invention summary"),
    domain: Optional[str] = Form("General Technology", description="Technical domain"),
    current_user: CurrentUser = Depends(get_current_user),
) -> PipelineAnalysisResponse:
    """Unified end-to-end pipeline orchestrator.

    Executes all 18 steps:
    1. Validate uploaded document
    2. Parse PDF/DOCX/TXT
    3. Clean and normalize text
    4. Detect patent sections
    5. Patent-aware chunking
    6. Technical feature extraction (AST/NLP)
    7. Prior-art retrieval query formulation per feature
    8. Hybrid retrieval (BM25 sparse + BGE dense + Qdrant)
    9. RRF fusion (k=60)
    10. BGE Cross-Encoder reranking
    11. Evidence candidate selection
    12. Feature -> Evidence mapping
    13. Evidence Matrix construction
    14. Deterministic EB-PRE readiness calculation
    15. Confidence score calculation
    16. Uncertainty flag generation
    17. Grounded Gemini explanation & 10-section report
    18. Persistence to Supabase / local demo store
    """
    start_time = time.time()
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file with a valid filename must be provided.",
        )

    ext = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {settings.ALLOWED_EXTENSIONS}",
        )

    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file stream.",
        ) from exc

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # -------------------------------------------------------------
    # STEP 1-5: Document Processing (Validation, Extraction, Sectioning, Chunking)
    # -------------------------------------------------------------
    logger.info("Executing Document Pipeline for file: %s", file.filename)
    doc_result = document_pipeline.process(
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=file.content_type,
    )

    if not doc_result.success or not doc_result.chunks:
        err_msg = doc_result.error or "Document parsing yielded no text chunks."
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=err_msg)

    # -------------------------------------------------------------
    # Create Project in Persistence Layer
    # -------------------------------------------------------------
    project_id = str(uuid.uuid4())
    proj_title = title.strip() if title and title.strip() else file.filename.rsplit(".", 1)[0].replace("_", " ").title()
    proj_desc = description.strip() if description and description.strip() else f"Automated Patent Readiness Assessment for {file.filename}."
    file_type = ext.replace(".", "")

    project_in = ProjectCreate(
        user_id=current_user.user_id,
        title=proj_title,
        description=proj_desc,
        original_file_name=file.filename,
        stored_file_name=f"{project_id}_{file.filename}",
        file_path=f"projects/{current_user.user_id}/{project_id}_{file.filename}",
        file_type=file_type,
        file_size=len(file_bytes),
        status="processing",
        processing_stage="document_processed",
    )
    p_status, project_record = await repository.create_project(project_in)
    if project_record:
        project_id = project_record.id

    # -------------------------------------------------------------
    # STEP 6: Technical Feature Extraction (AST / NLP Heuristics)
    # -------------------------------------------------------------
    logger.info("Extracting technical features for project: %s", project_id)
    feature_resp = patent_feature_service.extract_features(
        project_id=project_id,
        chunks=doc_result.chunks,
    )
    features = feature_resp.features
    if not features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unable to extract technical features from the provided document.",
        )

    # -------------------------------------------------------------
    # STEP 7-11: Hybrid Prior-Art Retrieval + RRF + BGE Cross-Encoder Reranking
    # -------------------------------------------------------------
    logger.info("Executing hybrid prior-art retrieval across %d features", len(features))
    seen_evidence: Dict[str, RerankedResult] = {}
    for i, feat in enumerate(features):
        query_text = feat.feature_text.strip()
        if not query_text:
            continue
        try:
            # Deep cross-encoder rerank top primary features (up to 6) for precision,
            # and use high-speed hybrid RRF for remaining features to avoid CPU timeouts
            should_rerank = (i < 6)
            search_req = SearchRequest(
                query=query_text,
                top_k=5,
                rerank=should_rerank,
                methods=["sparse", "dense"],
            )
            search_res = retrieval_service.search(search_req)
            raw_candidates = (
                search_res.reranked_results
                if (should_rerank and search_res.reranked_results)
                else (search_res.hybrid_results or [])
            )
            for cand in raw_candidates:
                key = f"{cand.patent_number}#{cand.chunk_index}"
                if key not in seen_evidence:
                    if isinstance(cand, RRFResult):
                        cand = RerankedResult(
                            patent_number=cand.patent_number,
                            patent_id=cand.metadata.get("patent_id") if cand.metadata else None,
                            chunk_id=cand.chunk_id,
                            chunk_index=cand.chunk_index,
                            text=cand.text,
                            section=cand.section,
                            claim_number=cand.claim_number,
                            page_number=cand.page_number,
                            paragraph_id=cand.paragraph_id,
                            source=cand.source,
                            metadata=cand.metadata,
                            sparse_rank=cand.sparse_rank,
                            dense_rank=cand.dense_rank,
                            sparse_score=cand.sparse_score,
                            dense_score=cand.dense_score,
                            rrf_score=float(cand.rrf_score),
                            reranker_score=float(cand.rrf_score),
                            reranker_rank=int(cand.fused_rank),
                            retrieval_method="hybrid_rrf",
                        )
                    seen_evidence[key] = cand
        except Exception as exc:
            logger.warning("Retrieval failed for feature '%s': %s", feat.feature_id, exc)

    all_evidence = list(seen_evidence.values())
    logger.info("Retrieved and reranked %d unique prior-art evidence candidates", len(all_evidence))

    # -------------------------------------------------------------
    # STEP 12: Feature -> Evidence Mapping
    # -------------------------------------------------------------
    mappings = []
    if all_evidence:
        logger.info("Mapping %d features to %d evidence items", len(features), len(all_evidence))
        mapping_res = patent_mapping_service.map_features_to_evidence(
            project_id=project_id,
            features=features,
            evidence=all_evidence,
            top_k=3,
        )
        mappings = mapping_res.mappings
    else:
        logger.warning("No prior-art candidates retrieved for project %s", project_id)

    # -------------------------------------------------------------
    # STEP 13-16: Evidence Matrix & Deterministic EB-PRE Assessment
    # -------------------------------------------------------------
    logger.info("Evaluating deterministic EB-PRE for project: %s", project_id)
    assessment = readiness_engine.assess_readiness(
        project_id=project_id,
        features=features,
        mappings=mappings,
    )

    if not all_evidence:
        assessment.uncertainty_flags.append(
            "No relevant prior art was retrieved within the configured search scope."
        )

    # -------------------------------------------------------------
    # STEP 17: Grounded Gemini Explanation & Structured Reporting
    # -------------------------------------------------------------
    t_expl_start = time.perf_counter()
    logger.info("[PERF] Step 17: Starting explanation generation...")
    explanation_req = ExplanationRequest(
        project_id=project_id,
        features=features,
        evidence_matrix=assessment.evidence_matrix,
        mappings=mappings,
        eb_pre_assessment=assessment,
    )
    explanation_res = await grounded_explainer.explain_assessment(explanation_req)
    t_expl_dur = time.perf_counter() - t_expl_start
    gen_method = "deterministic_fallback" if explanation_res.fallback_used else "gemini"
    logger.info(
        "[PERF] Step 17 explanation complete: model=%s, fallback=%s (took %.3fs)",
        explanation_res.model,
        explanation_res.fallback_used,
        t_expl_dur,
    )

    # -------------------------------------------------------------
    # STEP 18: Persistence (Supabase PostgreSQL / Local Demo Store)
    # -------------------------------------------------------------
    t_persist_start = time.perf_counter()
    logger.info("[PERF] Step 18: Starting persistence...")

    tp1 = time.perf_counter()
    st_chunks = await repository.save_document_chunks(
        project_id=project_id,
        chunks=doc_result.chunks,
        user_id=current_user.user_id,
    )
    logger.info("[PERF] save_document_chunks: status=%s (took %.3fs)", st_chunks.status, time.perf_counter() - tp1)

    tp2 = time.perf_counter()
    st_feats = await repository.save_features(
        project_id=project_id,
        features=features,
        user_id=current_user.user_id,
    )
    logger.info("[PERF] save_features: status=%s (took %.3fs)", st_feats.status, time.perf_counter() - tp2)

    if mappings:
        tp3 = time.perf_counter()
        st_ev = await repository.save_evidence_items(
            project_id=project_id,
            mappings=mappings,
            user_id=current_user.user_id,
        )
        logger.info("[PERF] save_evidence_items: status=%s (took %.3fs)", st_ev.status, time.perf_counter() - tp3)

    tp4 = time.perf_counter()
    st_ana = await repository.save_analysis(
        project_id=project_id,
        assessment=assessment,
        explanation=explanation_res.explanation,
        report_meta={
            "model": explanation_res.model,
            "generation_latency_ms": int((time.time() - start_time) * 1000),
        },
        user_id=current_user.user_id,
    )
    logger.info("[PERF] save_analysis: status=%s (took %.3fs)", st_ana.status, time.perf_counter() - tp4)

    tp5 = time.perf_counter()
    st_rep = await repository.save_report(
        project_id=project_id,
        report_data=explanation_res.report,
        report_type="json",
        user_id=current_user.user_id,
    )
    logger.info("[PERF] save_report: status=%s (took %.3fs)", st_rep.status, time.perf_counter() - tp5)

    t_persist_dur = time.perf_counter() - t_persist_start
    logger.info("[PERF] Step 18 total persistence took %.3fs", t_persist_dur)

    # -------------------------------------------------------------
    # Format Unified Response Payload
    # -------------------------------------------------------------
    t_resp_start = time.perf_counter()
    total_latency = int((time.time() - start_time) * 1000)
    dim_scores_dict = {
        k: v.model_dump() for k, v in assessment.dimension_scores.items()
    }


    evidence_matrix_dict = (
        assessment.evidence_matrix.model_dump()
        if assessment.evidence_matrix
        else {}
    )

    return PipelineAnalysisResponse(
        project_id=project_id,
        title=proj_title,
        filename=file.filename,
        file_type=file_type,
        file_size=len(file_bytes),
        chunk_count=len(doc_result.chunks),
        feature_count=len(features),
        prior_art_hit_count=len(all_evidence),
        mapping_count=len(mappings),
        readiness_score=assessment.readiness_score,
        readiness_percentage=assessment.readiness_percentage,
        confidence_score=assessment.confidence_score,
        readiness_category=assessment.readiness_category.value,
        category_display=assessment.category_display,
        dimension_scores=dim_scores_dict,
        weights=assessment.assessment_metadata.weights,
        uncertainty_flags=assessment.uncertainty_flags,
        features=[f.model_dump() for f in features],
        mappings=[m.model_dump() for m in mappings],
        evidence_matrix=evidence_matrix_dict,
        report=explanation_res.report.model_dump(),
        executive_summary=explanation_res.explanation.executive_summary,
        generation_method=gen_method,
        generation_latency_ms=total_latency,
        persisted=True,
    )
