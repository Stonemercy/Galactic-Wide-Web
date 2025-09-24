from dataclasses import dataclass


@dataclass
class RegionChangesJson:
    lang_code_long: str
    container: dict
    special_units: dict
    factions: dict
