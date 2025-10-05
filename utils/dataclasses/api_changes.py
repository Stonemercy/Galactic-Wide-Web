from dataclasses import dataclass
from typing import Any


@dataclass
class APIChanges:
    old_object: Any
    new_object: Any
    property: str
    stat_name: str
    stat_source: str
