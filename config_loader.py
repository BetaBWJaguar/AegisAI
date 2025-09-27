import json
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file {self.config_file} not found.")
        with open(self.config_file, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def get_database_config(self) -> dict:
        return self.config["database"]

    def get_jwt_config(self) -> dict:
        return self.config["jwt"]
