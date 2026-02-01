from typing import Dict, List, Any

from trainer.reports.intelligence.scenario_intelligence_utils import (
    find_best_scenario,
    find_worst_scenario,
    calculate_cost_difference,
    find_dominant_cost_component,
    generate_scenario_comment
)


class ScenarioIntelligenceEngine:

    @staticmethod
    def analyze(breakdown: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:

        if not scenarios:
            return {
                "summary": "No scenarios were provided for comparative analysis.",
                "best_scenario": None,
                "worst_scenario": None,
                "dominant_cost_component": None,
                "scenario_insights": []
            }

        base_total = breakdown["total_cost"]

        best = find_best_scenario(scenarios)
        worst = find_worst_scenario(scenarios)
        dominant_component = find_dominant_cost_component(breakdown)

        insights = []

        for s in scenarios:
            diff_info = calculate_cost_difference(base_total, s["total_cost"])
            comment = generate_scenario_comment(s["scenario"], diff_info)
            insights.append(comment)

        summary = (
            f"The baseline training cost is primarily driven by {dominant_component.lower()} expenses. "
            f"The most cost-efficient scenario is '{best['scenario']}', "
            f"while '{worst['scenario']}' represents the highest total cost."
        )

        return {
            "summary": summary,
            "best_scenario": best["scenario"],
            "worst_scenario": worst["scenario"],
            "dominant_cost_component": dominant_component,
            "scenario_insights": insights
        }
