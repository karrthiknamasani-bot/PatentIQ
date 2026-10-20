import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

DEMO_HEADERS = {
    "Authorization": f"Bearer {settings.DEMO_BEARER_TOKEN}"
}


def test_e2e_complete_lifecycle():
    """End-to-End smoke test executing full application pipeline:

    1. Health check
    2. List projects
    3. Create project workspace
    4. Execute full 18-step pipeline (/api/pipeline/analyze)
    5. Retrieve project details with persisted report and analysis
    6. Execute direct prior-art corpus search (/api/retrieval/search)
    7. Delete project workspace
    """
    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"

    # 2. List projects
    res = client.get("/api/projects", headers=DEMO_HEADERS)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 3. Create project workspace
    create_payload = {
        "title": "E2E Quantum Error Correction Assessment",
        "description": "Fault-tolerant quantum computing surface code architecture.",
        "domain": "Quantum Computing",
        "original_file_name": "quantum_spec.txt",
        "file_type": "txt",
        "file_size": 1024,
    }
    res = client.post("/api/projects", json=create_payload, headers=DEMO_HEADERS)
    assert res.status_code == 201
    created_proj = res.json()
    assert created_proj["id"] is not None
    assert created_proj["title"] == "E2E Quantum Error Correction Assessment"

    # 4. Execute Full 18-Step Pipeline
    sample_spec = (
        "TITLE: FAULT-TOLERANT QUANTUM SURFACE CODE ACCELERATOR\n\n"
        "FIELD OF THE INVENTION:\n"
        "This invention relates to quantum computing hardware, specifically distributed syndrome measurement.\n\n"
        "TECHNICAL CLAIMS:\n"
        "1. A fault-tolerant quantum processor comprising a 2D planar lattice of superconducting transmon qubits.\n"
        "2. The quantum processor of claim 1 wherein syndrome decoding is performed in sub-microsecond latency using an FPGA neural network.\n"
        "3. The quantum processor of claim 1 wherein stabilizer measurement operators commute across adjacent plaquettes.\n"
    )

    file_bytes = io.BytesIO(sample_spec.encode("utf-8"))
    files = {
        "file": ("quantum_spec.txt", file_bytes, "text/plain"),
    }
    form_data = {
        "title": "E2E Quantum Invention",
        "description": "Full end-to-end pipeline test invention disclosure.",
    }

    res = client.post(
        "/api/pipeline/analyze",
        data=form_data,
        files=files,
        headers=DEMO_HEADERS,
    )
    assert res.status_code == 200, f"Pipeline execution failed: {res.text}"
    p_data = res.json()

    # Verify pipeline response integrity
    project_id = p_data["project_id"]
    assert project_id is not None
    assert p_data["chunk_count"] > 0
    assert p_data["feature_count"] > 0
    assert p_data["readiness_score"] >= 0
    assert p_data["readiness_percentage"] >= 0.0
    assert p_data["readiness_category"] in [
        "low",
        "moderate",
        "high",
    ]
    assert len(p_data["dimension_scores"]) == 6
    assert "novelty" in p_data["dimension_scores"]
    assert "technical_differentiation" in p_data["dimension_scores"]
    assert "evidence_matrix" in p_data
    assert "report" in p_data
    assert p_data["report"]["executive_summary"] != ""
    assert p_data["report"]["legal_disclaimer"] != ""

    # 5. Retrieve project details
    res = client.get(f"/api/projects/{project_id}", headers=DEMO_HEADERS)
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == project_id
    assert detail["analysis"] is not None
    assert detail["report"] is not None
    assert detail["features_count"] > 0

    # 6. Execute direct prior-art corpus search
    search_payload = {
        "query": "quantum surface code syndrome decoding",
        "top_k": 5,
        "methods": ["sparse"],
        "rerank": False,
    }
    res = client.post("/api/retrieval/search", json=search_payload, headers=DEMO_HEADERS)
    assert res.status_code == 200
    search_data = res.json()
    assert search_data["query"] == "quantum surface code syndrome decoding"
    assert search_data["sparse_results"] is not None

    # 7. Delete project workspace
    res = client.delete(f"/api/projects/{project_id}", headers=DEMO_HEADERS)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Confirm deletion
    res = client.get(f"/api/projects/{project_id}", headers=DEMO_HEADERS)
    assert res.status_code == 404
