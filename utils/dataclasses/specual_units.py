from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class SpecialUnits:
    unit_codes_map = {
        ("THE JET BRIGADE", Emojis.SpecialUnits.jet_brigade): {1202, 1203},
        ("PREDATOR STRAIN", Emojis.SpecialUnits.predator_strain): {1243, 1245},
        ("SPORE BURSTER STRAIN", Emojis.SpecialUnits.spore_burster_strain): {1244},
        ("INCINERATION CORPS", Emojis.SpecialUnits.incineration_corps): {1248, 1249},
        ("THE GREAT HOST", Emojis.SpecialUnits.the_great_host): {1269},
        ("RUPTURE STRAIN", Emojis.SpecialUnits.rupture_strain): {1303},
        ("DRAGON ROACHES", Emojis.SpecialUnits.dragon_roaches): {1306},
        ("HIVE LORDS", Emojis.SpecialUnits.hive_lords): {1307},
    }

    @classmethod
    def get_from_effects_list(cls, active_effects: set) -> set | set[tuple[str, str]]:
        special_units = set()
        for unit_info, required_codes in cls.unit_codes_map.items():
            if required_codes.issubset(set([ae.id for ae in active_effects])):
                special_units.add(unit_info)
        return special_units
