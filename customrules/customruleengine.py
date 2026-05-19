from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

from customrules.customrule import CustomRule
from customrules.customrule_action import CustomRuleAction
from customrules.customrule_type import CustomRuleType
from customrules.customrule_service_impl_utils import (
    apply_replacement,
    highlight_matches,
    test_pattern_dispatch,
)

logger = logging.getLogger(__name__)


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


@dataclass
class EngineResult:
    original_text: str
    processed_text: str
    verdict: EngineVerdict
    matched: bool
    triggered_rule_count: int
    triggered_rules: List[RuleMatchResult]
    highlighted_original: str
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict = field(default_factory=dict)


OnRuleTriggeredCallback = Callable[[CustomRule, RuleMatchResult], None]


@dataclass
class EngineConfig:
    stop_on_block: bool = True
    stop_on_first_match: bool = False
    default_mask: str = "***"
    redact_placeholder: str = "[REDACTED]"
    highlight_pre: str = "<<"
    highlight_post: str = ">>"


class CustomRuleEngine:

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        on_rule_triggered: Optional[OnRuleTriggeredCallback] = None,
    ) -> None:
        self._config = config or EngineConfig()
        self._on_rule_triggered = on_rule_triggered
        self._regex_cache: Dict[Tuple[str, int], re.Pattern] = {}

    def evaluate(self, text: str, rules: List[CustomRule]) -> EngineResult:
        if not text:
            return self._empty_result(text)

        active_rules = sorted(
            [r for r in rules if r.enabled],
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

            flags = 0 if rule.case_sensitive else re.IGNORECASE
            matches, error = test_pattern_dispatch(
                rule.pattern, current_text, rule.case_sensitive, flags, rule.rule_type,
            )

            if error:
                logger.warning(
                    "Rule %s (%s) produced an error: %s",
                    rule.id, rule.name, error,
                )
                continue

            if not matches:
                continue

            match_result = RuleMatchResult(
                rule_id=str(rule.id),
                rule_name=rule.name,
                rule_type=rule.rule_type.value,
                action=rule.action.value,
                priority=rule.priority,
                match_count=len(matches),
                matches=matches,
            )

            current_text, blocked = self._apply_action(
                rule, match_result, current_text, matches,
            )

            rule.record_hit()

            if self._on_rule_triggered is not None:
                try:
                    self._on_rule_triggered(rule, match_result)
                except Exception:
                    logger.exception(
                        "on_rule_triggered callback failed for rule %s", rule.id,
                    )

            triggered_rules.append(match_result)
            all_matches.extend(matches)

            if self._config.stop_on_first_match:
                break

        verdict = self._resolve_verdict(triggered_rules, blocked)

        highlighted_original = highlight_matches(
            text, all_matches,
            self._config.highlight_pre,
            self._config.highlight_post,
        )

        return EngineResult(
            original_text=text,
            processed_text=current_text,
            verdict=verdict,
            matched=len(triggered_rules) > 0,
            triggered_rule_count=len(triggered_rules),
            triggered_rules=triggered_rules,
            highlighted_original=highlighted_original,
        )

    def evaluate_single(
        self, text: str, rule: CustomRule,
    ) -> Optional[RuleMatchResult]:
        if not rule.enabled:
            return None

        flags = 0 if rule.case_sensitive else re.IGNORECASE
        matches, error = test_pattern_dispatch(
            rule.pattern, text, rule.case_sensitive, flags, rule.rule_type,
        )

        if error or not matches:
            return None

        result = RuleMatchResult(
            rule_id=str(rule.id),
            rule_name=rule.name,
            rule_type=rule.rule_type.value,
            action=rule.action.value,
            priority=rule.priority,
            match_count=len(matches),
            matches=matches,
        )

        rule.record_hit()

        if self._on_rule_triggered is not None:
            try:
                self._on_rule_triggered(rule, result)
            except Exception:
                logger.exception(
                    "on_rule_triggered callback failed for rule %s", rule.id,
                )

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

        highlighted = highlight_matches(test_text, matches)

        return {
            "pattern": pattern,
            "rule_type": rule_type.value,
            "test_text": test_text,
            "case_sensitive": case_sensitive,
            "match_count": len(matches),
            "matches": matches,
            "highlighted_text": highlighted,
        }

    def _apply_action(
        self,
        rule: CustomRule,
        result: RuleMatchResult,
        text: str,
        matches: List[dict],
    ) -> Tuple[str, bool]:
        blocked = False

        if rule.action == CustomRuleAction.BLOCK:
            blocked = True

        elif rule.action == CustomRuleAction.REPLACE:
            replace_text = rule.replace_text or self._config.default_mask
            text = apply_replacement(text, matches, replace_text)
            result.replace_text = replace_text

        elif rule.action == CustomRuleAction.MASK:
            text = apply_replacement(text, matches, self._config.default_mask)

        elif rule.action == CustomRuleAction.REDACT:
            text = apply_replacement(text, matches, self._config.redact_placeholder)

        elif rule.action in (CustomRuleAction.FLAG, CustomRuleAction.WARN):
            result.highlighted_text = highlight_matches(text, matches)

        elif rule.action == CustomRuleAction.LOG:
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

        transform_actions = {
            CustomRuleAction.REPLACE.value,
            CustomRuleAction.MASK.value,
            CustomRuleAction.REDACT.value,
        }
        if any(t.action in transform_actions for t in triggered):
            return EngineVerdict.TRANSFORMED

        return EngineVerdict.FLAGGED

    @staticmethod
    def _empty_result(text: str) -> EngineResult:
        return EngineResult(
            original_text=text or "",
            processed_text=text or "",
            verdict=EngineVerdict.CLEAN,
            matched=False,
            triggered_rule_count=0,
            triggered_rules=[],
            highlighted_original=text or "",
        )
