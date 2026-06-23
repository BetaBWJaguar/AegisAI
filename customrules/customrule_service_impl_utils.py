
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
            {
                "match": m.group(),
                "start": m.start(),
                "end": m.end(),
                "groups": [g if g is not None else "" for g in m.groups()],
                "named_groups": {
                    k: (v if v is not None else "") for k, v in m.groupdict().items()
                },
            }
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
    matched = (
        fnmatch.fnmatchcase(test_text, pattern)
        if case_sensitive
        else fnmatch.fnmatch(test_text, pattern)
    )
    if matched:
        matches.append({"match": test_text, "start": 0, "end": len(test_text)})
    return matches, None


def test_pattern_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    try:
        compiled = re.compile(pattern, flags)
        matches = [
            {
                "match": m.group(),
                "start": m.start(),
                "end": m.end(),
                "groups": [g if g is not None else "" for g in m.groups()],
                "named_groups": {
                    k: (v if v is not None else "") for k, v in m.groupdict().items()
                },
            }
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
            {
                "match": m.group(),
                "start": m.start(),
                "end": m.end(),
                "groups": [g if g is not None else "" for g in m.groups()],
                "named_groups": {
                    k: (v if v is not None else "") for k, v in m.groupdict().items()
                },
            }
            for m in compiled.finditer(test_text)
        ]
        return matches, None
    except re.error as e:
        return [], f"Invalid dynamic pattern: {e}"


def test_semantic_match(
    pattern: str, test_text: str, case_sensitive: bool, flags: int
) -> Tuple[List[dict], Optional[str]]:
    pattern_words_raw = pattern.split()
    test_words_raw = test_text.split()

    if not case_sensitive:
        pattern_words = [w.lower() for w in pattern_words_raw]
        test_words = [w.lower() for w in test_words_raw]
    else:
        pattern_words = pattern_words_raw
        test_words = test_words_raw

    n_test = len(test_words)
    n_pattern = len(pattern_words)
    matches: List[dict] = []

    if n_pattern == 0 or n_test == 0:
        return matches, None

    offsets = [0] * (n_test + 1)
    for i in range(n_test):
        offsets[i + 1] = offsets[i] + len(test_words_raw[i]) + (1 if i > 0 else 0)

    pattern_lower = [w.lower() for w in pattern_words_raw]

    matcher = difflib.SequenceMatcher(None)
    matcher.set_seq2(pattern_lower)

    for i in range(n_test):
        max_j = min(i + n_pattern + 1, n_test + 1)
        for j in range(i + 1, max_j):
            segment = test_words[i:j]
            compare_segment = (
                [w.lower() for w in segment] if case_sensitive else segment
            )
            matcher.set_seq1(compare_segment)
            similarity = matcher.ratio()
            if similarity >= 0.7:
                matched_text = " ".join(test_words_raw[i:j])
                start = offsets[i] + (1 if i > 0 else 0)
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

def highlight_matches(
    text: str,
    matches: List[dict],
    pre_marker: str = "<<",
    post_marker: str = ">>",
) -> str:
    if not matches:
        return text


    sorted_matches = sorted(matches, key=lambda m: m["start"])
    parts: List[str] = []
    cursor = 0
    for m in sorted_matches:
        start, end = m["start"], m["end"]
        if start < cursor:
            continue
        parts.append(text[cursor:start])
        parts.append(pre_marker)
        parts.append(text[start:end])
        parts.append(post_marker)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def apply_replacement(
    text: str,
    matches: List[dict],
    replace_text: str,
) -> str:
    if not matches:
        return text

    sorted_matches = sorted(
        matches,
        key=lambda m: (m["start"], -(m["end"] - m["start"])),
        reverse=True,
    )
    result = text
    for m in sorted_matches:
        start, end = m["start"], m["end"]
        result = result[:start] + replace_text + result[end:]
    return result
