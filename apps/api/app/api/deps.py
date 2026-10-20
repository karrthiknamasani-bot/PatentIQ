"""Authentication and request dependencies.

Integrates directly with Supabase Auth. Validates bearer JWTs issued by
Supabase Auth without storing passwords, maintaining a separate user database,
or using legacy secrets.
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.schemas.user import CurrentUser
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

# Standard OAuth2 Bearer token extraction
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """Validates the incoming Bearer token against Supabase Auth or deterministic Demo token.

    Modes:
    1. Real Mode (Supabase Configured):
       Validates the Bearer JWT against Supabase Auth API.
    2. Demo Mode (Supabase Not Configured, Non-Production):
       Only accepts settings.DEMO_BEARER_TOKEN returning settings.DEMO_USER_ID.
       Arbitrary tokens are strictly rejected.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # When Supabase is NOT configured:
    if not supabase_service.is_configured:
        # Strict Demo Mode check: Never allowed in production, only exact demo token accepted
        if settings.ENVIRONMENT.lower() != "production" and token == settings.DEMO_BEARER_TOKEN:
            return CurrentUser(
                user_id=settings.DEMO_USER_ID,
                email=settings.DEMO_USER_EMAIL,
            )

        # Local durable SQLite session check (Google OAuth session)
        try:
            from app.services.persistence.sqlite_store import get_sqlite_store
            session_user = get_sqlite_store().get_session_user(token)
            if session_user:
                return CurrentUser(
                    user_id=session_user["user_id"],
                    email=session_user["email"],
                )
        except Exception as exc:
            logger.warning("Session token lookup failed: %s", exc)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication provider (Supabase) is not configured.",
        )

    # Real Mode: Supabase is configured
    client = supabase_service.get_client()

    try:
        # Verify token with Supabase Auth API
        auth_response = client.auth.get_user(token)
        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = auth_response.user
        return CurrentUser(
            user_id=str(user.id),
            email=getattr(user, "email", None),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Token verification failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
