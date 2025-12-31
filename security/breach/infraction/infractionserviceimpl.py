from security.breach.actions.actiondecision import ActionDecision
from security.breach.actions.actionpolicy import DoxxingActionPolicy
from security.breach.doxxing_detector import DoxxingDetector
from security.breach.infraction.infraction_result import InfractionResult
from security.breach.infraction.infractionservice import InfractionService


class InfractionServiceImpl(InfractionService):

    RISK_LEVELS = [
        ("CRITICAL", 2.40),
        ("HIGH", 1.80),
        ("MEDIUM", 1.20),
        ("LOW", 0.00),
    ]

    def analyze(self, text: str) -> InfractionResult:
        explanation = DoxxingDetector.explain(text)

        score = explanation["score"]
        is_doxxing = explanation["is_doxxing"]

        risk_tier = self._resolve_risk_tier(score, explanation)

        decision = DoxxingActionPolicy.decide(risk_tier)

        return InfractionResult(
            is_violation=is_doxxing,
            risk_tier=risk_tier,
            decision=decision,
            score=score,
            details=explanation
        )

    def _resolve_risk_tier(self, score: float, explain: dict) -> str:
        if explain.get("hard_trigger"):
            return "CRITICAL"

        for tier, threshold in self.RISK_LEVELS:
            if score >= threshold:
                return tier

        return "LOW"

    def analyze_risk(self, text: str) -> tuple[str, float, bool]:
        r = self.analyze(text)
        return r.risk_tier, r.score, r.is_violation

    def decide_action(self, text: str) -> ActionDecision:
        return self.analyze(text).decision

