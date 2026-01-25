from typing import List
from dataclasses import dataclass

@dataclass(frozen=True)
class TrainingScenario:
    name: str
    multiplier: float
    tags: List[str] = ()
