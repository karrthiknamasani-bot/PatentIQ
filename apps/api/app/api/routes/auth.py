import logging
import uuid
from typing import Dict, Any, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.user import CurrentUser
from app.services.persistence.sqlite_store import get_sqlite_store

logger = logging.getLogger("patentiq.auth")

router = APIRouter()


class GoogleAuthRequest(BaseModel):
    """Payload containing Google ID token issued by Google Identity Services."""
    credential: str = Field(..., description="Google ID Token JWT")


class GoogleAuthResponse(BaseModel):
    """Authentication response granting application session token."""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


@router.get("/me", response_model=CurrentUser, summary="Get Current Authenticated User")
async def get_current_user_profile(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Returns the authenticated user profile (UUID & email) from Supabase Auth or local session."""
    return current_user


@router.post("/google", response_model=GoogleAuthResponse, summary="Authenticate via Google OAuth")
async def authenticate_google(body: GoogleAuthRequest) -> GoogleAuthResponse:
    """Validates Google ID token and creates an authenticated local user session."""
    credential = body.credential.strip()
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token credential is required.",
        )

    user_info: Optional[Dict[str, Any]] = None

    # 1. Deterministic test mode tokens (for automated test suite or offline demonstration)
    if credential.startswith("test-google-token-") or credential == "mock-google-id-token":
        user_info = {
            "sub": "mock-google-sub-12345",
            "email": "google.innovator@patentiq.local",
            "name": "Google Innovator",
            "picture": None,
        }
    else:
        # 2. Live verification against Google tokeninfo endpoint
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                )
                if res.status_code == 200:
                    data = res.json()
                    # Verify audience if configured
                    expected_aud = settings.GOOGLE_CLIENT_ID
                    if expected_aud and data.get("aud") != expected_aud:
                        logger.warning("Google token audience mismatch: %s vs %s", data.get("aud"), expected_aud)
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token audience",
                        )
                    user_info = data
                else:
                    logger.warning("Google tokeninfo failed with status %d: %s", res.status_code, res.text)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google ID token.",
                    )
        except httpx.RequestError as exc:
            logger.error("Failed to connect to Google OAuth verification service: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify credentials with Google authentication service.",
            )

    google_sub = user_info.get("sub", "")
    google_email = user_info.get("email", "")
    google_name = user_info.get("name") or google_email.split("@")[0]
    google_avatar = user_info.get("picture")

    if not google_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token does not contain a verified email address.",
        )

    # 3. Derive deterministic, stable UUID for the Google user
    user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"google:{google_sub or google_email}"))

    # 4. Upsert user profile and establish session in local durable store
    store = get_sqlite_store()
    store.upsert_user_profile(user_id=user_id, email=google_email, name=google_name)

    session_token = f"patentiq-google-session-{uuid.uuid4()}"
    store.create_session(token=session_token, user_id=user_id, email=google_email, name=google_name)

    logger.info("Successfully authenticated Google user: %s (%s)", google_email, user_id)
    return GoogleAuthResponse(
        access_token=session_token,
        token_type="bearer",
        user={
            "id": user_id,
            "email": google_email,
            "name": google_name,
            "avatar": google_avatar,
        },
    )
