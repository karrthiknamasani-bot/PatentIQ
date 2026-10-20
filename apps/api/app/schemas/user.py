from typing import Optional
from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    """Authenticated user context derived from Supabase Auth JWT."""

    user_id: str = Field(..., description="Unique Supabase Auth UUID")
    email: Optional[str] = Field(None, description="User email address")
