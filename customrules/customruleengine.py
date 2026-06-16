from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

from customrules.customrule import CustomRule
from customrules.customrule_action import CustomRuleAction
from customrules.customrule_severity import RuleSeverity
from customrules.customrule_type import CustomRuleType
from customrules.customrule_service_impl_utils import (
    apply_replacement,
    highlight_matches,
    test_pattern_dispatch,
)

logger = logging.getLogger(__name__)

__all__ = [
    "EngineVerdict",
    "RuleMatchResult",
    "EngineResult",
    "OnRuleTriggeredCallback",
    "EngineConfig",
    "CustomRuleEngine",
]


class EngineVerdict(str, Enum):
    CLEAN = "CLEAN"
    FLAGGED = "FLAGGED"
    BLOCKED = "BLOCKED"
    TRANSFORMED = "TRANSFORMED"


@dataclass
class RuleMatchResult:
    rule_id: str
    rule_name: str
    rule_type: str
    action: str
    priority: int
    match_count: int
    matches: List[dict]
    replace_text: Optional[str] = None
    highlighted_text: Optional[str] = None
    severity: str = "MEDIUM"
    scope: Optional[str] = None


@dataclass
class EngineResult:
    original_text: str
    processed_text: str
    verdict: EngineVerdict
    matched: bool
    triggered_rule_count: int
    triggered_rules: List[RuleMatchResult]
    highlighted_original: str
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict = field(default_factory=dict)
    max_severity: Optional[str] = None
    scope: Optional[str] = None


OnRuleTriggeredCallback = Callable[[CustomRule, RuleMatchResult], None]


@dataclass
class EngineConfig:
    stop_on_block: bool = True
    stop_on_first_match: bool = False
    default_mask: str = "***"
    redact_placeholder: str = "[REDACTED]"
    highlight_pre: str = "<<"
    highlight_post: str = ">>"


_TRANSFORM_ACTIONS = frozenset({
    CustomRuleAction.REPLACE.value,
    CustomRuleAction.MASK.value,
    CustomRuleAction.REDACT.value,
})


