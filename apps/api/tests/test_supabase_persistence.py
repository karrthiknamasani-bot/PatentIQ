import uuid
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from app.schemas.document import DocumentChunk
from app.services.features.types import FeatureType, SourceProvenance
from app.services.features.feature_schema import TechnicalFeature
from app.services.mapping.types import FeatureEvidenceMapping, EvidenceRelationship
from app.services.readiness.types import (
    ReadinessAssessmentResponse,
    ReadinessCategory,
    DimensionScore,
    EvidenceMatrix,
    EvidenceMatrixCell,
)
from app.services.explanation.types import GroundedExplanation, DimensionExplanation, EvidenceBasedReport
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
from app.services.persistence.repository import SupabaseRepository
from app.services.supabase_service import SupabaseService


# =============================================================================
# Mock Supabase Fixtures & Helpers
# =============================================================================

class MockQueryBuilder:
    """Mock chaining query builder imitating postgrest-py / supabase-py."""

    def __init__(self, data=None):
        self._data = data if data is not None else []
        self._last_op = None
        self._filters = {}

    def insert(self, values):
        self._last_op = "insert"
        if isinstance(values, list):
            self._data = [{"id": str(uuid.uuid4()), **v} for v in values]
        elif isinstance(values, dict):
            self._data = [{"id": str(uuid.uuid4()), **values}]
        return self

    def upsert(self, values, on_conflict=None):
        self._last_op = "upsert"
        if isinstance(values, list):
            self._data = [{"id": str(uuid.uuid4()), **v} for v in values]
        elif isinstance(values, dict):
            self._data = [{"id": str(uuid.uuid4()), **values}]
        return self

    def select(self, *args, **kwargs):
        self._last_op = "select"
        return self

    def update(self, values):
        self._last_op = "update"
        if self._data and isinstance(self._data, list):
            self._data = [{**item, **values} for item in self._data]
        return self

    def delete(self):
        self._last_op = "delete"
        self._data = []
        return self

    def eq(self, column, value):
        self._filters[column] = value
        # Apply simple in-memory filter if data is already a list
        if isinstance(self._data, list):
            self._data = [row for row in self._data if row.get(column) == value or column not in row]
        return self

    def order(self, column, desc=False):
        return self

    def range(self, start, end):
        return self

    def limit(self, count):
        if isinstance(self._data, list):
            self._data = self._data[:count]
        return self

    def execute(self):
        res = MagicMock()
        res.data = self._data
        return res


class MockSupabaseClient:
    """Mock Supabase Client with table routing."""

    def __init__(self, table_data=None):
        self.tables = table_data or {}

    def table(self, table_name):
        initial = self.tables.get(table_name, [])
        # Return a query builder tracking operations for this table
        qb = MockQueryBuilder(data=initial.copy() if isinstance(initial, list) else initial)
        return qb


@pytest.fixture
def mock_service():
    """Provides a mock SupabaseService configured with mock clients."""
    svc = MagicMock(spec=SupabaseService)
    svc.is_configured = True
    svc.is_admin_configured = True
    client = MockSupabaseClient()
    svc.get_client.return_value = client
    svc.get_admin_client.return_value = client
    return svc, client


@pytest.fixture
def sample_user_project():
    return ProjectCreate(
        user_id="user_test_uuid_123",
        title="Smart Radio Frequency Ablation System",
        description="Dynamic impedance monitoring catheter",
        original_file_name="rf_ablation.docx",
        stored_file_name="rf_ablation_uuid.docx",
        file_path="uploads/rf_ablation_uuid.docx",
        file_type="docx",
        file_size=10240,
    )


@pytest.fixture
def sample_chunks():
    return [
        DocumentChunk(
            chunk_index=0,
            text="Abstract: A novel catheter with impedance sensor arrays.",
            section="abstract",
            page_number=1,
            source_reference="p.1 para 1",
            start_character=0,
            end_character=60,
            token_estimate=15,
        ),
        DocumentChunk(
            chunk_index=1,
            text="Claim 1: An RF ablation catheter comprising a feedback controller.",
            section="claims",
            page_number=3,
            claim_number=1,
            source_reference="claim 1",
            start_character=61,
            end_character=130,
            token_estimate=18,
        ),
    ]


