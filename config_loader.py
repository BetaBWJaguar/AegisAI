import json
import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

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
        jwt_cfg = self.config.get("jwt", {}).copy()

        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable not set")

        jwt_cfg["secret_key"] = secret_key
        return jwt_cfg
