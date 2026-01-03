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
RE_BITCOIN_ADDRESS = re.compile(r"\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b")
RE_ETHEREUM_ADDRESS = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
RE_CRYPTO_WALLET = re.compile(
    r"\b(?:0x[a-fA-F0-9]{40}|[13][a-zA-HJ-NP-Z0-9]{25,39}|bc1[a-zA-HJ-NP-Z0-9]{39,59})\b"
)

RE_SWIFT_BIC = re.compile(r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b")

RE_PASSPORT = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")
RE_DRIVER_LICENSE = re.compile(r"\b[A-Z]{1,2}\d{5,8}\b")
RE_STUDENT_ID = re.compile(r"\b(?:STU|STD|S)\d{6,10}\b", re.I)
RE_UNIVERSITY_EMAIL = re.compile(
    r"\b[A-Z0-9._%+-]+@(?:student\.|edu\.|ac\.)[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I
)

RE_FINGERPRINT = re.compile(
    r"\b(?:fingerprint|fingerprint_data|biometric_data|iris_scan|face_recognition)"
    r"[:\s]*[A-F0-9+/]{50,}={0,2}\b",
    re.I
)

RE_DNA_SEQUENCE = re.compile(r"\b(?:dna|genetic|genome)[:\s]*[ATCG]{20,}\b", re.I)
RE_SSN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
RE_TAX_ID = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
RE_NATIONAL_ID = re.compile(r"\b\d{10,15}\b")


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

        if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", iban):
            return False

        if not 15 <= len(iban) <= 34:
            return False

        rearranged = iban[4:] + iban[:4]

        numeric_iban = ""
        for ch in rearranged:
            numeric_iban += ch if ch.isdigit() else str(ord(ch) - ord("A") + 10)

        try:
            return int(numeric_iban) % 97 == 1
        except (ValueError, OverflowError):
            return False

    @staticmethod
    def _valid_bitcoin_address(addr: str) -> bool:
        addr = addr.lower()
        if addr.startswith("bc1"):
            return 39 <= len(addr) <= 59
        if addr.startswith(("1", "3")):
            return 26 <= len(addr) <= 35
        return False

    @staticmethod
    def _valid_ethereum_address(addr: str) -> bool:
        return bool(re.match(r"^0x[a-fA-F0-9]{40}$", addr))

    @staticmethod
    def _valid_swift_bic(bic: str) -> bool:
        return bool(re.match(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$", bic))

    @staticmethod
    def _valid_ssn(ssn: str) -> bool:
        digits = re.sub(r"\D", "", ssn)
        if len(digits) != 9:
            return False
        area = int(digits[:3])
        return 1 <= area <= 899 and area != 666

    @staticmethod
    def detect(text: str) -> List[PIISignal]:
        signals: List[PIISignal] = []

        def add(kind: str, regex: re.Pattern, validator=None) -> None:
            spans: List[Tuple[int, int]] = []
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
        add("bitcoin", RE_BITCOIN_ADDRESS, PIIDetector._valid_bitcoin_address)
        add("ethereum", RE_ETHEREUM_ADDRESS, PIIDetector._valid_ethereum_address)
        add("crypto_wallet", RE_CRYPTO_WALLET)
        add("swift_bic", RE_SWIFT_BIC, PIIDetector._valid_swift_bic)
        add("passport", RE_PASSPORT)
        add("driver_license", RE_DRIVER_LICENSE)
        add("ssn", RE_SSN, PIIDetector._valid_ssn)
        add("tax_id", RE_TAX_ID)
        add("national_id", RE_NATIONAL_ID)
        add("student_id", RE_STUDENT_ID)
        add("university_email", RE_UNIVERSITY_EMAIL)
        add("fingerprint", RE_FINGERPRINT)
        add("dna", RE_DNA_SEQUENCE)

        return signals
