import re
import unicodedata

from multilangsetup.normalizers.turkish_normalizer import TurkishNormalizer
from multilangsetup.normalizers.german_normalizer import GermanNormalizer
from obsf.obfuscation_config_loader import ObfuscationConfigLoader
from multilangsetup.obsfucationresolver.obsfucation_helper import ObfuscationHelper
from multilangsetup.obsfucationresolver.obsfucation_util import ObfuscationUtil
from multilangsetup.constants.english import EN_STOPWORDS, EN_CONTRACTIONS
from multilangsetup.constants.german import DE_STOPWORDS


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
        text = ObfuscationResolver._apply_language_specific_rules(text, lang, special_rules)

        if merged_cfg.get("remove_numbers", False):
            text = re.sub(r"\d+", "", text)

        if merged_cfg.get("remove_punctuation", False):
            text = re.sub(r"[^\w\s]", "", text)

        if merged_cfg.get("collapse_whitespace", True):
            text = re.sub(r"\s+", " ", text)

        max_len = merged_cfg.get("max_text_length")
        if isinstance(max_len, int) and max_len > 0:
            text = text[:max_len]

        text = ObfuscationHelper.clean_redundant_symbols(text)

        if lang == "tr":
            text = TurkishNormalizer.normalize_all(text, to_lower=False)

        if lang == "de":
            text = GermanNormalizer.normalize_all(text, to_lower=False)

        if merged_cfg.get("to_lowercase", True):
            if lang == "tr":
                text = TurkishNormalizer.to_lower_turkish(text)
            else:
                text = text.lower()

        if merged_cfg.get("remove_stopwords", False):
            if lang == "en":
                words = text.split()
                words = [w for w in words if w not in EN_STOPWORDS]
                text = " ".join(words)
            elif lang == "de":
                words = text.split()
                words = [w for w in words if w not in DE_STOPWORDS]
                text = " ".join(words)

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

        if lang == "en":
            text = ObfuscationResolver._apply_english_rules(text, rules)

        if lang == "tr":
            text = ObfuscationResolver._apply_turkish_rules(text, rules)

        if lang == "de":
            text = ObfuscationResolver._apply_german_rules(text, rules)

        return text

    @staticmethod
    def _apply_english_rules(text: str, rules: dict) -> str:

        if rules.get("normalize_english_chars", False):
            replacements = {
                "á": "a", "à": "a", "ä": "a", "â": "a",
                "é": "e", "è": "e", "ë": "e", "ê": "e",
                "í": "i", "ì": "i", "ï": "i", "î": "i",
                "ó": "o", "ò": "o", "ö": "o", "ô": "o",
                "ú": "u", "ù": "u", "ü": "u", "û": "u"
            }
            for k, v in replacements.items():
                text = text.replace(k, v)

        if rules.get("normalize_quotes", True):
            text = text.replace("“", '"').replace("”", '"')
            text = text.replace("‘", "'").replace("’", "'")

        if rules.get("expand_contractions", False):
            for k, v in EN_CONTRACTIONS.items():
                text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)

        if rules.get("normalize_spacing", True):
            text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def _apply_turkish_rules(text: str, rules: dict) -> str:

        if rules.get("normalize_turkish_chars", False):
            replacements = {
                "İ": "i", "I": "ı",
                "Ç": "ç", "Ş": "ş",
                "Ğ": "ğ", "Ü": "ü", "Ö": "ö"
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

    @staticmethod
    def _apply_german_rules(text: str, rules: dict) -> str:

        if rules.get("normalize_german_chars", False):
            replacements = {
                "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
                "ä": "ae", "ö": "oe", "ü": "ue",
                "ß": "ss"
            }
            for k, v in replacements.items():
                text = text.replace(k, v)

        if rules.get("umlaut_to_ascii", False):
            text = GermanNormalizer.normalize_umlauts(text, to_ascii=True)

        if rules.get("sharp_s_to_ss", False):
            text = text.replace("ß", "ss")

        if rules.get("normalize_spacing", True):
            text = re.sub(r"\s+", " ", text).strip()

        if rules.get("normalize_quotes", True):
            text = GermanNormalizer.normalize_quotes(text)

        return text
