import uuid
import json
from datetime import datetime
from pymongo import MongoClient
from pathlib import Path


class ModelRegistry:

    def __init__(self, config_file: str = "config.json"):

        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["models"]

    def save_model_info(self, name, version, model_path, dataset_id, parameters, metrics):
        doc = {
            "id": str(uuid.uuid4()),
            "name": name,
            "version": version,
            "model_path": model_path,
            "dataset_used": dataset_id,
            "parameters": parameters,
            "metrics": metrics,
            "created_at": datetime.utcnow().isoformat()
        }

        self.collection.insert_one(doc)
        return doc
