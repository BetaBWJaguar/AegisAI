import difflib
import fnmatch
import re
from typing import List, Optional, Tuple

from customrules.customrule_type import CustomRuleType


def test_pattern_dispatch(
    pattern: str, test_text: str, case_sensitive: bool, flags: int, rt: CustomRuleType
) -> Tuple[List[dict], Optional[str]]:
    handlers = {
        CustomRuleType.REGEX: test_regex_match,
        CustomRuleType.KEYWORD: test_keyword_match,
        CustomRuleType.WILDCARD: test_wildcard_match,
        CustomRuleType.PATTERN: test_pattern_match,
        CustomRuleType.EXACT: test_exact_match,
        CustomRuleType.DYNAMIC: test_dynamic_match,
        CustomRuleType.SEMANTIC: test_semantic_match,
    }

    handler = handlers.get(rt)
    if handler is None:
        return [], f"Test not supported for rule_type: {rt.value}"
    return handler(pattern, test_text, case_sensitive, flags)




def test_regex_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    try:
        compiled = re.compile(pattern, flags)
        matches = [
            {"match": m.group(), "start": m.start(), "end": m.end()}
            for m in compiled.finditer(test_text)
        ]
        return matches, None
    except re.error as e:
        return [], f"Invalid regex: {e}"


def test_keyword_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    search_text = test_text if case_sensitive else test_text.lower()
    search_pattern = pattern if case_sensitive else pattern.lower()
    matches: List[dict] = []
    start = 0
    while True:
        idx = search_text.find(search_pattern, start)
        if idx == -1:
            break
        matches.append(
            {
                "match": test_text[idx : idx + len(pattern)],
                "start": idx,
                "end": idx + len(pattern),
            }
        )
        start = idx + 1
    return matches, None


def test_wildcard_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    matches: List[dict] = []
    if fnmatch.fnmatch(test_text, pattern):
        matches.append({"match": test_text, "start": 0, "end": len(test_text)})
    return matches, None


def test_pattern_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    try:
        compiled = re.compile(pattern, flags)
        matches = [
            {"match": m.group(), "start": m.start(), "end": m.end()}
            for m in compiled.finditer(test_text)
        ]
        return matches, None
    except re.error as e:
        return [], f"Invalid pattern: {e}"


def test_exact_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    cmp_text = test_text if case_sensitive else test_text.lower()
    cmp_pattern = pattern if case_sensitive else pattern.lower()
    matches: List[dict] = []
    if cmp_text == cmp_pattern:
        matches.append({"match": test_text, "start": 0, "end": len(test_text)})
    return matches, None


def test_dynamic_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    try:
        wrapped = r"\b(?:%s)\b" % pattern
        compiled = re.compile(wrapped, flags)
        matches = [
            {"match": m.group(), "start": m.start(), "end": m.end()}
            for m in compiled.finditer(test_text)
        ]
        return matches, None
    except re.error as e:
        return [], f"Invalid dynamic pattern: {e}"


def test_semantic_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    pattern_words = pattern.split()
    test_words = test_text.split()
    if not case_sensitive:
        pattern_words = [w.lower() for w in pattern_words]
        test_words = [w.lower() for w in test_words]

    pattern_lower = [w.lower() for w in pattern.split()]
    matches: List[dict] = []
    for i in range(len(test_words)):
        for j in range(i + 1, min(i + len(pattern_words) + 1, len(test_words) + 1)):
            segment = test_words[i:j]
            similarity = difflib.SequenceMatcher(
                None, pattern_lower, [w.lower() for w in segment]
            ).ratio()
            if similarity >= 0.7:
                original_segment = test_text.split()[i:j]
                matched_text = " ".join(original_segment)
                start = len(" ".join(test_text.split()[:i])) + (1 if i > 0 else 0)
                end = start + len(matched_text)
                matches.append(
                    {
                        "match": matched_text,
                        "start": start,
                        "end": end,
                        "similarity": round(similarity, 3),
                    }
                )
    return matches, None
