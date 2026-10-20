import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service wrapper for Supabase database and authentication operations.

    Reads credentials strictly from application settings without logging or exposing secrets.
    Provides clean interfaces mapping to the reference schema in backend/supabase_schema.sql.
    """

    def __init__(self) -> None:
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None

    @property
    def is_configured(self) -> bool:
        """Returns True if minimum public client credentials are set and non-placeholder."""
        if not (settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY):
            return False
        url_lower = settings.SUPABASE_URL.lower()
        return "placeholder" not in url_lower and "your-project" not in url_lower

    @property
    def is_admin_configured(self) -> bool:
        """Returns True if admin service role credentials are set and non-placeholder."""
        if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
            return False
        url_lower = settings.SUPABASE_URL.lower()
        key_lower = settings.SUPABASE_SERVICE_ROLE_KEY.lower()
        return (
            "placeholder" not in url_lower
            and "your-project" not in url_lower
            and "your-" not in key_lower
            and "placeholder" not in key_lower
        )

    def get_client(self) -> Optional[Client]:
        """Returns the public anon Supabase client.

        Initializes lazily and returns None if credentials are not configured.
        """
        if not self.is_configured:
            logger.debug("Supabase public credentials not configured.")
            return None

        if self._client is None:
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_ANON_KEY,
            )
        return self._client

    def get_admin_client(self) -> Optional[Client]:
        """Returns the administrative service-role Supabase client.

        Used for server-side tasks requiring elevated permissions without exposing credentials.
        """
        if not self.is_admin_configured:
            logger.debug("Supabase service role credentials not configured.")
            return None

        if self._admin_client is None:
            self._admin_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return self._admin_client

    async def check_connection(self) -> Dict[str, Any]:
        """Checks connectivity to Supabase without exposing credentials or internal secrets.

        Returns a sanitized dictionary matching DatabaseHealthResponse.
        """
        if not self.is_configured:
            return {
                "status": "unconfigured",
                "service": "Supabase",
                "connected": False,
                "details": "Supabase credentials not configured in environment.",
                "schema_available": False,
            }

        try:
            client = self.get_client()
            if client is None:
                return {
                    "status": "unconfigured",
                    "service": "Supabase",
                    "connected": False,
                    "details": "Supabase client failed to initialize.",
                    "schema_available": False,
                }

            # Attempt a minimal safe query against the public schema (limit 0 to avoid returning data)
            # This checks DNS resolution, SSL handshake, and API gateway response
            response = client.table("projects").select("id").limit(1).execute()
            return {
                "status": "ok",
                "service": "Supabase",
                "connected": True,
                "details": "Connection successfully verified.",
                "schema_available": True,
            }
        except Exception as exc:
            # Sanitize error message to avoid printing any URL or key details
            error_type = type(exc).__name__
            logger.warning("Supabase connection check returned %s", error_type)
            return {
                "status": "degraded",
                "service": "Supabase",
                "connected": False,
                "details": f"Database reachable check returned: {error_type}",
                "schema_available": False,
            }

    # =========================================================================
    # Service Interface Methods (Target Architecture mapping to supabase_schema.sql)
    # =========================================================================

    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new project record in public.projects."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = client.table("projects").insert(project_data).execute()
        return res.data[0] if res.data else {}

    async def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches a project by ID ensuring user ownership."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = (
            client.table("projects")
            .select("*")
            .eq("id", project_id)
            .eq("user_id", user_id)
            .execute()
        )
        return res.data[0] if res.data else None

    async def list_projects(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists user-owned projects ordered by creation date."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = (
            client.table("projects")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    async def save_document_metadata(
        self, project_id: str, extracted_text: str, extracted_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Updates project with parsed document text and metadata."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = (
            client.table("projects")
            .update({
                "extracted_text": extracted_text,
                "extracted_metadata": extracted_metadata,
                "status": "processed",
            })
            .eq("id", project_id)
            .execute()
        )
        return res.data[0] if res.data else {}

    async def save_feature(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persists an extracted invention feature to public.features."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = client.table("features").insert(feature_data).execute()
        return res.data[0] if res.data else {}

    async def save_evidence_item(self, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persists a feature-to-patent evidence link in public.evidence_items."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = client.table("evidence_items").insert(evidence_data).execute()
        return res.data[0] if res.data else {}

    async def save_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persists an EB-PRE analysis result in public.analyses."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = client.table("analyses").insert(analysis_data).execute()
        return res.data[0] if res.data else {}

    async def save_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persists a report record in public.reports."""
        client = self.get_admin_client() or self.get_client()
        if not client:
            raise RuntimeError("Database service is not configured.")
        res = client.table("reports").insert(report_data).execute()
        return res.data[0] if res.data else {}


# Global service instance
supabase_service = SupabaseService()
