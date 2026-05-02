# -*- coding: utf-8 -*-
from typing import Dict, List, Optional, Tuple
from datetime import datetime

VALID_RISK_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})


def _get_readable_duration(total_minutes: int) -> str:
    if total_minutes <= 0:
        return "0 minutes"

    parts = []

    if total_minutes >= 1440:
        days = total_minutes // 1440
        parts.append(f"{days} day{'s' if days > 1 else ''}")
        total_minutes %= 1440

    if total_minutes >= 60:
        hours = total_minutes // 60
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        total_minutes %= 60

    if total_minutes > 0:
        parts.append(f"{total_minutes} minute{'s' if total_minutes > 1 else ''}")

    return " ".join(parts)


def validate_penalty_data(penalty: Dict) -> Tuple[bool, Optional[str]]:
    risk_level = penalty.get("risk_level")

    if not risk_level:
        return False, "Missing required field: risk_level"

    if risk_level not in VALID_RISK_LEVELS:
        return False, f"Invalid risk_level. Must be one of: {list(VALID_RISK_LEVELS)}"

    confidence = penalty.get("confidence")
    if confidence is not None and not (0 <= confidence <= 1):
        return False, "confidence must be a number between 0 and 1"

    category = penalty.get("category")
    if category is not None and (not isinstance(category, str) or not category.strip()):
        return False, "category must be a non-empty string"

    return True, None


def validate_penalties_list(penalties: List[Dict]) -> Tuple[bool, Optional[str], List[Dict]]:
    if not penalties:
        return False, "penalties must be a non-empty list", []

    get = validate_penalty_data
    for idx, penalty in enumerate(penalties):
        is_valid, error_message = get(penalty)
        if not is_valid:
            return False, f"Penalty at index {idx}: {error_message}", []

    return True, None, penalties


def format_penalty_response(total_duration: int, penalties_count: int, processed_at: Optional[str] = None) -> Dict:
    return {
        "success": True,
        "data": {
            "total_duration_minutes": total_duration,
            "readable_duration": _get_readable_duration(total_duration),
            "penalties_count": penalties_count,
            "processed_at": processed_at or datetime.utcnow().isoformat()
        }
    }


def filter_penalties_by_risk_level(penalties: List[Dict], risk_levels: List[str]) -> List[Dict]:
    if not penalties or not risk_levels:
        return []

    normalized_levels = frozenset(level.upper() for level in risk_levels)
    has_invalid = normalized_levels - VALID_RISK_LEVELS
    if has_invalid:
        normalized_levels = normalized_levels & VALID_RISK_LEVELS

    get = Dict.get
    return [p for p in penalties if get(p, "risk_level", "") in normalized_levels]


def sort_penalties_by_confidence(penalties: List[Dict], descending: bool = True) -> List[Dict]:
    if not penalties:
        return []

    get = Dict.get
    return sorted(penalties, key=lambda p: get(p, "confidence", 1.0), reverse=descending)


def aggregate_penalties_by_category(penalties: List[Dict]) -> Dict[str, Dict]:
    if not penalties:
        return {}

    get = Dict.get
    aggregation = {}
    risk_levels_template = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for penalty in penalties:
        category = get(penalty, "category", "UNCATEGORIZED")
        confidence = get(penalty, "confidence", 0.0)
        risk_level = get(penalty, "risk_level", "")

        if category in aggregation:
            cat_data = aggregation[category]
            cat_data[0] += 1
            cat_data[1] += confidence
            if risk_level in VALID_RISK_LEVELS:
                cat_data[2][risk_level] += 1
        else:
            risk_copy = risk_levels_template.copy()
            if risk_level in VALID_RISK_LEVELS:
                risk_copy[risk_level] = 1
            aggregation[category] = [1, confidence, risk_copy]

    result = {}
    for category, (count, total_conf, risk_levels) in aggregation.items():
        result[category] = {
            "count": count,
            "avg_confidence": round(total_conf / count, 4) if count else 0.0,
            "risk_levels": risk_levels
        }

    return result