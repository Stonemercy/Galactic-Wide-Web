from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class PlanetFeature:
    name: str
    emoji: str


class PlanetFeatures:
    all = {
        1195: PlanetFeature(
            "DSS CONSTRUCTION SITE - PHASE 1",
            "",
        ),
        1196: PlanetFeature(
            "DSS LOGISTICS HUB",
            "",
        ),
        1197: PlanetFeature(
            "XENOENTOMOLOGY CENTRE",
            Emojis.PlanetFeatures.xenoentomology_centre,
        ),
        1198: PlanetFeature(
            "DEEP MANTLE FORGE COMPLEX",
            Emojis.PlanetFeatures.deep_mantle_forge_complex,
        ),
        1199: PlanetFeature(
            "DSS CONSTRUCTION SITE - PHASE 2",
            "",
        ),
        1204: PlanetFeature(
            "LIBERTY DAY",
            Emojis.Icons.victory,
        ),
        1205: PlanetFeature(
            "DSS CONSTRUCTION SITE - PHASE 3",
            "",
        ),
        1206: PlanetFeature(
            "TERMINID RESEARCH PRESERVE",
            Emojis.PlanetFeatures.terminid_research_preserve,
        ),
        1211: PlanetFeature(
            "PLANETARY BOMBARDMENT",
            Emojis.SpaceStations.DSS.planetary_bombardment,
        ),
        1212: PlanetFeature(
            "EAGLE STORM",
            Emojis.SpaceStations.DSS.eagle_storm,
        ),
        1213: PlanetFeature(
            "ORBITAL BLOCKADE",
            Emojis.SpaceStations.DSS.orbital_blockade,
        ),
        1217: PlanetFeature(
            "DEMOCRACY SPACE STATION",
            Emojis.SpaceStations.DSS.icon,
        ),
        1228: PlanetFeature(
            "MERIDIAN BLACK HOLE",
            Emojis.PlanetFeatures.black_hole,
        ),
        1229: PlanetFeature(
            "MERIDIAN BLACK HOLE",
            Emojis.PlanetFeatures.black_hole,
        ),
        1230: PlanetFeature(
            "MERIDIAN BLACK HOLE",
            Emojis.PlanetFeatures.black_hole,
        ),
        1232: PlanetFeature(
            "FACTORY HUB",
            Emojis.PlanetFeatures.factory_hub,
        ),
        1234: PlanetFeature(
            "CENTRE OF SCIENCE",
            Emojis.PlanetFeatures.centre_of_science,
        ),
        1236: PlanetFeature(
            "CENTRE FOR CIVILIAN SURVEILLANCE AND SAFETY",
            Emojis.PlanetFeatures.cfcsas,
        ),
        1239: PlanetFeature(
            "JET BRIGADE FACTORIES",
            Emojis.Factions.automaton,
        ),
        1240: PlanetFeature(
            "VERGE OF DESTRUCTION",
            Emojis.Decoration.alert_icon,
        ),
        1241: PlanetFeature(
            "FRACTURED PLANET",
            Emojis.PlanetFeatures.fractured_planet,
        ),
        1242: PlanetFeature(
            "MOVING PLANET",
            Emojis.Decoration.alert_icon,
        ),
        1252: PlanetFeature(
            "FRACTURED PLANET",
            Emojis.PlanetFeatures.fractured_planet,
        ),
        1268: PlanetFeature(
            "NEGATIVE ENERGY LABRATORY",
            Emojis.PlanetFeatures.negative_energy_labratory,
        ),
        1282: PlanetFeature(
            "HELLDIVER TRAINING FACILITIES",
            Emojis.PlanetFeatures.helldiver_training_facilities,
        ),
        1286: PlanetFeature(
            "MAXIMUM SECURITY CITY CONSTRUCTION SITE",
            Emojis.PlanetFeatures.max_sec_city_construction_site,
        ),
        1287: PlanetFeature(
            "NEW HOPE CITY",
            Emojis.PlanetFeatures.new_hope_city,
        ),
        1291: PlanetFeature(
            "NEW ASPIRATION CITY",
            Emojis.PlanetFeatures.new_aspiration_city,
        ),
        1292: PlanetFeature(
            "NEW YEARNING CITY",
            Emojis.PlanetFeatures.new_yearning_city,
        ),
        1295: PlanetFeature(
            "TYRANNY PARK 2",
            Emojis.PlanetFeatures.tyranny_park_2,
        ),
        1304: PlanetFeature(
            "OUTPOST ALPHA",
            "",
        ),
        1311: PlanetFeature(
            "HIVE WORLD",
            Emojis.PlanetFeatures.hive_world,
        ),
        1324: PlanetFeature(
            "ULTRAMAFIC MINE",
            Emojis.PlanetFeatures.ultramafic_mine,
        ),
        1329: PlanetFeature(
            "LIBERTY DAY CELEBRATION",
            Emojis.Icons.victory,
        ),
        1333: PlanetFeature(
            "E-711 EXTRACTION FACILITY",
            Emojis.PlanetFeatures.e711_extraction_facility,
        ),
        1342: PlanetFeature(
            "CENTRE FOR THE CONFINEMENT OF DISSIDENCE (CECOD)",
            Emojis.PlanetFeatures.cecod,
        ),
        1344: PlanetFeature(
            "PANDORA BASE",
            Emojis.PlanetFeatures.pandora_base,
        ),
        1352: PlanetFeature(
            "CONVENTIONAL BLACK HOLE",
            Emojis.PlanetFeatures.black_hole,
        ),
        1353: PlanetFeature(
            "DATA CENTRE",
            Emojis.Factions.automaton,
        ),
        1355: PlanetFeature(
            "HEAVY ARMOR SURGE",
            Emojis.Factions.automaton,
        ),
        1357: PlanetFeature(
            "DEVASTATOR SURGE",
            Emojis.Factions.automaton,
        ),
        1373: PlanetFeature(
            "CLASS 1 EXOSTORM",
            Emojis.PlanetFeatures.exostorm,
        ),
        1374: PlanetFeature(
            "CLASS 2 EXOSTORM",
            Emojis.PlanetFeatures.exostorm,
        ),
        1375: PlanetFeature(
            "CLASS 3 EXOSTORM",
            Emojis.PlanetFeatures.exostorm,
        ),
        1376: PlanetFeature(
            "VOID",
            Emojis.PlanetFeatures.void,
        ),
        1387: PlanetFeature(
            "COMMUNICATIONS ARRAY",
            Emojis.Factions.automaton,
        ),
        1395: PlanetFeature(
            "TERMINID CONTROL SYSTEM+",
            Emojis.PlanetFeatures.tcs_plus,
        ),
        1396: PlanetFeature(
            "",
            Emojis.Factions.terminids,
        ),
    }

    def get_many(ids: list[int]) -> list[PlanetFeature]:
        results = []
        for id in ids:
            if pf := PlanetFeatures.all.get(id):
                results.append(pf)
        return results
