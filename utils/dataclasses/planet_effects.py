from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class PlanetEffects:
    effect_codes_map = {
        ("Meridian Black Hole", Emojis.PlanetEffects.black_hole): {1230},
        ("Centre for Civilian Surveillance and Safety", Emojis.PlanetEffects.cfcsas): {
            1236
        },
        ("Hive World", Emojis.PlanetEffects.hive_world): {1311},
    }

    @classmethod
    def get_from_effects_list(cls, active_effects: set) -> set | set[tuple[str, str]]:
        planet_effects = set()
        for effect_info, required_effects in cls.effect_codes_map.items():
            if required_effects.issubset(set([ae.id for ae in active_effects])):
                planet_effects.add(effect_info)
        return planet_effects
