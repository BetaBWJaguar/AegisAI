import re
import unicodedata
from obsf.obfuscation_config_loader import ObfuscationConfigLoader


class ObfuscationHelper:
    @staticmethod
    def _load_config_safe():
        try:
            return ObfuscationConfigLoader.load_global()
        except FileNotFoundError:
            return {}
        except Exception:
            return {}

    @staticmethod
    def normalize_unicode(text: str) -> str:
        if not text:
            return ""

        cfg = ObfuscationHelper._load_config_safe()
        if not cfg.get("normalize_unicode", True):
            return text

        return unicodedata.normalize("NFC", text)

    @staticmethod
    def clean_redundant_symbols(text: str) -> str:
        if not text:
            return ""

        cfg = ObfuscationHelper._load_config_safe()

        if cfg.get("reduce_symbol_repetition", True):
            threshold = int(cfg.get("symbol_repetition_threshold", 2))
            pattern = r"([!?.*#@%&])\1{" + str(threshold) + r",}"
            text = re.sub(pattern, r"\1", text)

        if cfg.get("clean_extra_spaces", True):
            text = re.sub(r"\s{2,}", " ", text)

        if cfg.get("apply_space_trim", True):
            text = text.strip()

        return text

    @staticmethod
    def apply_lowercase(text: str) -> str:
        if not text:
            return ""

        cfg = ObfuscationHelper._load_config_safe()
        return text.lower() if cfg.get("to_lowercase", True) else text
