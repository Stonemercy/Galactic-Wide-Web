from dataclasses import dataclass


@dataclass
class CampaignChangesJson:
    lang_code_long: str
    container: dict
    subfactions: dict
    factions: dict
    regions: dict
