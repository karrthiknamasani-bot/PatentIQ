import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings
from app.services.explanation.types import (
    GroundedContext,
    GroundedExplanation,
    PriorArtFinding,
    DimensionExplanation,
    EvidenceHighlight,
)
from app.services.explanation.prompt_builder import SYSTEM_PROMPT, build_grounded_prompt

logger = logging.getLogger("patentiq.explanation.gemini_client")


class BaseExplanationProvider(ABC):
    """Abstract interface for grounded explanation providers."""

    @abstractmethod
    async def generate_explanation(self, context: GroundedContext) -> GroundedExplanation:
        """Generate structured grounded explanation from context."""
        pass


class GeminiExplanationProvider(BaseExplanationProvider):
    """Production provider using Google Gemini 3.1 Pro Preview REST API via httpx."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_EXPLANATION_MODEL
        self.timeout = timeout or settings.GEMINI_TIMEOUT_SECONDS

    def _sanitize_error(self, message: str) -> str:
        """Strip API key from error strings to prevent credential exposure."""
        if self.api_key:
            return message.replace(self.api_key, "[REDACTED_API_KEY]")
        return message

    async def generate_explanation(self, context: GroundedContext) -> GroundedExplanation:
        """Call Gemini REST API with structured prompt and parse JSON output."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        user_prompt = build_grounded_prompt(context)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    sanitized_err = self._sanitize_error(response.text)
                    if response.status_code == 429:
                        logger.warning("Gemini API quota exhausted (status 429). Immediate fallback without retries.")
                    else:
                        logger.error("Gemini API returned error status %d: %s", response.status_code, sanitized_err)
                    raise RuntimeError(f"Gemini API error (status {response.status_code}): {sanitized_err}")


                resp_data = response.json()
                candidates = resp_data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini API returned empty candidate list")

                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if not raw_text:
                    raise RuntimeError("Gemini API returned empty response content")

                # Strip potential markdown formatting if returned
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("`json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("`"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("`"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                parsed_json = json.loads(cleaned_text)
                return GroundedExplanation.model_validate(parsed_json)

        except httpx.TimeoutException as e:
            logger.error("Gemini API call timed out after %s seconds", self.timeout)
            raise TimeoutError(f"Gemini API request timed out after {self.timeout}s")
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini response as JSON: %s", e)
            raise ValueError(f"Malformed JSON from Gemini: {e}")
        except Exception as e:
            logger.error("Gemini explanation generation failed: %s", self._sanitize_error(str(e)))
            raise RuntimeError(self._sanitize_error(str(e)))


class MockExplanationProvider(BaseExplanationProvider):
    """Deterministic mock provider for offline testing and controlled simulation."""

    def __init__(
        self,
        custom_explanation: Optional[GroundedExplanation] = None,
        should_fail: bool = False,
        failure_error: Optional[Exception] = None,
    ):
        self.custom_explanation = custom_explanation
        self.should_fail = should_fail
        self.failure_error = failure_error or RuntimeError("Simulated Gemini provider failure")

    async def generate_explanation(self, context: GroundedContext) -> GroundedExplanation:
        """Return pre-configured or dynamically synthesized valid explanation."""
        if self.should_fail:
            raise self.failure_error

        if self.custom_explanation is not None:
            return self.custom_explanation

        # Deterministically synthesize an explanation that perfectly mirrors context
        evidence_ids = [item.evidence_id for item in context.evidence_items]
        primary_eids = evidence_ids[:2] if evidence_ids else []

        prior_art_findings: List[PriorArtFinding] = []
        evidence_highlights: List[EvidenceHighlight] = []

        for item in context.evidence_items[:3]:
            prior_art_findings.append(
                PriorArtFinding(
                    statement=f"Prior-art document {item.patent_number} describes {item.text[:60]}...",
                    evidence_ids=[item.evidence_id],
                )
            )
            evidence_highlights.append(
                EvidenceHighlight(
                    feature_id=item.feature_id,
                    patent_number=item.patent_number,
                    relationship=item.relationship,
                    mapping_confidence=item.mapping_confidence,
                    evidence_id=item.evidence_id,
                    relevance_explanation=f"Exhibits {item.relationship} correspondence with feature {item.feature_id}.",
                )
            )

        dimension_explanations: List[DimensionExplanation] = []
        for dim_name, ds in context.dimension_scores.items():
            dim_eids = primary_eids if dim_name in {"novelty", "prior_art_overlap", "technical_differentiation"} else []
            dimension_explanations.append(
                DimensionExplanation(
                    dimension=dim_name,
                    score=ds.score,
                    explanation=f"Dimension {dim_name} evaluated to {ds.score:.4f}. {ds.rationale}",
                    evidence_ids=dim_eids,
                )
            )

        return GroundedExplanation(
            executive_summary=f"Assessment indicates {context.category_display} with a readiness score of {context.readiness_score:.4f} ({context.readiness_percentage:.1f}%).",
            invention_summary=f"Invention disclosure contains {len(context.features)} structured technical features in project {context.project_id}.",
            key_technical_features=[f.feature_text for f in context.features[:4]],
            prior_art_findings=prior_art_findings,
            dimension_explanations=dimension_explanations,
            differentiation_analysis="Evaluation against candidate evidence shows distinct structural and functional characteristics.",
            evidence_highlights=evidence_highlights,
            uncertainty_explanation=f"Active uncertainty indicators: {', '.join(context.uncertainty_flags) if context.uncertainty_flags else 'None'}.",
            limitations=[
                "Assessment is bounded by the retrieved prior-art candidate corpus.",
                "Does not evaluate legal validity, novelty grants, or infringement.",
            ],
            conclusion=f"The invention demonstrates {context.category_display} based on current technical evidence.",
            evidence_references=evidence_ids,
            readiness_score=context.readiness_score,
            readiness_percentage=context.readiness_percentage,
            readiness_category=context.readiness_category,
            confidence_score=context.confidence_score,
        )
