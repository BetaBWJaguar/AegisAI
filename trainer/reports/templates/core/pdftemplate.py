from dataclasses import dataclass
from datetime import datetime

@dataclass
class PdfTemplateContext:
    title: str
    generated_at: datetime
    currency: str
