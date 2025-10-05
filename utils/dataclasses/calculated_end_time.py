from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CalculatedEndTime:
    source_planet: Any | None = None
    gambit_planet: Any | None = None
    regions: list | None = None
    end_time: datetime | None = None