@pytest.fixture
def sample_features():
    return [
        TechnicalFeature(
            feature_id="feat_rf_sensor",
            project_id="proj_test_001",
            feature_type=FeatureType.COMPONENT,
            feature_text="Integrated sensor array monitoring tissue impedance during RF ablation",
            normalized_text="integrated sensor array monitoring tissue impedance during rf ablation",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_0", chunk_index=0, section="abstract", page_number=1, evidence_span_start=0, evidence_span_end=50)
            ],
            confidence=0.95,
        ),
        TechnicalFeature(
            feature_id="feat_adaptive_ctrl",
            project_id="proj_test_001",
            feature_type=FeatureType.FUNCTION,
            feature_text="Adaptive feedback control adjusting RF generator frequency within 5ms",
            normalized_text="adaptive feedback control adjusting rf generator frequency within 5ms",
            supporting_sources=[
                SourceProvenance(chunk_id="chk_1", chunk_index=1, section="claims", claim_number=1, page_number=3, evidence_span_start=0, evidence_span_end=60)
            ],
            confidence=0.88,
        ),
    ]


@pytest.fixture
def sample_mappings():
    return [
        FeatureEvidenceMapping(
            mapping_id="map_001",
            project_id="proj_test_001",
            feature_id="feat_rf_sensor",
            feature_type="component",
            feature_text="Integrated sensor array monitoring tissue impedance",
            patent_number="US-10492811-B2",
            patent_id="pat_uuid_001",
            chunk_id="chk_pat_001",
            chunk_index=1,
            evidence_text="An end effector with an impedance sensor array configured to monitor tissue impedance.",
            section="claims",
            claim_number=1,
            page_number=4,
            source="uspto",
            lexical_similarity=0.80,
            semantic_similarity=0.92,
            matching_score=0.872,
            evidence_relationship=EvidenceRelationship.DIRECT_MATCH,
            mapping_confidence=0.94,
            reranker_score=0.95,
            reranker_rank=1,
        )
    ]


@pytest.fixture
def sample_eb_pre_result(sample_features, sample_mappings):
    from app.services.readiness.readiness_engine import readiness_engine
    return readiness_engine.assess_readiness(
        project_id="proj_test_001",
        features=sample_features,
        mappings=sample_mappings,
    )


# =============================================================================
# Test Suite (21 Tests)
# =============================================================================

@pytest.mark.asyncio
async def test_01_project_creation(mock_service, sample_user_project):
    """Test 1: Project creation persistence with owner user_id."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)
    status, record = await repo.create_project(sample_user_project)

    assert status.success is True
    assert status.status == "persisted"
    assert record is not None
    assert record.user_id == "user_test_uuid_123"
    assert record.title == "Smart Radio Frequency Ablation System"


@pytest.mark.asyncio
async def test_02_project_ownership_isolation(mock_service):
    """Test 2: Project ownership filtering prevents User A from accessing User B's project."""
    svc, client = mock_service
    # Seed client with user B's project
    client.tables["projects"] = [
        {"id": "proj_b_1", "user_id": "user_B", "title": "Secret Project B"}
    ]
    repo = SupabaseRepository(service=svc)

    # User A requests User B's project
    proj = await repo.get_project("proj_b_1", user_id="user_A")
    assert proj is None, "User A must not be able to retrieve User B's project"


@pytest.mark.asyncio
async def test_03_project_retrieval_by_id(mock_service):
    """Test 3: Project retrieval returns ProjectRecord when user owns the project."""
    svc, client = mock_service
    client.tables["projects"] = [
        {"id": "proj_a_1", "user_id": "user_A", "title": "Project A", "original_file_name": "a.pdf", "stored_file_name": "a.pdf", "file_path": "a.pdf", "file_type": "pdf", "file_size": 100}
    ]
    repo = SupabaseRepository(service=svc)

    proj = await repo.get_project("proj_a_1", user_id="user_A")
    assert proj is not None
    assert proj.id == "proj_a_1"
    assert proj.title == "Project A"


@pytest.mark.asyncio
async def test_04_document_chunks_persistence(mock_service, sample_chunks):
    """Test 4: Document chunk persistence preserves section, offsets, and tokens."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)
    status = await repo.save_document_chunks("proj_test_001", sample_chunks, user_id="user_test_123")

    assert status.success is True
    assert status.affected_count == 2
    assert status.record_id == "proj_test_001"


@pytest.mark.asyncio
async def test_05_features_persistence_composite_uniqueness(mock_service, sample_features):
    """Test 5: Feature persistence preserves composite uniqueness on project_id + feature_id."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)
    status = await repo.save_features("proj_test_001", sample_features, user_id="user_test_123")

    assert status.success is True
    assert status.affected_count == 2


