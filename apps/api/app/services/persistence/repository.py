import logging
import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from app.core.config import settings
from app.services.supabase_service import SupabaseService, supabase_service as default_supabase_service
from app.schemas.document import DocumentChunk
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping
from app.services.readiness.types import ReadinessAssessmentResponse
from app.services.explanation.types import GroundedExplanation, EvidenceBasedReport
from app.services.persistence.models import (
    ProjectCreate,
    ProjectRecord,
    DocumentChunkRecord,
    FeatureRecord,
    EvidenceItemRecord,
    AnalysisRecord,
    ReportRecord,
    PersistenceStatus,
)
from app.services.persistence.sqlite_store import get_sqlite_store

logger = logging.getLogger("patentiq.persistence.repository")


class SupabaseRepository:
    """Centralized persistence repository for PatentIQ application data.

    Enforces:
    - User ownership and RLS boundaries via projects.user_id
    - Separation of storage: Relational in Supabase, Vector embeddings in Qdrant (NO pgvector)
    - Exact numerical preservation for EB-PRE scores and Step 10 explanations
    - Idempotent writes across all entities
    - Safe partial failure reporting
    """

    DEFAULT_TIMEOUT_SECONDS: float = 5.0

    # Class-level shared in-memory demo store for unconfigured local developer environment
    _demo_projects: Dict[str, Dict[str, Any]] = {}
    _demo_chunks: Dict[str, List[Dict[str, Any]]] = {}
    _demo_features: Dict[str, List[Dict[str, Any]]] = {}
    _demo_evidence: Dict[str, List[Dict[str, Any]]] = {}
    _demo_analyses: Dict[str, Dict[str, Any]] = {}
    _demo_reports: Dict[str, Dict[str, Any]] = {}

    def __init__(self, service: Optional[SupabaseService] = None):
        self.service = service or default_supabase_service

    def _is_local_user(self, user_id: str) -> bool:
        """Determines if a user is eligible for durable local SQLite persistence."""
        if user_id == settings.DEMO_USER_ID or user_id.startswith("00000000-"):
            return True
        try:
            store = get_sqlite_store()
            return store.get_user_profile(user_id) is not None
        except Exception:
            return False

    async def _run_bounded(self, fn, timeout_sec: Optional[float] = None) -> Any:
        """Executes a synchronous DB callable with a strict bounded timeout in a worker thread."""
        to = timeout_sec or self.DEFAULT_TIMEOUT_SECONDS
        return await asyncio.wait_for(asyncio.to_thread(fn), timeout=to)


    def _get_client(self, user_token: Optional[str] = None):
        """Resolves the appropriate user client respecting RLS.

        Normal user operations use the authenticated client or public anon client.
        Never falls back to service role for normal user data access.
        """
        if not self.service.is_configured:
            return None
        return self.service.get_client()

    def _get_admin_client(self):
        """Resolves elevated service role client for global corpus administration only."""
        if not self.service.is_admin_configured:
            return None
        return self.service.get_admin_client()

    # =========================================================================
    # 1. Project Persistence
    # =========================================================================

    async def create_project(
        self,
        project_in: ProjectCreate,
        user_token: Optional[str] = None,
    ) -> Tuple[PersistenceStatus, Optional[ProjectRecord]]:
        """Creates a new user project record."""
        client = self._get_client(user_token)
        if client is None:
            if settings.ENVIRONMENT.lower() != "production" and self._is_local_user(project_in.user_id):
                proj_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)
                data = project_in.model_dump()
                data.update({
                    "id": proj_id,
                    "created_at": now,
                    "updated_at": now,
                    "extracted_text": None,
                    "extracted_metadata": {},
                    "error_message": None,
                    "report_generated": False,
                    "progress": 0,
                })
                try:
                    store = get_sqlite_store()
                    store.create_project(data)
                except Exception as exc:
                    logger.warning("SQLite project creation fallback error: %s", exc)

                self._demo_projects[proj_id] = data
                record = ProjectRecord(**data)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=proj_id,
                    affected_count=1,
                    details="Project workspace created in local durable store.",
                ), record

            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase credentials not configured in environment.",
            ), None

        try:
            payload = project_in.model_dump()
            res = client.table("projects").insert(payload).execute()
            if not res.data:
                return PersistenceStatus(
                    success=False,
                    status="failed",
                    error="Insert returned empty result",
                ), None

            record = ProjectRecord(**res.data[0])
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=record.id,
                affected_count=1,
                details="Project workspace created successfully.",
            ), record
        except Exception as e:
            logger.warning("Project creation persistence failed: %s", type(e).__name__)
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            ), None

    async def get_project(
        self,
        project_id: str,
        user_id: str,
        user_token: Optional[str] = None,
    ) -> Optional[ProjectRecord]:
        """Fetches a project by ID with strict user ownership validation."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_p = store.get_project(project_id, user_id)
                if db_p:
                    return ProjectRecord(**db_p)
            except Exception as exc:
                logger.warning("SQLite get_project failed: %s", exc)

            if project_id in self._demo_projects and self._demo_projects[project_id].get("user_id") == user_id:
                return ProjectRecord(**self._demo_projects[project_id])
            return None

        try:
            res = (
                client.table("projects")
                .select("*")
                .eq("id", project_id)
                .eq("user_id", user_id)
                .execute()
            )
            if res.data:
                return ProjectRecord(**res.data[0])
            return None
        except Exception as e:
            logger.warning("Get project failed: %s", type(e).__name__)
            return None

    async def list_projects(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        user_token: Optional[str] = None,
    ) -> List[ProjectRecord]:
        """Lists projects owned by the specified user."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_projects = store.list_projects(user_id, limit=limit, offset=offset)
                if db_projects:
                    return [ProjectRecord(**p) for p in db_projects]
            except Exception as exc:
                logger.warning("SQLite list_projects failed: %s", exc)

            projects = [
                ProjectRecord(**p)
                for p in self._demo_projects.values()
                if p.get("user_id") == user_id
            ]
            projects.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
            return projects[offset:offset + limit]

        try:
            res = (
                client.table("projects")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return [ProjectRecord(**item) for item in (res.data or [])]
        except Exception as e:
            logger.warning("List projects failed: %s", type(e).__name__)
            return []

    async def delete_project(
        self,
        project_id: str,
        user_id: str,
        user_token: Optional[str] = None,
    ) -> PersistenceStatus:
        """Deletes a project and its associated records owned by the specified user."""
        client = self._get_client(user_token)
        if client is None:
            deleted_sqlite = False
            try:
                store = get_sqlite_store()
                deleted_sqlite = store.delete_project(project_id, user_id)
            except Exception as exc:
                logger.warning("SQLite delete_project failed: %s", exc)

            if deleted_sqlite or (project_id in self._demo_projects and self._demo_projects[project_id].get("user_id") == user_id):
                self._demo_projects.pop(project_id, None)
                self._demo_chunks.pop(project_id, None)
                self._demo_features.pop(project_id, None)
                self._demo_evidence.pop(project_id, None)
                self._demo_analyses.pop(project_id, None)
                self._demo_reports.pop(project_id, None)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=project_id,
                    affected_count=1,
                    details="Project deleted from local durable store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error="Project not found or user unauthorized.",
            )

        try:
            res = (
                client.table("projects")
                .delete()
                .eq("id", project_id)
                .eq("user_id", user_id)
                .execute()
            )
            affected = len(res.data) if res.data else 0
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=project_id,
                affected_count=affected,
                details="Project deleted successfully.",
            )
        except Exception as e:
            logger.warning("Delete project failed: %s", type(e).__name__)
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    # =========================================================================
    # 2. Document Chunks Persistence
    # =========================================================================

    async def save_document_chunks(
        self,
        project_id: str,
        chunks: List[DocumentChunk],
        user_id: str,
        user_token: Optional[str] = None,
    ) -> PersistenceStatus:
        """Persists Step 3 document chunks idempotently."""
        t_start = time.perf_counter()
        client = self._get_client(user_token)
        if client is None:
            if settings.ENVIRONMENT.lower() != "production" and self._is_local_user(user_id):
                chunk_dicts = [c.model_dump() for c in chunks]
                try:
                    store = get_sqlite_store()
                    store.save_document_chunks(project_id, chunk_dicts)
                except Exception as exc:
                    logger.warning("SQLite save_document_chunks failed: %s", exc)

                self._demo_chunks[project_id] = chunk_dicts
                dur = time.perf_counter() - t_start
                logger.info("[PERF-PERSIST] save_document_chunks: persisted %d chunks in local durable store (%.3fs)", len(chunks), dur)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=project_id,
                    affected_count=len(chunks),
                    details=f"Persisted {len(chunks)} document chunks in local durable store.",
                )
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_document_chunks: Supabase unconfigured (%.3fs)", dur)
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase credentials not configured in environment.",
            )

        try:
            def _do_save():
                client.table("document_chunks").delete().eq("project_id", project_id).execute()
                records = []
                for chk in chunks:
                    records.append({
                        "project_id": project_id,
                        "chunk_index": chk.chunk_index,
                        "section": chk.section,
                        "page_number": chk.page_number,
                        "source_reference": chk.source_reference,
                        "text": chk.text,
                        "start_character": chk.start_character,
                        "end_character": chk.end_character,
                        "token_estimate": chk.token_estimate,
                        "embedding_status": "synced" if getattr(chk, "embedding_synced", False) else "pending",
                    })

                if records:
                    res = client.table("document_chunks").insert(records).execute()
                    return len(res.data) if res.data else len(records)
                return 0

            affected = await self._run_bounded(_do_save)
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_document_chunks: persisted %d chunks to Supabase (%.3fs)", affected, dur)
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=project_id,
                affected_count=affected,
                details=f"Persisted {affected} document chunks.",
            )
        except (asyncio.TimeoutError, TimeoutError):
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_document_chunks: Supabase timed out after %.3fs. Falling back cleanly.", dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_chunks[project_id] = [c.model_dump() for c in chunks]
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=len(chunks),
                    details=f"Supabase timed out; saved {len(chunks)} chunks in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error="Supabase persistence timed out.",
            )
        except Exception as e:
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_document_chunks: Supabase error: %s (%.3fs). Falling back cleanly.", type(e).__name__, dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_chunks[project_id] = [c.model_dump() for c in chunks]
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=len(chunks),
                    details=f"Supabase failed; saved {len(chunks)} chunks in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    async def get_document_chunks(
        self,
        project_id: str,
        user_id: str,
        user_token: Optional[str] = None,
    ) -> List[DocumentChunkRecord]:
        """Retrieves all document chunks for a project ordered by chunk_index."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_chunks = store.get_document_chunks(project_id)
                if db_chunks:
                    return [DocumentChunkRecord(**c) for c in db_chunks]
            except Exception as exc:
                logger.warning("SQLite get_document_chunks failed: %s", exc)

            if project_id in self._demo_chunks:
                return [
                    DocumentChunkRecord(
                        project_id=project_id,
                        chunk_index=i,
                        section=c.get("section", "unknown"),
                        page_number=c.get("page_number"),
                        source_reference=c.get("source_reference"),
                        text=c.get("text", ""),
                        start_character=c.get("start_character", 0),
                        end_character=c.get("end_character", len(c.get("text", ""))),
                        token_estimate=c.get("token_estimate", 0),
                    )
                    for i, c in enumerate(self._demo_chunks[project_id])
                ]
            return []

        try:
            def _do_get():
                res = (
                    client.table("document_chunks")
                    .select("*")
                    .eq("project_id", project_id)
                    .order("chunk_index", desc=False)
                    .execute()
                )
                return [DocumentChunkRecord(**row) for row in (res.data or [])]
            return await self._run_bounded(_do_get)
        except Exception as e:
            logger.warning("Get document chunks failed: %s", type(e).__name__)
            if project_id in self._demo_chunks:
                return [
                    DocumentChunkRecord(
                        project_id=project_id,
                        chunk_index=i,
                        section=c.get("section", "unknown"),
                        page_number=c.get("page_number"),
                        source_reference=c.get("source_reference"),
                        text=c.get("text", ""),
                        start_character=c.get("start_character", 0),
                        end_character=c.get("end_character", len(c.get("text", ""))),
                        token_estimate=c.get("token_estimate", 0),
                    )
                    for i, c in enumerate(self._demo_chunks[project_id])
                ]
            return []

    # =========================================================================
    # 3. Technical Feature Persistence
    # =========================================================================

    async def save_features(
        self,
        project_id: str,
        features: List[TechnicalFeature],
        user_id: str,
        user_token: Optional[str] = None,
    ) -> PersistenceStatus:
        """Persists Step 7 extracted technical features idempotently."""
        t_start = time.perf_counter()
        client = self._get_client(user_token)
        if client is None:
            if settings.ENVIRONMENT.lower() != "production" and self._is_local_user(user_id):
                feat_dicts = [f.model_dump() for f in features]
                try:
                    store = get_sqlite_store()
                    store.save_features(project_id, feat_dicts)
                except Exception as exc:
                    logger.warning("SQLite save_features failed: %s", exc)

                self._demo_features[project_id] = feat_dicts
                dur = time.perf_counter() - t_start
                logger.info("[PERF-PERSIST] save_features: persisted %d features in local durable store (%.3fs)", len(features), dur)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=project_id,
                    affected_count=len(features),
                    details=f"Persisted {len(features)} technical features in local durable store.",
                )
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_features: Supabase unconfigured (%.3fs)", dur)
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase credentials not configured in environment.",
            )

        try:
            def _do_save():
                rows = []
                for feat in features:
                    importance = "medium"
                    if feat.confidence >= 0.90:
                        importance = "high"
                    elif feat.confidence < 0.65:
                        importance = "low"

                    source_span = feat.feature_text
                    if feat.supporting_sources:
                        s = feat.supporting_sources[0]
                        source_span = f"[{s.section} p.{s.page_number or '?'}] {feat.feature_text}"

                    rows.append({
                        "project_id": project_id,
                        "feature_id": feat.feature_id,
                        "title": feat.feature_text[:120],
                        "description": feat.feature_text,
                        "technical_category": feat.feature_type.value if hasattr(feat.feature_type, "value") else str(feat.feature_type),
                        "importance": importance,
                        "source_text_span": source_span,
                        "extraction_confidence": float(feat.confidence),
                    })

                if rows:
                    res = client.table("features").upsert(rows, on_conflict="project_id,feature_id").execute()
                    return len(res.data) if res.data else len(rows)
                return 0

            count = await self._run_bounded(_do_save)
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_features: persisted %d features to Supabase (%.3fs)", count, dur)
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=project_id,
                affected_count=count,
                details=f"Persisted {count} technical features.",
            )
        except (asyncio.TimeoutError, TimeoutError):
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_features: Supabase timed out after %.3fs. Falling back cleanly.", dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_features[project_id] = [f.model_dump() for f in features]
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=len(features),
                    details=f"Supabase timed out; saved {len(features)} features in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error="Supabase persistence timed out.",
            )
        except Exception as e:
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_features: Supabase error: %s (%.3fs). Falling back cleanly.", type(e).__name__, dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_features[project_id] = [f.model_dump() for f in features]
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=len(features),
                    details=f"Supabase failed; saved {len(features)} features in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    async def get_features(
        self,
        project_id: str,
        user_id: str,
        user_token: Optional[str] = None,
    ) -> List[FeatureRecord]:
        """Retrieves technical features for a project."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_features = store.get_features(project_id)
                if db_features:
                    return [FeatureRecord(**f) for f in db_features]
            except Exception as exc:
                logger.warning("SQLite get_features failed: %s", exc)

            if project_id in self._demo_features:
                return [
                    FeatureRecord(
                        project_id=project_id,
                        feature_id=f.get("feature_id", "f-0"),
                        title=f.get("feature_text", "")[:120],
                        description=f.get("feature_text", ""),
                        technical_category=str(f.get("feature_type", "structural")),
                        importance="medium",
                        source_text_span=f.get("feature_text", ""),
                        extraction_confidence=float(f.get("confidence", 1.0)),
                    )
                    for f in self._demo_features[project_id]
                ]
            return []

        try:
            def _do_get():
                res = (
                    client.table("features")
                    .select("*")
                    .eq("project_id", project_id)
                    .order("created_at", desc=False)
                    .execute()
                )
                return [FeatureRecord(**row) for row in (res.data or [])]
            return await self._run_bounded(_do_get)
        except Exception as e:
            logger.warning("Get features failed: %s", type(e).__name__)
            if project_id in self._demo_features:
                return [
                    FeatureRecord(
                        project_id=project_id,
                        feature_id=f.get("feature_id", "f-0"),
                        title=f.get("feature_text", "")[:120],
                        description=f.get("feature_text", ""),
                        technical_category=str(f.get("feature_type", "structural")),
                        importance="medium",
                        source_text_span=f.get("feature_text", ""),
                        extraction_confidence=float(f.get("confidence", 1.0)),
                    )
                    for f in self._demo_features[project_id]
                ]
            return []

    # =========================================================================
    # 4. Evidence Items Persistence
    # =========================================================================

    async def save_evidence_items(
        self,
        project_id: str,
        mappings: List[FeatureEvidenceMapping],
        user_id: str,
        user_token: Optional[str] = None,
    ) -> PersistenceStatus:
        """Persists Step 8 feature-to-prior-art evidence mappings."""
        t_start = time.perf_counter()
        client = self._get_client(user_token)
        if client is None:
            if settings.ENVIRONMENT.lower() != "production" and self._is_local_user(user_id):
                ev_dicts = [m.model_dump() for m in mappings]
                try:
                    store = get_sqlite_store()
                    store.save_evidence_items(project_id, ev_dicts)
                except Exception as exc:
                    logger.warning("SQLite save_evidence_items failed: %s", exc)

                self._demo_evidence[project_id] = ev_dicts
                dur = time.perf_counter() - t_start
                logger.info("[PERF-PERSIST] save_evidence_items: persisted %d mappings in local durable store (%.3fs)", len(mappings), dur)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=project_id,
                    affected_count=len(mappings),
                    details=f"Persisted {len(mappings)} evidence items in local durable store.",
                )
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_evidence_items: Supabase unconfigured (%.3fs)", dur)
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase credentials not configured in environment.",
            )

        try:
            def _do_save():
                client.table("evidence_items").delete().eq("project_id", project_id).execute()

                rows = []
                for m in mappings:
                    rel = m.evidence_relationship.value if hasattr(m.evidence_relationship, "value") else str(m.evidence_relationship)
                    p_id = m.patent_id or str(uuid.uuid5(uuid.NAMESPACE_DNS, m.patent_number))
                    f_id = getattr(m, "feature_db_id", None) or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{project_id}_{m.feature_id}"))

                    rows.append({
                        "project_id": project_id,
                        "feature_id": f_id,
                        "patent_id": p_id,
                        "chunk_text": m.evidence_text,
                        "retrieved_source": m.patent_number,
                        "retrieval_method": "hybrid_rrf",
                        "retrieval_similarity": float(m.semantic_similarity),
                        "reranker_score": float(m.reranker_score) if m.reranker_score is not None else None,
                        "rank": m.reranker_rank,
                        "section": m.section,
                        "claim_number": m.claim_number,
                        "page_number": m.page_number,
                        "evidence_strength": float(m.matching_score),
                        "confidence": float(m.mapping_confidence),
                        "evidence_relationship": rel,
                    })

                if rows:
                    res = client.table("evidence_items").insert(rows).execute()
                    return len(res.data) if res.data else len(rows)
                return 0

            count = await self._run_bounded(_do_save)
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_evidence_items: persisted %d items to Supabase (%.3fs)", count, dur)
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=project_id,
                affected_count=count,
                details=f"Persisted {count} evidence items.",
            )
        except (asyncio.TimeoutError, TimeoutError):
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_evidence_items: Supabase timed out after %.3fs. Falling back cleanly.", dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_evidence[project_id] = [m.model_dump() for m in mappings]
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=len(mappings),
                    details=f"Supabase timed out; saved {len(mappings)} evidence items in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error="Supabase persistence timed out.",
            )
        except Exception as e:
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_evidence_items: Supabase error: %s (%.3fs). Falling back cleanly.", type(e).__name__, dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_evidence[project_id] = [m.model_dump() for m in mappings]
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=len(mappings),
                    details=f"Supabase failed; saved {len(mappings)} evidence items in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    async def get_evidence_items(
        self,
        project_id: str,
        user_id: str,
        user_token: Optional[str] = None,
    ) -> List[EvidenceItemRecord]:
        """Retrieves evidence items for a project."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_ev = store.get_evidence_items(project_id)
                if db_ev:
                    return [EvidenceItemRecord(**e) for e in db_ev]
            except Exception as exc:
                logger.warning("SQLite get_evidence_items failed: %s", exc)

            if project_id in self._demo_evidence:
                return [
                    EvidenceItemRecord(
                        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{project_id}_{m.get('feature_id')}_{m.get('patent_number')}")),
                        project_id=project_id,
                        feature_id=m.get("feature_id", "f-0"),
                        patent_id=m.get("patent_id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, m.get("patent_number", "unknown"))),
                        chunk_text=m.get("evidence_text", ""),
                        retrieved_source=m.get("patent_number", ""),
                        retrieval_method="hybrid_rrf",
                        retrieval_similarity=float(m.get("semantic_similarity", 0.0)),
                        evidence_strength=float(m.get("matching_score", 0.0)),
                        confidence=float(m.get("mapping_confidence", 0.0)),
                        evidence_relationship=m.get("evidence_relationship", "contextual_match"),
                        created_at=datetime.now(timezone.utc),
                    )
                    for m in self._demo_evidence[project_id]
                ]
            return []


        try:
            def _do_get():
                res = (
                    client.table("evidence_items")
                    .select("*")
                    .eq("project_id", project_id)
                    .execute()
                )
                return [EvidenceItemRecord(**row) for row in (res.data or [])]
            return await self._run_bounded(_do_get)
        except Exception as e:
            logger.warning("Get evidence items failed: %s", type(e).__name__)
            if project_id in self._demo_evidence:
                return [
                    EvidenceItemRecord(
                        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{project_id}_{m.get('feature_id')}_{m.get('patent_number')}")),
                        project_id=project_id,
                        feature_id=m.get("feature_id", "f-0"),
                        patent_id=m.get("patent_id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, m.get("patent_number", "unknown"))),
                        chunk_text=m.get("evidence_text", ""),
                        retrieved_source=m.get("patent_number", ""),
                        retrieval_method="hybrid_rrf",
                        evidence_strength=float(m.get("matching_score", 0.0)),
                        confidence=float(m.get("mapping_confidence", 0.0)),
                        evidence_relationship=m.get("evidence_relationship", "contextual_match"),
                        created_at=datetime.now(timezone.utc),
                    )
                    for m in self._demo_evidence[project_id]
                ]
            return []

    # =========================================================================
    # 5. EB-PRE Analysis Persistence
    # =========================================================================

    async def save_analysis(
        self,
        project_id: str,
        assessment: ReadinessAssessmentResponse,
        explanation: Optional[GroundedExplanation] = None,
        report_meta: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        user_token: Optional[str] = None,
    ) -> PersistenceStatus:
        """Persists Step 9 EB-PRE assessment metrics with exact score preservation."""
        t_start = time.perf_counter()
        client = self._get_client(user_token)
        if client is None:
            if settings.ENVIRONMENT.lower() != "production" and self._is_local_user(user_id):
                dim_scores = assessment.dimension_scores
                meta = report_meta or {}
                recommendations = []
                if explanation and getattr(explanation, "executive_summary", None):
                    recommendations = [f"Focus on technical differentiation for early stage {assessment.readiness_category.value}"]

                rec_id = str(uuid.uuid4())
                row = {
                    "id": rec_id,
                    "project_id": project_id,
                    "readiness_score": int(round(assessment.readiness_percentage)),
                    "confidence_score": float(assessment.confidence_score),
                    "readiness_category": assessment.readiness_category.value,
                    "novelty_score": int(round(dim_scores["novelty"].score * 100)),
                    "overlap_score": int(round(dim_scores["prior_art_overlap"].score * 100)),
                    "differentiation_score": int(round(dim_scores["technical_differentiation"].score * 100)),
                    "documentation_score": int(round(dim_scores["documentation_quality"].score * 100)),
                    "innovation_characteristics": dim_scores["innovation_characteristics"].model_dump(),
                    "commercial_potential": dim_scores["commercial_potential"].model_dump(),
                    "explanation": explanation.executive_summary if explanation else "EB-PRE Deterministic Assessment",
                    "recommendations": recommendations,
                    "uncertainty_flags": assessment.uncertainty_flags,
                    "metadata": {
                        "readiness_score_raw": assessment.readiness_score,
                        "category_display": assessment.category_display,
                        "confidence_score": assessment.confidence_score,
                        "flags": assessment.uncertainty_flags,
                    },
                    "model_used": meta.get("model", settings.GEMINI_EXPLANATION_MODEL),
                    "processing_time": int(meta.get("generation_latency_ms", 0)),
                    "retrieved_chunk_count": len(assessment.evidence_matrix.cells) if assessment.evidence_matrix else 0,
                    "retrieved_patents": list({cell.patent_number for cell in (assessment.evidence_matrix.cells if assessment.evidence_matrix else [])}),
                    "status": "completed",
                    "created_at": datetime.now(timezone.utc),
                }
                try:
                    store = get_sqlite_store()
                    store.save_analysis(project_id, row)
                except Exception as exc:
                    logger.warning("SQLite save_analysis failed: %s", exc)

                self._demo_analyses[project_id] = row
                dur = time.perf_counter() - t_start
                logger.info("[PERF-PERSIST] save_analysis: persisted analysis in local durable store (%.3fs)", dur)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=rec_id,
                    affected_count=1,
                    details="EB-PRE readiness analysis persisted in local durable store.",
                )
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_analysis: Supabase unconfigured (%.3fs)", dur)
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase credentials not configured in environment.",
            )

        try:
            dim_scores = assessment.dimension_scores
            meta = report_meta or {}
            recommendations = []
            if explanation and getattr(explanation, "executive_summary", None):
                recommendations = [f"Focus on technical differentiation for early stage {assessment.readiness_category.value}"]

            row = {
                "project_id": project_id,
                "readiness_score": int(round(assessment.readiness_percentage)),
                "confidence_score": float(assessment.confidence_score),
                "readiness_category": assessment.readiness_category.value,
                "novelty_score": int(round(dim_scores["novelty"].score * 100)),
                "overlap_score": int(round(dim_scores["prior_art_overlap"].score * 100)),
                "differentiation_score": int(round(dim_scores["technical_differentiation"].score * 100)),
                "documentation_score": int(round(dim_scores["documentation_quality"].score * 100)),
                "innovation_characteristics": dim_scores["innovation_characteristics"].model_dump(),
                "commercial_potential": dim_scores["commercial_potential"].model_dump(),
                "explanation": explanation.executive_summary if explanation else "EB-PRE Deterministic Assessment",
                "recommendations": recommendations,
                "uncertainty_flags": assessment.uncertainty_flags,
                "metadata": {
                    "readiness_score_raw": assessment.readiness_score,
                    "category_display": assessment.category_display,
                    "confidence_score": assessment.confidence_score,
                    "flags": assessment.uncertainty_flags,
                },
                "model_used": meta.get("model", settings.GEMINI_EXPLANATION_MODEL),
                "processing_time": int(meta.get("generation_latency_ms", 0)),
                "retrieved_chunk_count": len(assessment.evidence_matrix.cells) if assessment.evidence_matrix else 0,
                "retrieved_patents": list({cell.patent_number for cell in (assessment.evidence_matrix.cells if assessment.evidence_matrix else [])}),
                "status": "completed",
            }

            def _do_save():
                client.table("analyses").delete().eq("project_id", project_id).execute()
                res = client.table("analyses").insert(row).execute()
                return res.data[0]["id"] if res.data else project_id

            rec_id = await self._run_bounded(_do_save)
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_analysis: persisted analysis to Supabase (%.3fs)", dur)
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=rec_id,
                affected_count=1,
                details="EB-PRE readiness analysis persisted with exact numerical integrity.",
            )
        except (asyncio.TimeoutError, TimeoutError):
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_analysis: Supabase timed out after %.3fs. Falling back cleanly.", dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_analyses[project_id] = row
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=1,
                    details="Supabase timed out; saved analysis in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error="Supabase persistence timed out.",
            )
        except Exception as e:
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_analysis: Supabase error: %s (%.3fs). Falling back cleanly.", type(e).__name__, dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_analyses[project_id] = row
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=1,
                    details="Supabase failed; saved analysis in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    async def get_analysis(
        self,
        project_id: str,
        user_id: str,
        user_token: Optional[str] = None,
    ) -> Optional[AnalysisRecord]:
        """Retrieves the analysis record for a project."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_ana = store.get_analysis(project_id)
                if db_ana:
                    return AnalysisRecord(**db_ana)
            except Exception as exc:
                logger.warning("SQLite get_analysis failed: %s", exc)

            if project_id in self._demo_analyses:
                return AnalysisRecord(**self._demo_analyses[project_id])
            return None

        try:
            def _do_get():
                res = (
                    client.table("analyses")
                    .select("*")
                    .eq("project_id", project_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if res.data:
                    return AnalysisRecord(**res.data[0])
                return None
            return await self._run_bounded(_do_get)
        except Exception as e:
            logger.warning("Get analysis failed: %s", type(e).__name__)
            if project_id in self._demo_analyses:
                return AnalysisRecord(**self._demo_analyses[project_id])
            return None

    # =========================================================================
    # 6. Report Persistence
    # =========================================================================

    async def save_report(
        self,
        project_id: str,
        report_data: EvidenceBasedReport,
        report_type: str = "json",
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = "",
        user_token: Optional[str] = None,
    ) -> PersistenceStatus:
        """Persists Step 10 structured evidence-based report."""
        t_start = time.perf_counter()
        client = self._get_client(user_token)
        if client is None:
            if settings.ENVIRONMENT.lower() != "production" and self._is_local_user(user_id):
                rec_id = str(uuid.uuid4())
                combined_metadata = {
                    "report": report_data.model_dump(),
                    **(metadata or {}),
                }
                row = {
                    "id": rec_id,
                    "project_id": project_id,
                    "type": report_type,
                    "file_path": f"projects/{project_id}/reports/report_{report_type}.json",
                    "metadata": combined_metadata,
                    "created_at": datetime.now(timezone.utc),
                }
                try:
                    store = get_sqlite_store()
                    store.save_report(project_id, report_type, row)
                except Exception as exc:
                    logger.warning("SQLite save_report failed: %s", exc)

                self._demo_reports[project_id] = row
                dur = time.perf_counter() - t_start
                logger.info("[PERF-PERSIST] save_report: persisted report in local durable store (%.3fs)", dur)
                return PersistenceStatus(
                    success=True,
                    status="persisted",
                    record_id=rec_id,
                    affected_count=1,
                    details="Structured 10-section report persisted in local durable store.",
                )
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_report: Supabase unconfigured (%.3fs)", dur)
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase credentials not configured in environment.",
            )

        try:
            combined_metadata = {
                "report": report_data.model_dump(),
                **(metadata or {}),
            }
            row = {
                "project_id": project_id,
                "type": report_type,
                "file_path": f"projects/{project_id}/reports/report_{report_type}.json",
                "metadata": combined_metadata,
            }

            def _do_save():
                client.table("reports").delete().eq("project_id", project_id).eq("type", report_type).execute()
                res = client.table("reports").insert(row).execute()
                return res.data[0]["id"] if res.data else project_id

            rec_id = await self._run_bounded(_do_save)
            dur = time.perf_counter() - t_start
            logger.info("[PERF-PERSIST] save_report: persisted report to Supabase (%.3fs)", dur)
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=rec_id,
                affected_count=1,
                details="Structured 10-section report persisted successfully.",
            )
        except (asyncio.TimeoutError, TimeoutError):
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_report: Supabase timed out after %.3fs. Falling back cleanly.", dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_reports[project_id] = row
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=1,
                    details="Supabase timed out; saved report in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error="Supabase persistence timed out.",
            )
        except Exception as e:
            dur = time.perf_counter() - t_start
            logger.warning("[PERF-PERSIST] save_report: Supabase error: %s (%.3fs). Falling back cleanly.", type(e).__name__, dur)
            if settings.ENVIRONMENT.lower() != "production" and user_id == settings.DEMO_USER_ID:
                self._demo_reports[project_id] = row
                return PersistenceStatus(
                    success=True,
                    status="persisted_demo_fallback",
                    record_id=project_id,
                    affected_count=1,
                    details="Supabase failed; saved report in demo store.",
                )
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )


    async def get_report(
        self,
        project_id: str,
        user_id: str,
        report_type: str = "json",
        user_token: Optional[str] = None,
    ) -> Optional[ReportRecord]:
        """Retrieves a report record for a project."""
        client = self._get_client(user_token)
        if client is None:
            try:
                store = get_sqlite_store()
                db_rep = store.get_report(project_id, report_type)
                if db_rep:
                    return ReportRecord(**db_rep)
            except Exception as exc:
                logger.warning("SQLite get_report failed: %s", exc)

            if project_id in self._demo_reports:
                return ReportRecord(**self._demo_reports[project_id])
            return None

        try:
            res = (
                client.table("reports")
                .select("*")
                .eq("project_id", project_id)
                .eq("type", report_type)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if res.data:
                return ReportRecord(**res.data[0])
            return None
        except Exception as e:
            logger.warning("Get report failed: %s", type(e).__name__)
            return None

    # =========================================================================
    # 7. Global Patent Corpus Operations (Admin / Service Role Protected)
    # =========================================================================

    async def save_patent_document(
        self,
        patent_data: Dict[str, Any],
    ) -> PersistenceStatus:
        """Persists a global patent document into public.patent_documents.

        STRICTLY requires service role client. Normal users cannot write to corpus.
        """
        client = self._get_admin_client()
        if client is None:
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase service role credentials not configured in environment.",
            )

        try:
            res = client.table("patent_documents").upsert(patent_data, on_conflict="patent_number").execute()
            rec_id = res.data[0]["id"] if res.data else None
            return PersistenceStatus(
                success=True,
                status="persisted",
                record_id=rec_id,
                affected_count=1,
                details=f"Patent {patent_data.get('patent_number')} persisted to global corpus.",
            )
        except Exception as e:
            logger.warning("Patent document persistence failed: %s", type(e).__name__)
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    async def save_patent_chunks(
        self,
        patent_id: str,
        chunks: List[Dict[str, Any]],
    ) -> PersistenceStatus:
        """Persists global patent chunks into public.patent_chunks.

        STRICTLY requires service role client.
        """
        client = self._get_admin_client()
        if client is None:
            return PersistenceStatus(
                success=False,
                status="unconfigured",
                details="Supabase service role credentials not configured in environment.",
            )

        try:
            if not chunks:
                return PersistenceStatus(success=True, status="persisted", affected_count=0)

            res = client.table("patent_chunks").insert(chunks).execute()
            count = len(res.data) if res.data else len(chunks)
            return PersistenceStatus(
                success=True,
                status="persisted",
                affected_count=count,
                details=f"Persisted {count} chunks for patent {patent_id}.",
            )
        except Exception as e:
            logger.warning("Patent chunks persistence failed: %s", type(e).__name__)
            return PersistenceStatus(
                success=False,
                status="failed",
                error=f"Persistence error: {type(e).__name__}",
            )

    async def get_patent_document(self, patent_number: str) -> Optional[Dict[str, Any]]:
        """Reads a patent document from the global corpus. Open to all users."""
        client = self._get_client() or self._get_admin_client()
        if client is None:
            return None

        try:
            res = (
                client.table("patent_documents")
                .select("*")
                .eq("patent_number", patent_number)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.warning("Get patent document failed: %s", type(e).__name__)
            return None

    async def get_patent_chunks(self, patent_id: str) -> List[Dict[str, Any]]:
        """Reads patent chunks from the global corpus. Open to all users."""
        client = self._get_client() or self._get_admin_client()
        if client is None:
            return []

        try:
            res = (
                client.table("patent_chunks")
                .select("*")
                .eq("patent_id", patent_id)
                .order("chunk_index", desc=False)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.warning("Get patent chunks failed: %s", type(e).__name__)
            return []


repository = SupabaseRepository()
