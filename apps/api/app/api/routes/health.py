from fastapi import APIRouter
from app.schemas.health import HealthResponse, DatabaseHealthResponse
from app.core.config import settings
from app.services.supabase_service import supabase_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="API Health Check")
async def get_health() -> HealthResponse:
    """Returns basic API service health status, service name, and version.

    Independent of external database connectivity.
    """
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
    )


@router.get("/health/database", response_model=DatabaseHealthResponse, summary="Database Health Check")
async def get_database_health() -> DatabaseHealthResponse:
    """Verifies reachability of the database service safely.

    Checks Supabase PostgreSQL if configured; otherwise reports local durable SQLite store.
    """
    result = await supabase_service.check_connection()
    if result.get("status") == "unconfigured":
        from app.services.persistence.sqlite_store import get_sqlite_store
        store = get_sqlite_store()
        is_ready = store.is_ready()
        return DatabaseHealthResponse(
            status="connected" if is_ready else "unconfigured",
            service="SQLite (Local Durable Store)",
            connected=is_ready,
            details="Local durable SQLite database active at data/patentiq_local.db." if is_ready else "Local store uninitialized.",
            schema_available=is_ready,
        )

    return DatabaseHealthResponse(
        status=result["status"],
        service=result.get("service", "Supabase"),
        connected=result["connected"],
        details=result.get("details"),
        schema_available=result.get("schema_available"),
    )
