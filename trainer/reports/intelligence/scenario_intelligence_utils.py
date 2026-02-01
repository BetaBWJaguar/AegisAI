from typing import Dict, List, Any


def find_best_scenario(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    return min(scenarios, key=lambda s: s["total_cost"])


def find_worst_scenario(scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    return max(scenarios, key=lambda s: s["total_cost"])


def calculate_cost_difference(base_total: float, scenario_total: float) -> Dict[str, float]:
    diff = scenario_total - base_total
    pct = (diff / base_total * 100) if base_total > 0 else 0.0
    return {"difference": diff, "percentage": pct}


def find_dominant_cost_component(breakdown: Dict[str, Any]) -> str:
    components = {
        "Hardware": breakdown.get("hardware_cost", 0),
        "Storage": breakdown.get("storage_cost", 0),
        "Token": breakdown.get("token_cost", 0),
        "Energy": breakdown.get("energy_cost", 0),
    }
    return max(components, key=components.get)


def generate_scenario_comment(name: str, diff_info: Dict[str, float]) -> str:
    diff = diff_info["difference"]
    pct = diff_info["percentage"]

    if diff < 0:
        return f"{name} reduces total cost by {abs(pct):.1f}% compared to baseline."
    elif diff > 0:
        return f"{name} increases total cost by {pct:.1f}% compared to baseline."
    return f"{name} has the same total cost as the baseline."
