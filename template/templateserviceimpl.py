import uuid
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient

from config_loader import ConfigLoader
from template.create.create import TemplateCreate
from template.template import Template
from template.templateservice import TemplateService
from template.upsert.upsert import TemplateUpsert


class TemplateServiceImpl(TemplateService):
    def __init__(self, config_file: str = "config.json"):
        cfg = ConfigLoader(config_file).get_database_config()
        uri = f"mongodb://{cfg['username']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['authSource']}"
        self.client = MongoClient(uri)
        self.db = self.client[cfg["name"]]
        self.collection = self.db["templates"]

    def create_template(self, data: TemplateCreate) -> Template:
        tpl = Template.create(
            name=data.name,
            pattern=data.pattern,
            description=data.description
        )
        doc = tpl.to_dict()
        result = self.collection.insert_one(doc)
        tpl._id = str(result.inserted_id)
        return tpl

    def get_template(self, template_id: str) -> Optional[Template]:
        doc = self.collection.find_one({"id": template_id})
        if not doc:
            return None
        return Template(
            id=uuid.UUID(doc["id"]),
            name=doc["name"],
            pattern=doc["pattern"],
            description=doc["description"],
            created_at=datetime.fromisoformat(doc["created_at"]),
            updated_at=datetime.fromisoformat(doc["updated_at"]),
            _id=str(doc["_id"])
        )

    def list_templates(self) -> List[Template]:
        templates = []
        for doc in self.collection.find():
            templates.append(
                Template(
                    id=uuid.UUID(doc["id"]),
                    name=doc["name"],
                    pattern=doc["pattern"],
                    description=doc["description"],
                    created_at=datetime.fromisoformat(doc["created_at"]),
                    updated_at=datetime.fromisoformat(doc["updated_at"]),
                    _id=str(doc["_id"])
                )
            )
        return templates

    def update_template(self, template_id: str, data: TemplateUpsert) -> Optional[Template]:
        tpl = self.get_template(template_id)
        if not tpl:
            return None

        if data.name is not None:
            tpl.name = data.name
        if data.pattern is not None:
            tpl.pattern = data.pattern
        if data.description is not None:
            tpl.description = data.description

        tpl.updated_at = datetime.utcnow()
        self.collection.update_one(
            {"id": template_id},
            {"$set": tpl.to_dict()}
        )
        return tpl

    def delete_template(self, template_id: str) -> bool:
        result = self.collection.delete_one({"id": template_id})
        return result.deleted_count > 0
