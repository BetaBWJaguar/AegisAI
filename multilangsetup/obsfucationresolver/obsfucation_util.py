import re

class ObfuscationUtil:
    OBFUSCATION_MAP = {
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's',
        '6': 'g', '7': 't', '8': 'b', '9': 'g',
        '@': 'a', '$': 's', '!': 'i', '|': 'l', '+': 't',
        '€': 'e', '¥': 'y', '₺': 't', '§': 's'
    }

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

        map_to_use = mapping if mapping else cls.OBFUSCATION_MAP
        return text.translate(str.maketrans(map_to_use))
