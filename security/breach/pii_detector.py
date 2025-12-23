import re
from dataclasses import dataclass
from typing import List, Tuple

RE_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
RE_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s\-()]*)?(?:\d[\s\-()]*){9,12}(?!\d)")
RE_IPV4  = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_COORD = re.compile(r"\b-?\d{1,2}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}\b")
RE_MAPS  = re.compile(r"(google\.com/maps|maps\.google|goo\.gl/maps|yandex\..*/maps|apple\.com/maps)", re.I)

@dataclass
class PIISignal:
    kind: str
    spans: List[Tuple[int, int]]

class PIIDetector:

    @staticmethod
    def detect(text: str) -> List[PIISignal]:
        signals: List[PIISignal] = []

        def add(kind: str, regex: re.Pattern):
            spans = [(m.start(), m.end()) for m in regex.finditer(text)]
            if spans:
                signals.append(PIISignal(kind, spans))

        add("email", RE_EMAIL)
        add("phone", RE_PHONE)
        add("ipv4", RE_IPV4)
        add("coord", RE_COORD)
        add("maps", RE_MAPS)

        return signals
