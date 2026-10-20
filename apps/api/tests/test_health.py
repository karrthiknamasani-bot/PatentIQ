from unittest.mock import AsyncMock, patch, PropertyMock
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.supabase_service import SupabaseService


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify that GET /api/health returns 200 with status ok and service name."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "PatentIQ API"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_database_health_unconfigured():
    """Verify that GET /api/health/database reports local SQLite store when Supabase is absent."""
    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=False):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/api/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["status"] == "connected"
        assert data["service"] == "SQLite (Local Durable Store)"


@pytest.mark.asyncio
async def test_database_health_mocked_success():
    """Verify that GET /api/health/database returns ok when Supabase connection succeeds."""
    mock_check = AsyncMock(return_value={
        "status": "ok",
        "service": "Supabase",
        "connected": True,
        "details": "Connection successfully verified.",
    })
    with patch("app.services.supabase_service.supabase_service.check_connection", mock_check):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/api/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["status"] == "ok"
        assert data["service"] == "Supabase"


@pytest.mark.asyncio
async def test_database_health_mocked_degraded():
    """Verify that GET /api/health/database handles connection failure gracefully."""
    mock_check = AsyncMock(return_value={
        "status": "degraded",
        "service": "Supabase",
        "connected": False,
        "details": "Database reachable check returned: APIError",
    })
    with patch("app.services.supabase_service.supabase_service.check_connection", mock_check):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/api/health/database")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["status"] == "degraded"
