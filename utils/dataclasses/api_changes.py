from dataclasses import dataclass
from typing import Any


@dataclass
class APIChanges:
    planet: Any
    statistic: str
    before: int | list | Any
    after: int | list | Any
