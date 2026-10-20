from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health status")
    service: str = Field(default="PatentIQ API", description="Service name")
    version: str = Field(default="0.1.0", description="API version")


class DatabaseHealthResponse(BaseModel):
    status: str = Field(..., description="Health status (ok, unconfigured, degraded)")
    service: str = Field(default="Supabase", description="Service name")
    connected: bool = Field(..., description="Whether connection was successfully established")
    details: Optional[str] = Field(None, description="Safe diagnostic message without credentials")
    schema_available: Optional[bool] = Field(None, description="Whether schema tables are available")