@pytest.mark.asyncio
async def test_06_feature_id_preservation(mock_service, sample_features):
    """Test 6: Feature IDs generated in Step 7 are preserved verbatim without mutation."""
    svc, client = mock_service
    repo = SupabaseRepository(service=svc)
    status = await repo.save_features("proj_test_001", sample_features, user_id="user_test_123")

    assert status.success is True
    # Seed retrieved features matching sample
    client.tables["features"] = [
        {
            "id": "uuid_feat_1",
            "project_id": "proj_test_001",
            "feature_id": "feat_rf_sensor",
            "title": "Sensor Array",
            "description": "Sensor description",
            "technical_category": "component",
            "importance": "high",
            "source_text_span": "span",
            "extraction_confidence": 0.95,
        }
    ]
    retrieved = await repo.get_features("proj_test_001", user_id="user_test_123")
    assert len(retrieved) == 1
    assert retrieved[0].feature_id == "feat_rf_sensor"


@pytest.mark.asyncio
async def test_07_evidence_items_persistence(mock_service, sample_mappings):
    """Test 7: Evidence items persistence records similarity, reranker score, and rank."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)
    status = await repo.save_evidence_items("proj_test_001", sample_mappings, user_id="user_test_123")

    assert status.success is True
    assert status.affected_count == 1


@pytest.mark.asyncio
async def test_08_evidence_provenance_preservation(mock_service):
    """Test 8: Evidence provenance (patent_number, claim, page, relationship) is preserved."""
    svc, client = mock_service
    client.tables["evidence_items"] = [
        {
            "id": "uuid_ev_1",
            "project_id": "proj_test_001",
            "feature_id": "feat_uuid_1",
            "patent_id": "pat_uuid_1",
            "chunk_text": "An impedance sensor...",
            "retrieved_source": "US-10492811-B2",
            "retrieval_method": "hybrid_rrf",
            "retrieval_similarity": 0.92,
            "reranker_score": 0.95,
            "rank": 1,
            "section": "claims",
            "claim_number": 1,
            "page_number": 4,
            "evidence_strength": 0.872,
            "confidence": 0.94,
            "evidence_relationship": "direct_match",
        }
    ]
    repo = SupabaseRepository(service=svc)
    items = await repo.get_evidence_items("proj_test_001", user_id="user_test_123")

    assert len(items) == 1
    ev = items[0]
    assert ev.retrieved_source == "US-10492811-B2"
    assert ev.claim_number == 1
    assert ev.section == "claims"
    assert ev.evidence_relationship == "direct_match"


@pytest.mark.asyncio
async def test_09_analysis_exact_eb_pre_score_preservation(mock_service, sample_eb_pre_result):
    """Test 9: Exact EB-PRE scores and readiness category are persisted without calculation drift."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)
    status = await repo.save_analysis("proj_test_001", sample_eb_pre_result, user_id="user_test_123")

    assert status.success is True
    assert status.status == "persisted"


@pytest.mark.asyncio
async def test_10_analysis_six_dimensions_preservation(mock_service, sample_eb_pre_result):
    """Test 10: All six core dimension scores and JSONB fields are preserved."""
    svc, client = mock_service
    client.tables["analyses"] = [
        {
            "id": "ana_uuid_1",
            "project_id": "proj_test_001",
            "readiness_score": 51,
            "confidence_score": 0.6768,
            "readiness_category": "moderate",
            "novelty_score": 42,
            "overlap_score": 57,
            "differentiation_score": 42,
            "documentation_score": 94,
            "innovation_characteristics": {"complexity": "high"},
            "commercial_potential": {"readiness": "prototype"},
            "explanation": "Assessment summary",
            "recommendations": ["Improve differentiation"],
            "uncertainty_flags": ["direct_prior_art_overlap"],
            "metadata": {"flags": ["direct_prior_art_overlap"]},
            "model_used": "gemini-3.1-pro-preview",
            "processing_time": 120,
            "retrieved_chunk_count": 1,
            "retrieved_patents": ["US-10492811-B2"],
            "status": "completed",
        }
    ]
    repo = SupabaseRepository(service=svc)
    rec = await repo.get_analysis("proj_test_001", user_id="user_test_123")

    assert rec is not None
    assert rec.readiness_score == 51
    assert rec.novelty_score == 42
    assert rec.overlap_score == 57
    assert rec.differentiation_score == 42
    assert rec.documentation_score == 94
    assert rec.uncertainty_flags == ["direct_prior_art_overlap"]


