import re

class ObfuscationUtil:

    @classmethod
    def replace_common_patterns(cls, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'([@!$%&*?+])\1+', r'\1', text)

        return text

    @classmethod
    def resolve_symbols_and_numbers(cls, text: str, mapping: dict = None) -> str:
        if not text:
            return ""

        map_to_use = mapping
        return text.translate(str.maketrans(map_to_use))
