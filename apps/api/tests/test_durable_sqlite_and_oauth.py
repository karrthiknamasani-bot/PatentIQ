import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.persistence.models import ProjectCreate
from app.services.persistence.repository import SupabaseRepository
from app.services.persistence.sqlite_store import get_sqlite_store


@pytest.mark.asyncio
async def test_database_health_endpoint():
    """Verify that GET /api/health/database returns SQLite connected status in local mode."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/health/database")

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["status"] == "connected"
    assert "SQLite" in data["service"]


@pytest.mark.asyncio
async def test_sqlite_persistence_survives_memory_wipe():
    """Verify that project data saved in SQLite survives memory dictionary deletion."""
    repo = SupabaseRepository()
    test_user_id = "00000000-0000-0000-0000-000000000001"

    status, proj = await repo.create_project(
        ProjectCreate(
            user_id=test_user_id,
            title="Durable Battery Separator Invention",
            description="High temperature ceramic separator",
            original_file_name="battery_separator.pdf",
            stored_file_name="battery_separator_uuid.pdf",
            file_path="uploads/battery_separator_uuid.pdf",
            file_type="pdf",
            file_size=1024,
        )
    )
    assert status.success is True
    project_id = proj.id

    # Simulate backend restart by wiping memory cache completely
    repo._demo_projects.clear()
    assert project_id not in repo._demo_projects

    # Retrieve from disk via repository
    recovered = await repo.get_project(project_id, test_user_id)
    assert recovered is not None
    assert recovered.id == project_id
    assert recovered.title == "Durable Battery Separator Invention"
    assert recovered.user_id == test_user_id

    # Clean up
    del_status = await repo.delete_project(project_id, test_user_id)
    assert del_status.success is True


@pytest.mark.asyncio
async def test_google_oauth_flow_and_session_auth():
    """Verify Google OAuth endpoint generates valid sessions that authenticate protected routes."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # 1. Exchange mock Google token
        oauth_resp = await client.post(
            "/api/auth/google",
            json={"credential": "test-google-token-12345"},
        )
        assert oauth_resp.status_code == 200
        auth_data = oauth_resp.json()
        assert "access_token" in auth_data
        session_token = auth_data["access_token"]
        assert session_token.startswith("patentiq-google-session-")
        google_user_id = auth_data["user"]["id"]

        # 2. Authenticate to /api/auth/me with bearer session token
        me_resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {session_token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user_id"] == google_user_id
        assert "google.innovator" in me_data["email"]

        # 3. Create a project under the Google user identity
        proj_resp = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {session_token}"},
            json={
                "title": "Google Innovator Solar Concentrator",
                "description": "Fresnel lens solar concentrator",
            },
        )
        assert proj_resp.status_code in (200, 201)
        created_proj = proj_resp.json()
        assert created_proj["title"] == "Google Innovator Solar Concentrator"

        # 4. Verify project ownership in SQLite
        store = get_sqlite_store()
        db_p = store.get_project(created_proj["id"], google_user_id)
        assert db_p is not None
        assert db_p["user_id"] == google_user_id
