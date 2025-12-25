import re
from dataclasses import dataclass
from typing import List, Tuple


RE_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
RE_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s\-()]*)?(?:\d[\s\-()]*){9,12}(?!\d)")
RE_IPV4  = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_COORD = re.compile(r"\b-?\d{1,2}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}\b")
RE_MAPS  = re.compile(
    r"(google\.com/maps|maps\.google|goo\.gl/maps|yandex\..*/maps|apple\.com/maps)",
    re.I
)
RE_ID_NUMBER = re.compile(r"\b\d{11}\b")
RE_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b", re.I)
RE_URL = re.compile(
    r"\b(?:https?://|www\.)[A-Z0-9.-]+\.[A-Z]{2,}(?:/[^\s]*)?",
    re.I
)
RE_CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


@dataclass
class PIISignal:
    kind: str
    spans: List[Tuple[int, int]]


class PIIDetector:

    @staticmethod
    def _valid_ipv4(ip: str) -> bool:
        try:
            return all(0 <= int(p) <= 255 for p in ip.split("."))
        except ValueError:
            return False

    @staticmethod
    def _valid_iban(iban: str) -> bool:
        iban = iban.upper().replace(" ", "")

        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', iban):
            return False
        if not 15 <= len(iban) <= 34:
            return False

        rearranged = iban[4:] + iban[:4]
        numeric = ""

        for c in rearranged:
            numeric += c if c.isdigit() else str(ord(c) - 55)

        try:
            return int(numeric) % 97 == 1
        except Exception:
            return False

    @staticmethod
    def _valid_credit_card(cc: str) -> bool:
        cc = re.sub(r"\D", "", cc)
        if not 13 <= len(cc) <= 19:
            return False

        total = 0
        reverse = cc[::-1]
        for i, d in enumerate(reverse):
            n = int(d)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def _valid_iban(iban: str) -> bool:
        iban = iban.upper().replace(" ", "")
        

        if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]+$', iban):
            return False
            

        if len(iban) < 15 or len(iban) > 34:
            return False

        rearranged = iban[4:] + iban[:4]

        numeric_iban = ''
        for char in rearranged:
            if char.isdigit():
                numeric_iban += char
            else:
                numeric_iban += str(ord(char) - ord('A') + 10)

        try:
            return int(numeric_iban) % 97 == 1
        except (ValueError, OverflowError):
            return False

    @staticmethod
    def detect(text: str) -> List[PIISignal]:
        signals: List[PIISignal] = []

        def add(kind: str, regex: re.Pattern, validator=None):
            spans = []
            for m in regex.finditer(text):
                if validator and not validator(m.group()):
                    continue
                spans.append((m.start(), m.end()))
            if spans:
                signals.append(PIISignal(kind, spans))

        add("email", RE_EMAIL)
        add("phone", RE_PHONE)
        add("ipv4", RE_IPV4, PIIDetector._valid_ipv4)
        add("coord", RE_COORD)
        add("maps", RE_MAPS)
        add("id_number", RE_ID_NUMBER)
        add("iban", RE_IBAN, PIIDetector._valid_iban)
        add("credit_card", RE_CREDIT_CARD, PIIDetector._valid_credit_card)
        add("url", RE_URL)

        return signals