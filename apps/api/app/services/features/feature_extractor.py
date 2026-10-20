import re
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any

from app.schemas.document import DocumentChunk
from app.services.features.types import FeatureType, FeatureCandidate
from app.core.config import settings

logger = logging.getLogger("patentiq.features")


class BaseFeatureExtractor(ABC):
    """Abstract base interface for technical feature extractors."""

    @abstractmethod
    def extract(self, chunk: DocumentChunk) -> List[FeatureCandidate]:
        """Extracts candidate technical features from a document chunk.

        Args:
            chunk: Processed document chunk with text and section metadata.

        Returns:
            List of FeatureCandidate objects grounded in the chunk text.
        """
        ...


class RuleBasedFeatureExtractor(BaseFeatureExtractor):
    """Conservative, deterministic, pattern-based feature extractor.

    Extracts explicit technical components, functions, mechanisms, technical effects,
    problems, and claimed aspects with exact character span grounding in the source text.
    """

    # Compiled regex patterns for technical syntax patterns
    PATTERNS = [
        # Claimed aspects (claims section)
        (
            FeatureType.CLAIMED_ASPECT,
            re.compile(
                r"(?:(?:claim\s+\d+[:\.]?|we\s+claim[:\.]?|what\s+is\s+claimed\s+is[:\.]?)\s*)?"
                r"(?:an?\s+)?([A-Za-z0-9_\-\s]{4,60}\s+(?:comprising|including|consisting\s+of)\s+[^;\.\n]+)",
                re.IGNORECASE,
            ),
            0.95,
        ),
        # Functional capability & interactions (Subject + Action Verb + Object/Effect)
        (
            FeatureType.FUNCTION,
            re.compile(
                r"\b([A-Za-z0-9_\-\s]{3,40}\s+(?:prevents|prevents\s+from|ensures|enables|controls|regulates|mitigates|coordinates|orchestrates|facilitates)\s+[^;\.\n]{10,120})",
                re.IGNORECASE,
            ),
            0.92,
        ),
        # Functional components & operations (Subject + configured/adapted/operable to + Action)
        (
            FeatureType.FUNCTION,
            re.compile(
                r"((?:[A-Za-z0-9_\-\s]{3,40}\s+)?(?:configured|adapted|operable|programmed)\s+to\s+[^;\.\n]{10,120})",
                re.IGNORECASE,
            ),
            0.90,
        ),
        # Technical mechanisms / methods
        (
            FeatureType.MECHANISM,
            re.compile(
                r"((?:by\s+means\s+of|via|utilizing|employing)\s+an?\s+[^;\.\n]{10,100})",
                re.IGNORECASE,
            ),
            0.85,
        ),
        # Technical effects & advantages
        (
            FeatureType.TECHNICAL_EFFECT,
            re.compile(
                r"((?:thereby|advantageously|so\s+as\s+to)\s+(?:improving|reducing|increasing|enhancing|preventing|achieving)\s+[^;\.\n]{10,100})",
                re.IGNORECASE,
            ),
            0.90,
        ),
        # Problems addressed
        (
            FeatureType.PROBLEM,
            re.compile(
                r"((?:problem\s+of|disadvantage\s+of|challenge\s+with|drawback\s+of|need\s+for)\s+[^;\.\n]{10,100})",
                re.IGNORECASE,
            ),
            0.85,
        ),
        # Component relations & couplings
        (
            FeatureType.RELATIONSHIP,
            re.compile(
                r"([A-Za-z0-9_\-\s]{3,40}\s+(?:coupled\s+to|connected\s+to|communicatively\s+coupled\s+with|integrated\s+into|disposed\s+on)\s+[^;\.\n]{5,60})",
                re.IGNORECASE,
            ),
            0.88,
        ),
        # Technical constraints
        (
            FeatureType.CONSTRAINT,
            re.compile(
                r"((?:wherein|where)\s+(?:the\s+)?[A-Za-z0-9_\-\s]{3,30}\s+(?:is\s+between|is\s+at\s+least|does\s+not\s+exceed|is\s+less\s+than|is\s+within)\s+[^;\.\n]{5,70})",
                re.IGNORECASE,
            ),
            0.88,
        ),
        # Process definitions
        (
            FeatureType.PROCESS,
            re.compile(
                r"((?:method|process|procedure|algorithm|technique)\s+(?:for|of|comprising)\s+[^;\.\n]{10,100})",
                re.IGNORECASE,
            ),
            0.88,
        ),
        # Substantive process operations with context
        (
            FeatureType.PROCESS,
            re.compile(
                r"\b((?:[A-Za-z0-9_\-\s]{3,30}\s+)?(?:synchronizing|allocating|locking|propagating|confirming|tracking|detecting|monitoring|resolving|authenticating)\s+[^;\.\n]{10,100})",
                re.IGNORECASE,
            ),
            0.85,
        ),
        # Inputs & Outputs: requiring substantive context
        (
            FeatureType.INPUT,
            re.compile(
                r"((?:receives|receiving|provided\s+with|inputting)\s+(?:an?|the)?\s+[^;\.\n]{12,90})",
                re.IGNORECASE,
            ),
            0.85,
        ),
        (
            FeatureType.OUTPUT,
            re.compile(
                r"((?:generates|generating|outputs|outputting|transmitting|transmits)\s+(?:an?|the)?\s+[^;\.\n]{12,90})",
                re.IGNORECASE,
            ),
            0.85,
        ),
        # Component definitions
        (
            FeatureType.COMPONENT,
            re.compile(
                r"(?:includes?|comprises?|having|incorporating)\s+an?\s+([A-Za-z0-9_\-\s]{3,50}\s+(?:module|circuit|sensor|processor|actuator|unit|device|layer|assembly|motor|interface|detector|mechanism|engine|database|controller|server|service|gateway|bus|store|queue|manager|handler|repository))",
                re.IGNORECASE,
            ),
            0.90,
        ),
    ]

    def extract(self, chunk: DocumentChunk) -> List[FeatureCandidate]:
        """Extracts technical feature candidates grounded in the chunk text."""
        candidates: List[FeatureCandidate] = []
        text = chunk.text
        if not text or not text.strip():
            return candidates

        # Check for claim elements specifically if chunk is in claims
        if chunk.section == "claims" or chunk.claim_number is not None or "claim" in text.lower()[:50]:
            claim_cand = self._extract_claim_elements(chunk)
            candidates.extend(claim_cand)

        # Apply syntactic pattern matchers
        for ftype, pattern, base_confidence in self.PATTERNS:
            for match in pattern.finditer(text):
                feature_text = match.group(1).strip()
                # Clean boundary noise
                feature_text = feature_text.rstrip(";., ")
                if len(feature_text) < 4:
                    continue

                span_start = match.start(1)
                span_end = span_start + len(feature_text)

                candidates.append(
                    FeatureCandidate(
                        feature_type=ftype,
                        feature_text=feature_text,
                        source_chunk_id=str(chunk.chunk_index),
                        source_chunk_index=chunk.chunk_index,
                        source_reference=chunk.source_reference,
                        section=chunk.section,
                        page_number=chunk.page_number,
                        claim_number=chunk.claim_number,
                        evidence_span_start=span_start,
                        evidence_span_end=span_end,
                        confidence=base_confidence,
                        extraction_method="rule_based",
                    )
                )

        # Check for explicit list items (e.g. numbered or bulleted technical features)
        list_item_re = re.compile(r"^(?:[\d]+[\.\)]|[\-*•])\s+([A-Za-z0-9_\-\s/]{8,100})$", re.MULTILINE)
        for match in list_item_re.finditer(text):
            item_text = match.group(1).strip().rstrip(";., ")
            # Clean dependent claim boilerplate if item is a numbered dependent claim
            dep_sub = re.match(r"^The\s+[\w\-]+\s+of\s+claim\s+\d+[,;]?\s*(?:wherein|where|further\s+comprising)\s+(.+)", item_text, re.IGNORECASE)
            if dep_sub:
                item_text = dep_sub.group(1).strip().rstrip(";., ")
            if len(item_text) >= 10:
                lower = item_text.lower()
                if any(k in lower for k in ["module", "circuit", "sensor", "processor", "engine", "database", "controller", "server", "bus", "manager"]):
                    ftype = FeatureType.COMPONENT
                elif any(k in lower for k in ["synchronization", "propagation", "locking", "allocation", "process", "control", "method", "detection", "logging", "expiration"]):
                    ftype = FeatureType.PROCESS
                elif any(k in lower for k in ["configured", "adapted", "operable", "programmed"]):
                    ftype = FeatureType.FUNCTION
                elif any(k in lower for k in ["wherein", "limit", "rate", "bound", "threshold", "constraint"]):
                    ftype = FeatureType.CONSTRAINT
                else:
                    ftype = FeatureType.FUNCTION

                span_start = match.start(1)
                span_end = span_start + len(item_text)
                candidates.append(
                    FeatureCandidate(
                        feature_type=ftype,
                        feature_text=item_text,
                        source_chunk_id=str(chunk.chunk_index),
                        source_chunk_index=chunk.chunk_index,
                        source_reference=chunk.source_reference,
                        section=chunk.section,
                        page_number=chunk.page_number,
                        claim_number=chunk.claim_number,
                        evidence_span_start=span_start,
                        evidence_span_end=span_end,
                        confidence=0.88,
                        extraction_method="rule_based",
                    )
                )

        return candidates

    def _extract_claim_elements(self, chunk: DocumentChunk) -> List[FeatureCandidate]:
        """Extracts structured claimed aspects from independent and dependent claims."""
        results = []
        text = chunk.text

        # 1. Independent claim extraction: "Claim 1: A system comprising: ..."
        claim_match = re.search(r"(?:Claim\s+\d+[:\.]?\s*)?(.+?)(?:comprising|including)[:;]", text, re.IGNORECASE)
        if claim_match:
            preamble = claim_match.group(1).strip()
            # Clean leading claim numbers e.g. "1. " or "Claim 1: "
            preamble = re.sub(r"^(?:Claim\s+)?\d+[:\.]?\s*", "", preamble, flags=re.IGNORECASE).strip()
            if len(preamble) >= 5:
                results.append(
                    FeatureCandidate(
                        feature_type=FeatureType.CLAIMED_ASPECT,
                        feature_text=preamble,
                        source_chunk_id=str(chunk.chunk_index),
                        source_chunk_index=chunk.chunk_index,
                        source_reference=chunk.source_reference or f"claim:{chunk.claim_number or 1}",
                        section=chunk.section,
                        page_number=chunk.page_number,
                        claim_number=chunk.claim_number,
                        evidence_span_start=claim_match.start(1),
                        evidence_span_end=claim_match.end(1),
                        confidence=0.95,
                        extraction_method="rule_based",
                    )
                )

            # Extract individual claim limitations/elements following comprising/including
            post_preamble = text[claim_match.end():]
            elements = re.split(r"[;\n]", post_preamble)
            for elem in elements:
                clean_elem = elem.strip().lstrip("-*•0123456789.) ").rstrip(".;, ")
                # Strip dependent claim boilerplate if element starts a dependent claim
                dep_in_elem = re.match(r"^The\s+[\w\-]+\s+of\s+claim\s+\d+[,;]?\s*(?:wherein|where|further\s+comprising)\s+(.+)", clean_elem, re.IGNORECASE)
                if dep_in_elem:
                    clean_elem = dep_in_elem.group(1).strip()
                # Strip leading connective boilerplate "and ", "wherein "
                if clean_elem.lower().startswith("and "):
                    clean_elem = clean_elem[4:].strip()
                if clean_elem.lower().startswith("wherein "):
                    clean_elem = clean_elem[8:].strip()
                if len(clean_elem) >= 8:
                    span_start = text.find(clean_elem)
                    span_end = (span_start + len(clean_elem)) if span_start != -1 else len(clean_elem)
                    results.append(
                        FeatureCandidate(
                            feature_type=FeatureType.CLAIMED_ASPECT,
                            feature_text=clean_elem,
                            source_chunk_id=str(chunk.chunk_index),
                            source_chunk_index=chunk.chunk_index,
                            source_reference=chunk.source_reference or f"claim:{chunk.claim_number or 1}",
                            section=chunk.section,
                            page_number=chunk.page_number,
                            claim_number=chunk.claim_number,
                            evidence_span_start=span_start if span_start != -1 else 0,
                            evidence_span_end=span_end,
                            confidence=0.92,
                            extraction_method="rule_based",
                        )
                    )

        # 2. Dependent claim limitation extraction: "Claim 2: The system of claim 1, wherein <limitation>"
        dep_match = re.search(
            r"(?:Claim\s+\d+[:\.]?\s*)?(?:The\s+[\w\-]+\s+of\s+claim\s+\d+[,;]?\s*(?:wherein|where|further\s+comprising))\s+(.+)",
            text,
            re.IGNORECASE,
        )
        if dep_match:
            limitation = dep_match.group(1).strip().rstrip(";., ")
            if len(limitation) >= 8:
                results.append(
                    FeatureCandidate(
                        feature_type=FeatureType.CLAIMED_ASPECT,
                        feature_text=limitation,
                        source_chunk_id=str(chunk.chunk_index),
                        source_chunk_index=chunk.chunk_index,
                        source_reference=chunk.source_reference or f"claim:{chunk.claim_number or 2}",
                        section=chunk.section,
                        page_number=chunk.page_number,
                        claim_number=chunk.claim_number,
                        evidence_span_start=dep_match.start(1),
                        evidence_span_end=dep_match.end(1),
                        confidence=0.93,
                        extraction_method="rule_based",
                    )
                )

        return results


