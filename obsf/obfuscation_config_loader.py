import json
from pathlib import Path

class ObfuscationConfigLoader:
    BASE_DIR = Path(__file__).resolve().parent
    GLOBAL_CONFIG_PATH = BASE_DIR / "obfuscation_config.json"
    LANG_DIR = BASE_DIR / "languages"

    @classmethod
    def load_global(cls):
        if not cls.GLOBAL_CONFIG_PATH.exists():
            raise FileNotFoundError("Global config not found.")
        with cls.GLOBAL_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load_language(cls, lang: str):
        path = cls.LANG_DIR / f"{lang}.json"
        if not path.exists():
            raise FileNotFoundError(f"{lang}.json not found.")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
