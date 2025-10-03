import uuid
from typing import List, Optional
from datetime import datetime

from template.create.create import TemplateCreate
from template.template import Template
from template.templateservice import TemplateService
from template.upsert.upsert import TemplateUpsert


class TemplateServiceImpl(TemplateService):
    def __init__(self):
        self.templates: dict[str, Template] = {}

    def create_template(self, data: TemplateCreate) -> Template:
        tpl = Template.create(
            name=data.name,
            pattern=data.pattern,
            description=data.description
        )
        self.templates[str(tpl.id)] = tpl
        return tpl

    def get_template(self, template_id: str) -> Optional[Template]:
        return self.templates.get(template_id)

    def list_templates(self) -> List[Template]:
        return list(self.templates.values())

    def update_template(self, template_id: str, data: TemplateUpsert) -> Optional[Template]:
        tpl = self.templates.get(template_id)
        if not tpl:
            return None
        if data.name is not None:
            tpl.name = data.name
        if data.pattern is not None:
            tpl.pattern = data.pattern
        if data.description is not None:
            tpl.description = data.description
        tpl.updated_at = datetime.utcnow()
        self.templates[template_id] = tpl
        return tpl

    def delete_template(self, template_id: str) -> bool:
        return self.templates.pop(template_id, None) is not None