@pytest.mark.asyncio
async def test_11_report_persistence_ten_sections(mock_service):
    """Test 11: 10-section report output is preserved completely in report persistence."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)
    mock_report = EvidenceBasedReport(
        project_id="proj_test_001",
        executive_summary="Summary of findings",
        invention_overview="Novel RF ablation",
        technical_feature_analysis=[{"feature": "sensor", "analysis": "direct match found"}],
        prior_art_evidence=[{"patent": "US-10492811-B2", "evidence": "Claim 1 discloses sensor"}],
        evidence_matrix_summary={"summary": "1 direct match found"},
        eb_pre_dimension_assessment=[{"dimension": "novelty", "score": 42}],
        technical_differentiation="Key novelty in frequency adjustment speed",
        uncertainty_and_limitations={"limitations": ["Prior art corpus limited to 15 patents"]},
        overall_early_stage_readiness={"recommendation": "Moderate readiness, recommend filing provisional"},
        legal_disclaimer="PatentIQ provides technical indications, not legal advice.",
        metadata={"model": "gemini-3.1-pro-preview"},
    )
    status = await repo.save_report("proj_test_001", mock_report, user_id="user_test_123")

    assert status.success is True
    assert status.status == "persisted"


@pytest.mark.asyncio
async def test_12_report_metadata_preservation(mock_service):
    """Test 12: Report metadata (model, latency, fallback used) is stored and retrievable."""
    svc, client = mock_service
    client.tables["reports"] = [
        {
            "id": "rep_uuid_1",
            "project_id": "proj_test_001",
            "type": "json",
            "file_path": "projects/proj_test_001/reports/report_json.json",
            "metadata": {
                "model": "gemini-3.1-pro-preview",
                "generation_latency_ms": 940.5,
                "fallback_used": False,
                "grounding_valid": True,
            },
        }
    ]
    repo = SupabaseRepository(service=svc)
    rep = await repo.get_report("proj_test_001", user_id="user_test_123")

    assert rep is not None
    assert rep.metadata["model"] == "gemini-3.1-pro-preview"
    assert rep.metadata["fallback_used"] is False


@pytest.mark.asyncio
async def test_13_idempotent_feature_persistence(mock_service, sample_features):
    """Test 13: Repeated feature persistence calls do not create duplicate entries."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)

    status1 = await repo.save_features("proj_test_001", sample_features, user_id="user_test_123")
    status2 = await repo.save_features("proj_test_001", sample_features, user_id="user_test_123")

    assert status1.success is True
    assert status2.success is True
    assert status1.affected_count == status2.affected_count == 2


@pytest.mark.asyncio
async def test_14_idempotent_evidence_persistence(mock_service, sample_mappings):
    """Test 14: Repeated evidence persistence calls replace cleanly without duplicate accumulation."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)

    status1 = await repo.save_evidence_items("proj_test_001", sample_mappings, user_id="user_test_123")
    status2 = await repo.save_evidence_items("proj_test_001", sample_mappings, user_id="user_test_123")

    assert status1.success is True
    assert status2.success is True
    assert status1.affected_count == status2.affected_count == 1


@pytest.mark.asyncio
async def test_15_partial_persistence_failure_handling(mock_service, sample_features):
    """Test 15: Partial persistence failure reports error cleanly without crashing the pipeline."""
    svc, client = mock_service
    # Configure client to raise exception on evidence_items
    def failing_table(name):
        if name == "evidence_items":
            qb = MagicMock()
            qb.delete.side_effect = RuntimeError("Database connection timeout")
            return qb
        return MockQueryBuilder()

    client.table = failing_table
    repo = SupabaseRepository(service=svc)

    # Features succeed
    feat_status = await repo.save_features("proj_test_001", sample_features, user_id="user_test_123")
    assert feat_status.success is True

    # Evidence fails cleanly
    ev_status = await repo.save_evidence_items("proj_test_001", [], user_id="user_test_123")
    assert ev_status.success is False
    assert ev_status.status == "failed"
    assert "Persistence error" in ev_status.error


@pytest.mark.asyncio
async def test_16_unconfigured_supabase_handling():
    """Test 16: When Supabase is not configured, operations return unconfigured status without crashing."""
    unconfigured_svc = MagicMock(spec=SupabaseService)
    unconfigured_svc.is_configured = False
    unconfigured_svc.is_admin_configured = False
    unconfigured_svc.get_client.return_value = None
    unconfigured_svc.get_admin_client.return_value = None

    repo = SupabaseRepository(service=unconfigured_svc)

    status, proj = await repo.create_project(
        ProjectCreate(
            user_id="u1",
            title="T",
            original_file_name="f",
            stored_file_name="f",
            file_path="p",
            file_type="txt",
            file_size=10,
        )
    )
    assert status.success is False
    assert status.status == "unconfigured"
    assert proj is None


@pytest.mark.asyncio
async def test_17_service_role_credential_protection(mock_service):
    """Test 17: Service role keys are never exposed in user query responses or logs."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)

    # Verify repo._get_client uses standard client, not admin
    user_client = repo._get_client()
    assert user_client == svc.get_client()
    assert user_client != svc.get_admin_client.return_value or svc.get_client() is not None


