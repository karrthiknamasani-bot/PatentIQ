from typing import Tuple
from app.services.readiness.types import ReadinessCategory, READINESS_CATEGORY_DISPLAY


def determine_readiness_category(
    score: float,
    threshold_moderate: float = 0.40,
    threshold_high: float = 0.70,
) -> Tuple[ReadinessCategory, str]:
    """Map continuous readiness score into decision-support category tiers.
    
    Category Tiers:
    - Low:      [0.00, threshold_moderate) -> Low early-stage patent readiness
    - Moderate: [threshold_moderate, threshold_high) -> Moderate early-stage patent readiness
    - High:     [threshold_high, 1.00] -> High early-stage patent readiness
    """
    if score >= threshold_high:
        cat = ReadinessCategory.HIGH
    elif score >= threshold_moderate:
        cat = ReadinessCategory.MODERATE
    else:
        cat = ReadinessCategory.LOW

    return cat, READINESS_CATEGORY_DISPLAY[cat]
