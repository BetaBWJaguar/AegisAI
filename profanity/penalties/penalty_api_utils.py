# -*- coding: utf-8 -*-
from typing import Dict, List, Optional
from datetime import datetime


def validate_penalty_data(penalty: Dict) -> tuple[bool, Optional[str]]:
    required_fields = ["risk_level"]
    
    for field in required_fields:
        if field not in penalty:
            return False, f"Missing required field: {field}"
    
    valid_risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if penalty.get("risk_level") not in valid_risk_levels:
        return False, f"Invalid risk_level. Must be one of: {valid_risk_levels}"
    
    if "confidence" in penalty:
        confidence = penalty["confidence"]
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            return False, "confidence must be a number between 0 and 1"
    
    if "category" in penalty:
        category = penalty["category"]
        if not isinstance(category, str) or not category.strip():
            return False, "category must be a non-empty string"
    
    return True, None


def validate_penalties_list(penalties: List[Dict]) -> tuple[bool, Optional[str], List[Dict]]:
    if not isinstance(penalties, list):
        return False, "penalties must be a list", []
    
    if not penalties:
        return False, "penalties list cannot be empty", []
    
    valid_penalties = []
    
    for idx, penalty in enumerate(penalties):
        is_valid, error_message = validate_penalty_data(penalty)
        if not is_valid:
            return False, f"Penalty at index {idx}: {error_message}", []
        valid_penalties.append(penalty)
    
    return True, None, valid_penalties


def format_penalty_response(
    total_duration: int,
    penalties_count: int,
    processed_at: Optional[str] = None
) -> Dict:
    if processed_at is None:
        processed_at = datetime.utcnow().isoformat()
    
    return {
        "success": True,
        "data": {
            "total_duration_minutes": total_duration,
            "penalties_count": penalties_count,
            "processed_at": processed_at
        }
    }
