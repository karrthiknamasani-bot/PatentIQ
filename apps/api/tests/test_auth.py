from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.supabase_service import SupabaseService


@pytest.mark.asyncio
async def test_auth_me_no_token():
    """Verify that GET /api/auth/me returns 401 when no token is provided."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_auth_me_unconfigured_service():
    """Verify that GET /api/auth/me returns 503 if Supabase is unconfigured."""
    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=False):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer some-test-token"},
            )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_auth_me_mocked_success():
    """Verify that GET /api/auth/me returns current user when Supabase verifies token."""
    mock_user = MagicMock()
    mock_user.id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    mock_user.email = "inventor@example.com"

    mock_auth_response = MagicMock()
    mock_auth_response.user = mock_user

    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = mock_auth_response

    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=True), \
         patch("app.services.supabase_service.supabase_service.get_client", return_value=mock_client):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer valid-mock-jwt"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert data["email"] == "inventor@example.com"


@pytest.mark.asyncio
async def test_auth_me_invalid_token():
    """Verify that GET /api/auth/me returns 401 if Supabase rejects the token."""
    mock_client = MagicMock()
    mock_client.auth.get_user.side_effect = Exception("Invalid JWT signature")

    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=True), \
         patch("app.services.supabase_service.supabase_service.get_client", return_value=mock_client):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get(
                "/api/auth/me",
                headers={"Authorization": "Bearer expired-mock-jwt"},
            )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
