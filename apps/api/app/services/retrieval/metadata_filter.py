import re
from typing import Optional, Any
from app.schemas.patent import PatentChunkCreate
from app.services.retrieval.types import RetrievalFilters


class MetadataFilterMatcher:
    """Evaluates filter predicates against patent chunk metadata for in-memory BM25 filtering

    and generates native Qdrant filter expressions for dense vector search.
    """

    @classmethod
    def matches_chunk(cls, chunk: PatentChunkCreate, filters: Optional[RetrievalFilters]) -> bool:
        """Returns True if the chunk satisfies all non-None filter criteria."""
        if not filters:
            return True

        meta = chunk.metadata or {}

        # 1. Section filter
        if filters.section and chunk.section.lower() != filters.section.lower():
            return False

        # 2. Claim-only constraint
        if filters.claim_only and chunk.section.lower() != "claims":
            return False

        # 3. Country code filter
        if filters.country_code:
            chunk_country = meta.get("country_code") or ""
            if chunk_country.upper() != filters.country_code.strip().upper():
                return False

        # 4. Language filter
        if filters.language:
            chunk_lang = meta.get("language") or "en"
            if chunk_lang.lower() != filters.language.strip().lower():
                return False

        # 5. CPC class prefix or exact match
        if filters.cpc_class:
            cpc_list = meta.get("cpc_classes") or []
            if not isinstance(cpc_list, list):
                cpc_list = [str(cpc_list)]
            target_cpc = filters.cpc_class.strip().upper()
            if not any(target_cpc in c.upper() for c in cpc_list):
                return False

        # 6. IPC class prefix or exact match
        if filters.ipc_class:
            ipc_list = meta.get("ipc_classes") or []
            if not isinstance(ipc_list, list):
                ipc_list = [str(ipc_list)]
            target_ipc = filters.ipc_class.strip().upper()
            if not any(target_ipc in c.upper() for c in ipc_list):
                return False

        # 7. Date range filter
        pub_date = meta.get("publication_date")
        if pub_date:
            date_str = str(pub_date).strip()
            if filters.date_from and date_str < filters.date_from:
                return False
            if filters.date_to and date_str > filters.date_to:
                return False
        elif filters.date_from or filters.date_to:
            # Date required by filter but missing from chunk
            return False

        return True

    @classmethod
    def build_qdrant_filter(cls, filters: Optional[RetrievalFilters]) -> Optional[Any]:
        """Translates RetrievalFilters into a native Qdrant models.Filter object.

        Returns None if filters is empty or None.
        """
        if not filters:
            return None

        try:
            from qdrant_client.http import models
        except ImportError:
            return None

        must_conditions = []

        if filters.country_code:
            must_conditions.append(
                models.FieldCondition(
                    key="country_code",
                    match=models.MatchValue(value=filters.country_code.strip().upper()),
                )
            )

        if filters.section:
            must_conditions.append(
                models.FieldCondition(
                    key="section",
                    match=models.MatchValue(value=filters.section.strip().lower()),
                )
            )

        if filters.claim_only:
            must_conditions.append(
                models.FieldCondition(
                    key="section",
                    match=models.MatchValue(value="claims"),
                )
            )

        if filters.language:
            must_conditions.append(
                models.FieldCondition(
                    key="language",
                    match=models.MatchValue(value=filters.language.strip().lower()),
                )
            )

        if filters.cpc_class:
            must_conditions.append(
                models.FieldCondition(
                    key="cpc_classes",
                    match=models.MatchValue(value=filters.cpc_class.strip()),
                )
            )

        if filters.ipc_class:
            must_conditions.append(
                models.FieldCondition(
                    key="ipc_classes",
                    match=models.MatchValue(value=filters.ipc_class.strip()),
                )
            )

        if filters.date_from or filters.date_to:
            range_cond = models.Range(
                gte=filters.date_from if filters.date_from else None,
                lte=filters.date_to if filters.date_to else None,
            )
            must_conditions.append(
                models.FieldCondition(
                    key="publication_date",
                    range=range_cond,
                )
            )

        if not must_conditions:
            return None

        return models.Filter(must=must_conditions)
