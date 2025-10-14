from dataclasses import dataclass


@dataclass
class CampaignChangesJson:
    lang_code_long: str
    container: dict
    special_units: dict
    factions: dict
    regions: dict
