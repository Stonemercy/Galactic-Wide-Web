from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class PlanetFeatures:
    feature_codes_map = {
        ("XENOENTOMOLOGY CENTRE", Emojis.PlanetFeatures.xenoentomology_centre): {1197},
        (
            "DEEP MANTLE FORGE COMPLEX",
            Emojis.PlanetFeatures.deep_mantle_forge_complex,
        ): {1198},
        ("MERIDIAN BLACK HOLE", Emojis.PlanetFeatures.black_hole): {1229, 1230},
        ("FACTORY HUB", Emojis.PlanetFeatures.factory_hub): {1232},
        ("CENTRE OF SCIENCE", Emojis.PlanetFeatures.centre_of_science): {1234},
        ("CENTRE FOR CIVILIAN SURVEILLANCE AND SAFETY", Emojis.PlanetFeatures.cfcsas): {
            1236
        },
        ("FRACTURED PLANET", Emojis.PlanetFeatures.cfcsas): {1241},
        (
            "HELLDIVER TRAINING FACILITIES",
            Emojis.PlanetFeatures.helldiver_training_facilities,
        ): {1282},
        (
            "NEW HOPE CITY",
            Emojis.PlanetFeatures.new_hope_city,
        ): {1287},
        (
            "NEW ASPIRATION CITY",
            Emojis.PlanetFeatures.new_aspiration_city,
        ): {1291},
        (
            "NEW YEARNING CITY",
            Emojis.PlanetFeatures.helldiver_training_facilities,
        ): {1292},
        ("HIVE WORLD", Emojis.PlanetFeatures.hive_world): {1311},
        ("ULGRAMAFIC MINE", Emojis.PlanetFeatures.ulgramafic_mine): {1324},
        ("E-711 Extraction Facility", Emojis.PlanetFeatures.e711_extraction_facility): {
            1333
        },
        (
            "Centre for the Confinement of Dissidence (CECOD)",
            Emojis.PlanetFeatures.cecod,
        ): {1342},
    }

    @classmethod
    def get_from_effects_list(cls, active_effects: set) -> set[tuple[str, str]]:
        planet_effects = set()
        for ae in active_effects:
            features_list = [k for k, v in cls.feature_codes_map.items() if ae.id in v]
            if features_list:
                planet_effects.add(features_list[0])
        return planet_effects
