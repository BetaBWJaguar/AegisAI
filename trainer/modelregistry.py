from datetime import datetime
from pymongo import MongoClient
from pathlib import Path

from config_loader import ConfigLoader


class ModelRegistry:

    def __init__(self, config_file: str = "config.json"):

        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["models"]

    def save_model_info(self, name, version, model_path, dataset_id, parameters, metrics):
        doc = {
            "name": name,
            "version": version,
            "model_path": model_path,
            "dataset_used": dataset_id,
            "parameters": parameters,
            "metrics": metrics,
            "created_at": datetime.utcnow().isoformat()
        }

        result = self.collection.insert_one(doc)

        doc["_id"] = str(result.inserted_id)

        return doc
