import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.schemas.user import CurrentUser
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectSummaryResponse,
    ProjectDetailResponse,
)
from app.services.persistence.models import ProjectCreate
from app.services.persistence.repository import SupabaseRepository

logger = logging.getLogger("patentiq.api.projects")

router = APIRouter()
repository = SupabaseRepository()


@router.get("", response_model=List[ProjectSummaryResponse], summary="List User Projects")
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
) -> List[ProjectSummaryResponse]:
    """Retrieves all projects owned by the authenticated user."""
    projects = await repository.list_projects(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
    )

    summaries = []
    for p in projects:
        # Check if analysis exists for scoring overview
        analysis = await repository.get_analysis(project_id=p.id, user_id=current_user.user_id)
        summaries.append(
            ProjectSummaryResponse(
                id=p.id,
                user_id=p.user_id,
                title=p.title,
                description=p.description,
                original_file_name=p.original_file_name,
                file_type=p.file_type,
                file_size=p.file_size,
                status=p.status,
                processing_stage=p.processing_stage,
                readiness_score=analysis.readiness_score if analysis else None,
                confidence_score=analysis.confidence_score if analysis else None,
                readiness_category=analysis.readiness_category if analysis else None,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return summaries


@router.post("", response_model=ProjectSummaryResponse, status_code=status.HTTP_201_CREATED, summary="Create Project")
async def create_project(
    req: ProjectCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectSummaryResponse:
    """Creates a new project workspace for the authenticated user."""
    stored_name = f"{uuid.uuid4()}.{req.file_type}"
    project_in = ProjectCreate(
        user_id=current_user.user_id,
        title=req.title,
        description=req.description,
        original_file_name=req.original_file_name or "document.txt",
        stored_file_name=stored_name,
        file_path=f"projects/{current_user.user_id}/{stored_name}",
        file_type=req.file_type or "txt",
        file_size=req.file_size or 0,
        status="created",
        processing_stage="created",
    )

    p_status, record = await repository.create_project(project_in)
    if not p_status.success or not record:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {p_status.error or p_status.details}",
        )

    return ProjectSummaryResponse(
        id=record.id,
        user_id=record.user_id,
        title=record.title,
        description=record.description,
        original_file_name=record.original_file_name,
        file_type=record.file_type,
        file_size=record.file_size,
        status=record.status,
        processing_stage=record.processing_stage,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse, summary="Get Project Details")
async def get_project(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectDetailResponse:
    """Retrieves full details, analysis metrics, and report for a specific project."""
    project = await repository.get_project(project_id=project_id, user_id=current_user.user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found or unauthorized.",
        )

    analysis = await repository.get_analysis(project_id=project_id, user_id=current_user.user_id)
    report = await repository.get_report(project_id=project_id, user_id=current_user.user_id)
    features = await repository.get_features(project_id=project_id, user_id=current_user.user_id)
    chunks = await repository.get_document_chunks(project_id=project_id, user_id=current_user.user_id)

    return ProjectDetailResponse(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        description=project.description,
        original_file_name=project.original_file_name,
        file_type=project.file_type,
        file_size=project.file_size,
        status=project.status,
        processing_stage=project.processing_stage,
        readiness_score=analysis.readiness_score if analysis else None,
        confidence_score=analysis.confidence_score if analysis else None,
        readiness_category=analysis.readiness_category if analysis else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
        extracted_text=project.extracted_text,
        extracted_metadata=project.extracted_metadata or {},
        analysis=analysis.model_dump() if analysis else None,
        report=report.model_dump() if report else None,
        features_count=len(features),
        chunks_count=len(chunks),
    )


@router.delete("/{project_id}", summary="Delete Project")
async def delete_project(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Permanently deletes a project workspace and all its cascaded analysis data."""
    del_status = await repository.delete_project(project_id=project_id, user_id=current_user.user_id)
    if not del_status.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=del_status.error or f"Project '{project_id}' could not be deleted.",
        )

    return {
        "success": True,
        "message": f"Project '{project_id}' deleted successfully.",
        "project_id": project_id,
    }
