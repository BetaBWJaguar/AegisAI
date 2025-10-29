import re

class ObfuscationUtil:
    OBFUSCATION_MAP = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '6': 'g',
        '7': 't',
        '8': 'b',
        '9': 'g',
        '@': 'a',
        '$': 's',
        '!': 'i',
        '|': 'l',
        '+': 't',
        '€': 'e',
        '¥': 'y',
        '₺': 't',
        '§': 's'
    }

    @staticmethod
    def replace_common_patterns(text: str) -> str:
        text = re.sub(r'([@!$%&*?+])\1+', r'\1', text)

        text = ObfuscationUtil.resolve_symbols_and_numbers(text)

        return text

    @staticmethod
    def resolve_symbols_and_numbers(text: str) -> str:
        for k, v in ObfuscationUtil.OBFUSCATION_MAP.items():
            text = text.replace(k, v)
        return text
