import re
import unicodedata

from multilangsetup.normalizers.turkish_normalizer import TurkishNormalizer
from obsf.obfuscation_config_loader import ObfuscationConfigLoader
from multilangsetup.obsfucationresolver.obsfucation_helper import ObfuscationHelper
from multilangsetup.obsfucationresolver.obsfucation_util import ObfuscationUtil


class ObfuscationResolver:
    @staticmethod
    def resolve_all(text: str, lang: str = None) -> str:
        if not isinstance(text, str) or not text.strip():
            return ""

        try:
            global_cfg = ObfuscationConfigLoader.load_global()
        except FileNotFoundError:
            global_cfg = {}

        enabled_langs = global_cfg.get("languages_enabled", [])
        default_lang = global_cfg.get("default_language", "tr")
        lang = (lang or default_lang).lower()

        if lang not in enabled_langs:
            lang = default_lang

        try:
            lang_cfg = ObfuscationConfigLoader.load_language(lang)
        except FileNotFoundError:
            lang_cfg = {}

        settings = lang_cfg.get("settings", {})
        special_rules = lang_cfg.get("special_rules", {})
        merged_cfg = {**global_cfg, **settings}

        if merged_cfg.get("normalize_unicode", True):
            text = ObfuscationHelper.normalize_unicode(text)

        text = ObfuscationUtil.replace_common_patterns(text)
        leet_map = special_rules.get("leet_mapping", {})
        text = ObfuscationUtil.resolve_symbols_and_numbers(text, mapping=leet_map)
        text = ObfuscationResolver._apply_language_specific_rules(text, lang, special_rules)
        text = ObfuscationHelper.clean_redundant_symbols(text)

        if lang == "tr" and merged_cfg.get("apply_turkish_normalizer", True):
            text = TurkishNormalizer.normalize_all(text, to_lower=False)

        if merged_cfg.get("to_lowercase", True):
            text = TurkishNormalizer.to_lower_turkish(text) if lang == "tr" else text.lower()

        return text.strip()

    @staticmethod
    def _apply_language_specific_rules(text: str, lang: str, rules: dict) -> str:
        if not text or not rules:
            return text

        if rules.get("replace_diacritics", False):
            text = "".join(
                c for c in unicodedata.normalize("NFD", text)
                if unicodedata.category(c) != "Mn"
            )

        if lang == "tr":
            text = ObfuscationResolver._apply_turkish_rules(text, rules)

        return text

    @staticmethod
    def _apply_turkish_rules(text: str, rules: dict) -> str:
        if rules.get("normalize_turkish_chars", False):
            replacements = {
                "İ": "i", "I": "ı",
                "Ç": "ç", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö"
            }
            for k, v in replacements.items():
                text = text.replace(k, v)

        if rules.get("convert_q_to_k", False):
            text = re.sub(r"q", "k", text, flags=re.IGNORECASE)

        if rules.get("normalize_spacing", True):
            text = re.sub(r"\s+", " ", text).strip()

        if rules.get("normalize_quotes", True):
            text = TurkishNormalizer.normalize_quotes(text)

        return text
