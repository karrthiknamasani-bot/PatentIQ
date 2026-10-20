from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Project title")
    description: Optional[str] = Field(None, max_length=2000, description="Invention overview")
    domain: Optional[str] = Field("General Technology", max_length=100, description="Technical domain")
    original_file_name: Optional[str] = Field("document.txt", max_length=255)
    file_type: Optional[str] = Field("txt", max_length=10)
    file_size: Optional[int] = Field(0, ge=0)


class ProjectSummaryResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    original_file_name: str
    file_type: str
    file_size: int
    status: str = "uploaded"
    processing_stage: str = "uploaded"
    readiness_score: Optional[int] = None
    confidence_score: Optional[float] = None
    readiness_category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectDetailResponse(ProjectSummaryResponse):
    extracted_text: Optional[str] = None
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    analysis: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    features_count: int = 0
    chunks_count: int = 0
