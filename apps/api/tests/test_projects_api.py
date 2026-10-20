import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_projects_unauthenticated():
    """Verify that projects endpoints require authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/projects")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_projects_demo_mode_lifecycle():
    """Verify project creation, retrieval, listing, and deletion using the deterministic demo token."""
    auth_headers = {"Authorization": f"Bearer {settings.DEMO_BEARER_TOKEN}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Create project
        create_payload = {
            "title": "Quantum Neural Processor",
            "description": "A novel superconducting quantum neural computing architecture.",
            "domain": "Quantum Computing",
            "original_file_name": "quantum_spec.txt",
            "file_type": "txt",
            "file_size": 1024,
        }
        create_res = await client.post("/api/projects", json=create_payload, headers=auth_headers)
        assert create_res.status_code == 201
        project_data = create_res.json()
        project_id = project_data["id"]
        assert project_data["title"] == "Quantum Neural Processor"
        assert project_data["user_id"] == settings.DEMO_USER_ID

        # 2. List projects
        list_res = await client.get("/api/projects", headers=auth_headers)
        assert list_res.status_code == 200
        projects_list = list_res.json()
        assert any(p["id"] == project_id for p in projects_list)

        # 3. Get project detail
        detail_res = await client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["id"] == project_id
        assert detail_data["title"] == "Quantum Neural Processor"

        # 4. Delete project
        del_res = await client.delete(f"/api/projects/{project_id}", headers=auth_headers)
        assert del_res.status_code == 200
        assert del_res.json()["success"] is True

        # 5. Confirm deletion (404)
        get_deleted_res = await client.get(f"/api/projects/{project_id}", headers=auth_headers)
        assert get_deleted_res.status_code == 404
