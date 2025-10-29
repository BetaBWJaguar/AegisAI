from multilangsetup.obsfucationresolver.obsfucation_helper import ObfuscationHelper
from multilangsetup.obsfucationresolver.obsfucation_util import ObfuscationUtil


class ObfuscationResolver:
    @staticmethod
    def resolve_all(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = ObfuscationHelper.normalize_unicode(text)
        text = ObfuscationUtil.replace_common_patterns(text)
        text = ObfuscationUtil.resolve_symbols_and_numbers(text)
        text = ObfuscationHelper.clean_redundant_symbols(text)
        return text.strip()
