from dataclasses import dataclass


@dataclass
class RandomiserData:
    stratagems: list[list[str, dict]]
    primary_weapon: dict
    secondary_weapon: dict
    grenade: dict
    booster: dict
    armor: dict
    where_to_spawn: str
    json_dict: dict