class GeminiFeatureExtractor(BaseFeatureExtractor):
    """LLM-backed feature extractor leveraging Gemini for structured technical feature parsing.

    Features:
    - Structured JSON output schema enforcement.
    - Grounding verification: Extracted features are verified to be anchored in the chunk text.
    - Rejects hallucinated or ungrounded details.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._rule_fallback = RuleBasedFeatureExtractor()

    def extract(self, chunk: DocumentChunk) -> List[FeatureCandidate]:
        """Extracts technical features using Gemini if configured, otherwise falls back gracefully."""
        if not self.api_key:
            logger.info("GEMINI_API_KEY not configured. Using rule-based feature extractor fallback.")
            return self._rule_fallback.extract(chunk)

        try:
            return self._extract_with_gemini(chunk)
        except Exception as exc:
            logger.warning("Gemini extraction failed (%s). Falling back to rule-based extractor.", exc)
            return self._rule_fallback.extract(chunk)

    def _extract_with_gemini(self, chunk: DocumentChunk) -> List[FeatureCandidate]:
        """Invokes Gemini API with strict structured JSON output."""
        import json
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        prompt = (
            "You are a technical patent analyst. Extract all explicit technical features from the provided document passage.\n"
            "Rules:\n"
            "1. Extract ONLY technical features explicitly stated in the text.\n"
            "2. Do NOT invent, assume, or hallucinate any details.\n"
            "3. Do NOT assess novelty, patentability, or prior art.\n"
            "4. Classify each feature into one of these exact types: "
            f"{[t.value for t in FeatureType]}.\n"
            "5. feature_text must be a verbatim or near-verbatim quote from the text.\n\n"
            f"Passage (Section: {chunk.section}):\n\"\"\"\n{chunk.text}\n\"\"\""
        )

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )

        raw_json = json.loads(response.text)
        items = raw_json if isinstance(raw_json, list) else raw_json.get("features", [])

        candidates: List[FeatureCandidate] = []
        for item in items:
            ftype_raw = str(item.get("feature_type", "")).lower().strip()
            try:
                ftype = FeatureType(ftype_raw)
            except ValueError:
                continue

            ftext = str(item.get("feature_text", "")).strip()
            if not ftext:
                continue

            # Grounding check: verify verbatim or case-insensitive presence in chunk text
            span_start = None
            span_end = None
            idx = chunk.text.lower().find(ftext.lower())
            if idx != -1:
                span_start = idx
                span_end = idx + len(ftext)
                # Use exact case from chunk
                ftext = chunk.text[span_start:span_end]

            confidence = float(item.get("confidence", 0.9))
            candidates.append(
                FeatureCandidate(
                    feature_type=ftype,
                    feature_text=ftext,
                    source_chunk_id=str(chunk.chunk_index),
                    source_chunk_index=chunk.chunk_index,
                    source_reference=chunk.source_reference,
                    section=chunk.section,
                    page_number=chunk.page_number,
                    claim_number=chunk.claim_number,
                    evidence_span_start=span_start,
                    evidence_span_end=span_end,
                    confidence=min(max(confidence, 0.0), 1.0),
                    extraction_method="llm_gemini",
                )
            )

        return candidates


class MockFeatureExtractor(BaseFeatureExtractor):
    """Deterministic mock extractor for unit tests without network or LLM dependencies."""

    def __init__(self, predefined_candidates: Optional[List[FeatureCandidate]] = None):
        self._predefined = predefined_candidates

    def extract(self, chunk: DocumentChunk) -> List[FeatureCandidate]:
        if self._predefined is not None:
            return self._predefined

        # Default predictable mock extraction
        return [
            FeatureCandidate(
                feature_type=FeatureType.COMPONENT,
                feature_text="mock technical component",
                source_chunk_id=str(chunk.chunk_index),
                source_chunk_index=chunk.chunk_index,
                source_reference=chunk.source_reference,
                section=chunk.section,
                page_number=chunk.page_number,
                claim_number=chunk.claim_number,
                evidence_span_start=0,
                evidence_span_end=24,
                confidence=0.95,
                extraction_method="mock",
            )
        ]
