from abc import ABC, abstractmethod
from typing import List, Optional

from template.create.create import TemplateCreate
from template.template import Template
from template.upsert.upsert import TemplateUpsert


class TemplateService(ABC):

    @abstractmethod
    def create_template(self, data: TemplateCreate) -> Template:
        pass

    @abstractmethod
    def get_template(self, template_id: str) -> Optional[Template]:
        pass

    @abstractmethod
    def list_templates(self) -> List[Template]:
        pass

    @abstractmethod
    def update_template(self, template_id: str, data: TemplateUpsert) -> Optional[Template]:
        pass

    @abstractmethod
    def delete_template(self, template_id: str) -> bool:
        pass
