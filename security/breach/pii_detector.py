import re
from dataclasses import dataclass
from typing import List, Tuple


RE_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
RE_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s\-()]*)?(?:\d[\s\-()]*){9,12}(?!\d)")
RE_IPV4  = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
RE_BIRTHDATE = re.compile(
    r"\b(?:(?:19|20)\d{2}[-./](?:0?[1-9]|1[0-2])[-./](?:0?[1-9]|[12]\d|3[01])"
    r"|(?:0?[1-9]|[12]\d|3[01])[-./](?:0?[1-9]|1[0-2])[-./](?:19|20)\d{2})\b"
)

RE_VIN = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
RE_DOSAGE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(mg|g|mcg|μg|ml|iu|unit|units)\b", re.I)
RE_ICD10  = re.compile(r"\bICD-?10\s*:\s*[A-TV-Z][0-9]{2}(?:\.[0-9A-TV-Z]{1,4})?\b", re.I)
RE_COORD = re.compile(r"\b-?\d{1,2}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}\b")
RE_MAPS  = re.compile(r"(google\.com/maps|maps\.google|goo\.gl/maps|yandex\..*/maps|apple\.com/maps)", re.I)
RE_ID_NUMBER = re.compile(r"\b\d{11}\b")
RE_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b", re.I)
RE_URL = re.compile(r"\b(?:https?://|www\.)[A-Z0-9.-]+\.[A-Z]{2,}(?:/[^\s]*)?", re.I)
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
    def _valid_credit_card(cc: str) -> bool:
        cc = re.sub(r"\D", "", cc)
        if not 13 <= len(cc) <= 19:
            return False
        total = 0
        for i, d in enumerate(cc[::-1]):
            n = int(d)
            if i % 2 == 1:
                n = n * 2 - 9 if n * 2 > 9 else n * 2
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
        add("birthdate", RE_BIRTHDATE)
        add("vin", RE_VIN)
        add("health", RE_DOSAGE)
        add("health", RE_ICD10)
        add("coord", RE_COORD)
        add("maps", RE_MAPS)
        add("id_number", RE_ID_NUMBER)
        add("iban", RE_IBAN, PIIDetector._valid_iban)
        add("credit_card", RE_CREDIT_CARD, PIIDetector._valid_credit_card)
        add("url", RE_URL)

        return signals