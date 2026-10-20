import logging
from typing import List, Optional, Dict, Any

from app.schemas.document import DocumentChunk
from app.services.features.types import (
    FeatureType,
    FeatureCandidate,
    SourceProvenance,
)
from app.services.features.feature_schema import (
    TechnicalFeature,
    ExtractionMetadata,
    FeatureExtractionResponse,
)
from app.services.features.feature_normalizer import FeatureNormalizer
from app.services.features.feature_extractor import (
    BaseFeatureExtractor,
    RuleBasedFeatureExtractor,
    GeminiFeatureExtractor,
)

logger = logging.getLogger("patentiq.features")


class PatentFeatureService:
    """End-to-end service for extracting, normalizing, and consolidating technical features.

    Pipeline:
    Processed Document Chunks
            ↓
    Feature Extraction (Rule-Based or LLM)
            ↓
    Validation (Controlled Vocabulary & Quality checks)
            ↓
    Deterministic Normalization
            ↓
    Duplicate Consolidation & Multi-Source Provenance Merging
            ↓
    Deterministic Feature IDs
            ↓
    Structured Technical Feature Set
    """

    DANGLING_ENDINGS = {
        "to", "for", "with", "by", "from", "of", "in", "on", "during", "between",
        "and", "or", "wherein", "available", "such", "as", "the", "a", "an", "that",
        "which", "is", "are", "was", "were", "be", "being", "having", "including",
        "comprising",
    }

    @classmethod
    def _is_fragmentary(cls, text: str) -> bool:
        """Detects whether candidate text is an isolated dangling fragment or incomplete predicate."""
        cleaned = text.strip().rstrip(";., ")
        words = cleaned.split()
        if not words:
            return True

        # 1. Ends in a dangling word (preposition, conjunction, or dangling modifier)
        if words[-1].lower() in cls.DANGLING_ENDINGS:
            return True

        # 2. Bare incomplete verb phrases (e.g. "receives a conflict response", "confirming the same seat")
        # that lack a subject or outcome and are fewer than 5 words
        bare_verb_prefixes = {
            "receives", "receiving", "confirming", "confirms", "locking", "locks",
            "allocating", "allocates", "maintains", "maintaining", "outputting",
            "configured to", "operable to", "adapted to",
        }
        lower = cleaned.lower()
        if len(words) < 5:
            if any(lower.startswith(p) for p in bare_verb_prefixes):
                if not any(k in lower for k in ["control", "manager", "algorithm", "database", "controller", "engine", "service", "system", "synchronization"]):
                    return True

        return False

    def __init__(self, extractor: Optional[BaseFeatureExtractor] = None):
        self._extractor = extractor

    def get_extractor(self, method: str = "auto") -> BaseFeatureExtractor:
        """Resolves the feature extractor instance based on requested method."""
        if self._extractor is not None:
            return self._extractor

        if method == "gemini":
            return GeminiFeatureExtractor()
        # Default or 'rule_based' or 'auto'
        return RuleBasedFeatureExtractor()

    def extract_features(
        self,
        project_id: str,
        chunks: List[DocumentChunk],
        method: str = "auto",
    ) -> FeatureExtractionResponse:
        """Executes the full feature extraction pipeline over a set of document chunks.

        Args:
            project_id: Invention project identifier.
            chunks: List of DocumentChunk instances.
            method: 'auto', 'rule_based', or 'gemini'.

        Returns:
            FeatureExtractionResponse containing structured TechnicalFeatures and metadata.
        """
        if not project_id or not project_id.strip():
            raise ValueError("project_id must be a non-empty string.")

        if not chunks:
            return FeatureExtractionResponse(
                project_id=project_id,
                features=[],
                total_features=0,
                extraction_metadata=ExtractionMetadata(
                    number_of_input_chunks=0,
                    number_of_raw_candidates=0,
                    number_of_validated_features=0,
                    number_of_duplicates_merged=0,
                    extraction_method=method,
                    processing_status="completed_empty",
                ),
            )

        extractor = self.get_extractor(method)
        raw_candidates: List[FeatureCandidate] = []

        # 1. Extraction from all chunks
        for chunk in chunks:
            try:
                extracted = extractor.extract(chunk)
                raw_candidates.extend(extracted)
            except Exception as exc:
                logger.warning("Extraction error on chunk %d: %s", chunk.chunk_index, exc)

        # 2. Validation & Normalization
        validated_candidates: List[Tuple[FeatureCandidate, str]] = []
        for cand in raw_candidates:
            if not cand.feature_text or not cand.feature_text.strip():
                continue

            normalized = FeatureNormalizer.normalize_text(cand.feature_text)
            if not normalized:
                continue

            validated_candidates.append((cand, normalized))

        # 3. Quality Filtering, Subsumption & Provenance Merging
        # Sort candidates by length descending so comprehensive technical capabilities subsume sub-clauses
        validated_candidates.sort(key=lambda item: len(item[1]), reverse=True)

        grouped_features: Dict[str, Dict[str, Any]] = {}
        duplicates_merged_count = 0

        for cand, norm_text in validated_candidates:
            is_frag = self._is_fragmentary(norm_text)

            prov = SourceProvenance(
                chunk_id=cand.source_chunk_id,
                chunk_index=cand.source_chunk_index,
                source_reference=cand.source_reference,
                section=cand.section,
                page_number=cand.page_number,
                claim_number=cand.claim_number,
                evidence_span_start=cand.evidence_span_start,
                evidence_span_end=cand.evidence_span_end,
            )

            # Check if candidate is subsumed by an already accepted longer candidate
            subsumed = False
            for existing_canon_key, group in grouped_features.items():
                existing_norm = group["normalized_text"]
                # A. Substring inclusion
                if norm_text.lower() in existing_norm.lower():
                    subsumed = True
                    group["supporting_sources"].append(prov)
                    duplicates_merged_count += 1
                    break
                # B. Sub-clause fragment from the same chunk whose tokens are covered
                elif is_frag and cand.source_chunk_index == group["primary_candidate"].source_chunk_index:
                    frag_words = set(norm_text.lower().split()) - {"a", "an", "the", "of", "to", "in", "for", "with", "by", "on", "at", "during", "is", "are"}
                    existing_words = set(existing_norm.lower().split())
                    if frag_words and frag_words.issubset(existing_words):
                        subsumed = True
                        group["supporting_sources"].append(prov)
                        duplicates_merged_count += 1
                        break

            if subsumed:
                continue

            # Incomplete isolated dangling fragments are discarded
            if is_frag:
                duplicates_merged_count += 1
                continue

            canon_key = FeatureNormalizer.get_canonical_key(cand.feature_type.value, norm_text)
            if canon_key not in grouped_features:
                grouped_features[canon_key] = {
                    "primary_candidate": cand,
                    "normalized_text": norm_text,
                    "supporting_sources": [prov],
                    "max_confidence": cand.confidence,
                }
            else:
                # Existing exact duplicate found
                duplicates_merged_count += 1
                group = grouped_features[canon_key]
                group["supporting_sources"].append(prov)
                if cand.confidence > group["max_confidence"]:
                    group["max_confidence"] = cand.confidence
                    group["primary_candidate"] = cand

        # 4. Deterministic Feature ID Generation and Final Assembly
        final_features: List[TechnicalFeature] = []
        for canon_key, group in grouped_features.items():
            primary = group["primary_candidate"]
            norm_text = group["normalized_text"]
            sources = group["supporting_sources"]

            feat_id = FeatureNormalizer.generate_feature_id(
                project_id=project_id,
                feature_type=primary.feature_type.value,
                normalized_text=norm_text,
            )

            final_features.append(
                TechnicalFeature(
                    project_id=project_id,
                    feature_id=feat_id,
                    feature_type=primary.feature_type,
                    feature_text=primary.feature_text,
                    normalized_text=norm_text,
                    source_chunk_id=primary.source_chunk_id,
                    source_reference=primary.source_reference,
                    section=primary.section,
                    page_number=primary.page_number,
                    claim_number=primary.claim_number,
                    evidence_span_start=primary.evidence_span_start,
                    evidence_span_end=primary.evidence_span_end,
                    extraction_method=primary.extraction_method,
                    confidence=group["max_confidence"],
                    supporting_sources=sources,
                )
            )

        # Stable sort: feature_type ascending, then feature_id ascending
        final_features.sort(key=lambda f: (f.feature_type.value, f.feature_id))

        metadata = ExtractionMetadata(
            number_of_input_chunks=len(chunks),
            number_of_raw_candidates=len(raw_candidates),
            number_of_validated_features=len(final_features),
            number_of_duplicates_merged=duplicates_merged_count,
            extraction_method=method,
            processing_status="completed",
        )

        return FeatureExtractionResponse(
            project_id=project_id,
            features=final_features,
            total_features=len(final_features),
            extraction_metadata=metadata,
        )


# Global singleton instance for FastAPI dependency injection
patent_feature_service = PatentFeatureService()
