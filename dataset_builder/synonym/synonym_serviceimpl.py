from typing import Dict, List, Optional
from pymongo import MongoClient
from dataset_builder.synonym.synonym_service import SynonymService
from config_loader import ConfigLoader


class SynonymServiceImpl(SynonymService):

    def __init__(self, config_file: str = "config.json"):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"

        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["synonyms"]

    def get_all_synonyms(self) -> Dict[str, List[str]]:
        result = {}
        for doc in self.collection.find():
            word = doc.get("word")
            synonyms = doc.get("synonyms", [])
            if word:
                result[word] = synonyms
        return result

    def get_synonym(self, word: str) -> Optional[List[str]]:
        doc = self.collection.find_one({"word": word.lower()})
        if doc:
            return doc.get("synonyms", [])
        return None

    def add_synonym(self, word: str, synonyms: List[str]) -> bool:
        if not word or not synonyms:
            return False

        word_key = word.lower()
        existing = self.collection.find_one({"word": word_key})

        if existing:
            existing_synonyms = set(existing.get("synonyms", []))
            new_synonyms = set([s.lower() for s in synonyms if s])
            merged = list(existing_synonyms.union(new_synonyms))
            self.collection.update_one(
                {"word": word_key},
                {"$set": {"synonyms": merged}}
            )
        else:
            self.collection.insert_one({
                "word": word_key,
                "synonyms": [s.lower() for s in synonyms if s]
            })
        return True

    def update_synonym(self, word: str, synonyms: List[str]) -> bool:
        if not word:
            return False

        word_key = word.lower()
        result = self.collection.update_one(
            {"word": word_key},
            {"$set": {"synonyms": [s.lower() for s in synonyms if s]}}
        )
        return result.modified_count > 0

    def delete_synonym(self, word: str) -> bool:
        result = self.collection.delete_one({"word": word.lower()})
        return result.deleted_count > 0

    def add_synonyms_bulk(self, synonym_dict: Dict[str, List[str]]) -> bool:
        if not synonym_dict:
            return False

        operations = []
        for word, synonyms in synonym_dict.items():
            if not word or not synonyms:
                continue

            word_key = word.lower()
            operations.append({
                "word": word_key,
                "synonyms": [s.lower() for s in synonyms if s]
            })

        if operations:
            for op in operations:
                existing = self.collection.find_one({"word": op["word"]})
                if existing:
                    existing_synonyms = set(existing.get("synonyms", []))
                    new_synonyms = set(op["synonyms"])
                    merged = list(existing_synonyms.union(new_synonyms))
                    self.collection.update_one(
                        {"word": op["word"]},
                        {"$set": {"synonyms": merged}}
                    )
                else:
                    # Insert
                    self.collection.insert_one(op)

        return True

    def clear_all_synonyms(self) -> bool:
        result = self.collection.delete_many({})
        return result.deleted_count >= 0