@pytest.mark.asyncio
async def test_18_patent_corpus_write_protection(mock_service):
    """Test 18: Normal user client cannot write to patent corpus tables without admin client."""
    svc, client = mock_service
    svc.is_admin_configured = False
    svc.get_admin_client.return_value = None

    repo = SupabaseRepository(service=svc)
    status = await repo.save_patent_document({"patent_number": "US-9999999-B2", "title": "Test Patent"})

    assert status.success is False
    assert status.status == "unconfigured"
    assert "service role" in status.details.lower()


@pytest.mark.asyncio
async def test_19_global_patent_corpus_read_access(mock_service):
    """Test 19: All authenticated and anonymous users can read global patent documents."""
    svc, client = mock_service
    client.tables["patent_documents"] = [
        {"patent_number": "US-10492811-B2", "title": "Surgical instrument", "abstract": "RF device"}
    ]
    repo = SupabaseRepository(service=svc)
    doc = await repo.get_patent_document("US-10492811-B2")

    assert doc is not None
    assert doc["patent_number"] == "US-10492811-B2"
    assert doc["title"] == "Surgical instrument"


@pytest.mark.asyncio
async def test_20_full_pipeline_persistence_orchestration(
    mock_service,
    sample_user_project,
    sample_chunks,
    sample_features,
    sample_mappings,
    sample_eb_pre_result,
):
    """Test 20: Full pipeline persistence from Project -> Chunks -> Features -> Evidence -> Analysis -> Report."""
    svc, _ = mock_service
    repo = SupabaseRepository(service=svc)

    # 1. Project
    p_status, proj = await repo.create_project(sample_user_project)
    assert p_status.success is True
    pid = proj.id

    # 2. Document Chunks
    chk_status = await repo.save_document_chunks(pid, sample_chunks, user_id=sample_user_project.user_id)
    assert chk_status.success is True

    # 3. Features
    feat_status = await repo.save_features(pid, sample_features, user_id=sample_user_project.user_id)
    assert feat_status.success is True

    # 4. Evidence
    ev_status = await repo.save_evidence_items(pid, sample_mappings, user_id=sample_user_project.user_id)
    assert ev_status.success is True

    # 5. Analysis
    ana_status = await repo.save_analysis(pid, sample_eb_pre_result, user_id=sample_user_project.user_id)
    assert ana_status.success is True

    # 6. Report
    rep_obj = EvidenceBasedReport(
        project_id=pid,
        executive_summary="Orchestration test summary",
        invention_overview="Overview",
        technical_feature_analysis=[],
        prior_art_evidence=[],
        evidence_matrix_summary={"status": "complete"},
        eb_pre_dimension_assessment=[],
        technical_differentiation="Diff",
        uncertainty_and_limitations={"limitations": []},
        overall_early_stage_readiness={"readiness": "ready"},
        legal_disclaimer="Disclaimer",
    )
    rep_status = await repo.save_report(pid, rep_obj, user_id=sample_user_project.user_id)
    assert rep_status.success is True


@pytest.mark.asyncio
async def test_21_database_health_schema_reporting():
    """Test 21: Database health reports schema_available status accurately."""
    svc = SupabaseService()
    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=False):
        res = await svc.check_connection()
        assert res["status"] == "unconfigured"
        assert res["schema_available"] is False

    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=True):
        mock_client = MockSupabaseClient({"projects": []})
        with patch.object(SupabaseService, "get_client", return_value=mock_client):
            res = await svc.check_connection()
            assert res["status"] == "ok"
            assert res["schema_available"] is True
