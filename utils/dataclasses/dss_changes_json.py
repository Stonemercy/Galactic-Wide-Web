from dataclasses import dataclass


@dataclass
class DSSChangesJson:
    lang_code_long: str
    container: dict
    special_units: dict