class CustomRuleEngine:

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        on_rule_triggered: Optional[OnRuleTriggeredCallback] = None,
    ) -> None:
        self._config = config or EngineConfig()
        self._on_rule_triggered = on_rule_triggered

    def evaluate(
        self,
        text: str,
        rules: List[CustomRule],
        scope: Optional[str] = None,
    ) -> EngineResult:
        if not text:
            return self._empty_result(text)

        active_rules = sorted(
            (
                r for r in rules
                if r.enabled
                and not r.is_expired()
                and not r.is_in_cooldown()
                and r.applies_to_scope(scope)
            ),
            key=lambda r: r.priority,
            reverse=True,
        )

        if not active_rules:
            return self._empty_result(text)

        current_text = text
        triggered_rules: List[RuleMatchResult] = []
        all_matches: List[dict] = []
        blocked = False

        for rule in active_rules:
            if blocked and self._config.stop_on_block:
                break

            matches = self._test_rule(rule, current_text)
            if matches is None:
                continue

            matches = self._filter_exceptions(rule, current_text, matches)
            if not matches:
                continue

            result = self._build_match_result(rule, matches)
            current_text, blocked = self._apply_action(
                rule, result, current_text, matches,
            )
            rule.record_hit()
            self._fire_callback(rule, result)

            triggered_rules.append(result)
            all_matches.extend(matches)

            if self._config.stop_on_first_match:
                break

        return EngineResult(
            original_text=text,
            processed_text=current_text,
            verdict=self._resolve_verdict(triggered_rules, blocked),
            matched=bool(triggered_rules),
            triggered_rule_count=len(triggered_rules),
            triggered_rules=triggered_rules,
            highlighted_original=highlight_matches(
                text, all_matches,
                self._config.highlight_pre,
                self._config.highlight_post,
            ),
            max_severity=self._resolve_max_severity(triggered_rules),
            scope=scope,
        )

    def evaluate_single(
        self, text: str, rule: CustomRule,
    ) -> Optional[RuleMatchResult]:
        if not rule.enabled:
            return None

        matches = self._test_rule(rule, text)
        if matches is None:
            return None

        result = self._build_match_result(rule, matches)
        rule.record_hit()
        self._fire_callback(rule, result)
        return result

    def test_pattern(
        self,
        pattern: str,
        rule_type: CustomRuleType,
        test_text: str,
        case_sensitive: bool = False,
    ) -> dict:
        flags = 0 if case_sensitive else re.IGNORECASE
        matches, error = test_pattern_dispatch(
            pattern, test_text, case_sensitive, flags, rule_type,
        )

        if error:
            return {"error": error, "matches": []}

        return {
            "pattern": pattern,
            "rule_type": rule_type.value,
            "test_text": test_text,
            "case_sensitive": case_sensitive,
            "match_count": len(matches),
            "matches": matches,
            "highlighted_text": highlight_matches(test_text, matches),
        }


    def _test_rule(
        self, rule: CustomRule, text: str,
    ) -> Optional[List[dict]]:
        flags = 0 if rule.case_sensitive else re.IGNORECASE
        matches, error = test_pattern_dispatch(
            rule.pattern, text, rule.case_sensitive, flags, rule.rule_type,
        )
        if error:
            logger.warning(
                "Rule %s (%s) produced an error: %s",
                rule.id, rule.name, error,
            )
            return None
        return matches or None

    @staticmethod
    def _build_match_result(
        rule: CustomRule, matches: List[dict],
    ) -> RuleMatchResult:
        return RuleMatchResult(
            rule_id=str(rule.id),
            rule_name=rule.name,
            rule_type=rule.rule_type.value,
            action=rule.action.value,
            priority=rule.priority,
            match_count=len(matches),
            matches=matches,
            severity=rule.severity.value,
            scope=rule.scope,
        )

    @staticmethod
    def _filter_exceptions(
        rule: CustomRule, text: str, matches: List[dict],
    ) -> List[dict]:
        if not rule.exceptions:
            return matches

        exception_spans: List[Tuple[int, int]] = []
        for exc_pattern in rule.exceptions:
            try:
                flags = 0 if rule.case_sensitive else re.IGNORECASE
                for m in re.finditer(exc_pattern, text, flags):
                    exception_spans.append((m.start(), m.end()))
            except re.error:
                logger.warning(
                    "Invalid exception pattern %r on rule %s", exc_pattern, rule.id,
                )

        if not exception_spans:
            return matches

        def _overlaps(match: dict) -> bool:
            ms, me = match["start"], match["end"]
            for es, ee in exception_spans:
                if ms < ee and es < me:
                    return True
            return False

        return [m for m in matches if not _overlaps(m)]

    def _fire_callback(
        self, rule: CustomRule, result: RuleMatchResult,
    ) -> None:
        if self._on_rule_triggered is not None:
            try:
                self._on_rule_triggered(rule, result)
            except Exception:
                logger.exception(
                    "on_rule_triggered callback failed for rule %s", rule.id,
                )

    def _apply_action(
        self,
        rule: CustomRule,
        result: RuleMatchResult,
        text: str,
        matches: List[dict],
    ) -> Tuple[str, bool]:
        action = rule.action
        blocked = action == CustomRuleAction.BLOCK

        if action == CustomRuleAction.REPLACE:
            replace_text = rule.replace_text or self._config.default_mask
            text = apply_replacement(text, matches, replace_text)
            result.replace_text = replace_text

        elif action == CustomRuleAction.MASK:
            text = apply_replacement(text, matches, self._config.default_mask)

        elif action == CustomRuleAction.REDACT:
            text = apply_replacement(text, matches, self._config.redact_placeholder)

        elif action in (CustomRuleAction.FLAG, CustomRuleAction.WARN):
            result.highlighted_text = highlight_matches(text, matches)

        elif action == CustomRuleAction.LOG:
            logger.info(
                "Rule %s (%s) matched %d time(s) in text.",
                rule.id, rule.name, len(matches),
            )

        return text, blocked

    @staticmethod
    def _resolve_verdict(
        triggered: List[RuleMatchResult], blocked: bool,
    ) -> EngineVerdict:
        if blocked:
            return EngineVerdict.BLOCKED
        if not triggered:
            return EngineVerdict.CLEAN
        if any(t.action in _TRANSFORM_ACTIONS for t in triggered):
            return EngineVerdict.TRANSFORMED
        return EngineVerdict.FLAGGED

    @staticmethod
    def _resolve_max_severity(
        triggered: List[RuleMatchResult],
    ) -> Optional[str]:
        if not triggered:
            return None
        best = RuleSeverity.highest(t.severity for t in triggered)
        return best.value if best else None

    @staticmethod
    def _empty_result(text: str) -> EngineResult:
        safe = text or ""
        return EngineResult(
            original_text=safe,
            processed_text=safe,
            verdict=EngineVerdict.CLEAN,
            matched=False,
            triggered_rule_count=0,
            triggered_rules=[],
            highlighted_original=safe,
        )
