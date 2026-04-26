# -*- coding: utf-8 -*-
from typing import Dict, List, Optional, Tuple
from datetime import datetime

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def validate_penalty_data(penalty: Dict) -> Tuple[bool, Optional[str]]:
    if "risk_level" not in penalty:
        return False, "Missing required field: risk_level"
    if penalty["risk_level"] not in VALID_RISK_LEVELS:
        return False, f"Invalid risk_level. Must be one of: {list(VALID_RISK_LEVELS)}"
    if "confidence" in penalty and not (isinstance(penalty["confidence"], (int, float)) and 0 <= penalty["confidence"] <= 1):
        return False, "confidence must be a number between 0 and 1"
    if "category" in penalty and (not isinstance(penalty["category"], str) or not penalty["category"].strip()):
        return False, "category must be a non-empty string"
    return True, None


def validate_penalties_list(penalties: List[Dict]) -> Tuple[bool, Optional[str], List[Dict]]:
    if not isinstance(penalties, list) or not penalties:
        return False, "penalties must be a non-empty list", []
    
    for idx, penalty in enumerate(penalties):
        is_valid, error_message = validate_penalty_data(penalty)
        if not is_valid:
            return False, f"Penalty at index {idx}: {error_message}", []
    
    return True, None, penalties


def format_penalty_response(total_duration: int, penalties_count: int, processed_at: Optional[str] = None) -> Dict:
    return {
        "success": True,
        "data": {
            "total_duration_minutes": total_duration,
            "penalties_count": penalties_count,
            "processed_at": processed_at or datetime.utcnow().isoformat()
        }
    }


def filter_penalties_by_risk_level(penalties: List[Dict], risk_levels: List[str]) -> List[Dict]:
    if not penalties or not risk_levels:
        return []
    
    normalized_levels = {level.upper() for level in risk_levels if level.upper() in VALID_RISK_LEVELS}
    
    return [
        penalty for penalty in penalties
        if penalty.get("risk_level", "").upper() in normalized_levels
    ]


def sort_penalties_by_confidence(penalties: List[Dict], descending: bool = True) -> List[Dict]:
    if not penalties:
        return []
    
    return sorted(
        penalties,
        key=lambda p: p.get("confidence", 1.0),
        reverse=descending
    )


def aggregate_penalties_by_category(penalties: List[Dict]) -> Dict[str, Dict]:
    if not penalties:
        return {}
    
    aggregation = {}
    
    for penalty in penalties:
        category = penalty.get("category", "UNCATEGORIZED")
        confidence = penalty.get("confidence", 0.0)
        risk_level = penalty.get("risk_level", "").upper()
        
        if category not in aggregation:
            aggregation[category] = {
                "count": 0,
                "total_confidence": 0.0,
                "risk_levels": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            }
        
        aggregation[category]["count"] += 1
        aggregation[category]["total_confidence"] += confidence
        
        if risk_level in VALID_RISK_LEVELS:
            aggregation[category]["risk_levels"][risk_level] += 1
    
    for category_data in aggregation.values():
        if category_data["count"] > 0:
            category_data["avg_confidence"] = round(
                category_data["total_confidence"] / category_data["count"], 4
            )
        else:
            category_data["avg_confidence"] = 0.0
        del category_data["total_confidence"]
    
    return aggregation
