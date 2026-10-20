import io
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


SAMPLE_INVENTION_DISCLOSURE = """
TITLE: Autonomous Hybrid Drone Navigation via Edge LiDAR SLAM

ABSTRACT:
A system and method for autonomous aerial vehicle navigation in GPS-denied environments.
The system comprises an edge neuromorphic processor, a low-latency solid-state LiDAR sensor,
and an adaptive optical flow camera array coupled to a brushless motor flight controller.

FIELD OF THE INVENTION:
The present invention relates generally to robotics and avionics, and more specifically
to edge-accelerated simultaneous localization and mapping (SLAM) for unmanned aerial vehicles.

BACKGROUND OF THE INVENTION:
Conventional drones rely heavily on global positioning satellite (GPS) signals. In indoor,
underground, or contested electronic environments, loss of GPS causes catastrophic localization failure.

SUMMARY OF THE INVENTION:
The present disclosure provides a resilient navigation unit comprising:
1. A multi-channel solid-state LiDAR producing 100,000 range points per second.
2. An edge FPGA executing sparse feature-graph SLAM with sub-millisecond pose updates.
3. An inertial measurement unit (IMU) sensor fusion filter fusing optical flow velocity vectors.
4. A deterministic fault-recovery state machine switching to predictive dead reckoning.

DETAILED DESCRIPTION:
Referring to the architecture, LiDAR sensor pulses reflect off ambient obstacles.
The edge processor computes point-cloud voxel grids, extracting planar and edge features.
A Kalman filter blends IMU angular velocity with optical odometry to maintain trajectory.
"""


@pytest.mark.asyncio
async def test_pipeline_unauthenticated():
    """Verify that the pipeline orchestrator requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        files = {"file": ("disclosure.txt", io.BytesIO(b"Hello world"), "text/plain")}
        res = await client.post("/api/pipeline/analyze", files=files)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_pipeline_invalid_extension():
    """Verify that unsupported file extensions are rejected."""
    auth_headers = {"Authorization": f"Bearer {settings.DEMO_BEARER_TOKEN}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        files = {"file": ("disclosure.exe", io.BytesIO(b"binary payload"), "application/octet-stream")}
        res = await client.post("/api/pipeline/analyze", files=files, headers=auth_headers)
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]


@pytest.mark.asyncio
async def test_pipeline_full_execution():
    """Verify end-to-end execution of the 18-step pipeline orchestrator."""
    auth_headers = {"Authorization": f"Bearer {settings.DEMO_BEARER_TOKEN}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        file_content = SAMPLE_INVENTION_DISCLOSURE.encode("utf-8")
        files = {"file": ("drone_slam_patent.txt", io.BytesIO(file_content), "text/plain")}
        data = {
            "title": "Autonomous Drone SLAM",
            "domain": "Robotics & Avionics",
        }
        res = await client.post(
            "/api/pipeline/analyze",
            files=files,
            data=data,
            headers=auth_headers,
        )

        assert res.status_code == 200, res.text
        resp_data = res.json()

        # Check core identity & structure
        assert resp_data["project_id"] is not None
        assert resp_data["title"] == "Autonomous Drone SLAM"
        assert resp_data["chunk_count"] > 0
        assert resp_data["feature_count"] > 0

        # Check EB-PRE numerical score bounds
        readiness = resp_data["readiness_score"]
        assert 0.0 <= readiness <= 1.0
        assert 0.0 <= resp_data["readiness_percentage"] <= 100.0
        assert 0.0 <= resp_data["confidence_score"] <= 1.0
        assert resp_data["readiness_category"] in ["low", "moderate", "high"]

        # Check 6 dimensions present
        dims = resp_data["dimension_scores"]
        expected_dims = [
            "novelty",
            "prior_art_overlap",
            "technical_differentiation",
            "innovation_characteristics",
            "documentation_quality",
            "commercial_potential",
        ]
        for dim in expected_dims:
            assert dim in dims
            assert "score" in dims[dim]

        # Check report structure
        assert "report" in resp_data
        report = resp_data["report"]
        assert "executive_summary" in report or "invention_overview" in report
        assert resp_data["generation_method"] in ["gemini", "deterministic_fallback"]
        assert resp_data["persisted"] is True
