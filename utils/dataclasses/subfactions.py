from dataclasses import dataclass
from utils.dataclasses import Faction, Factions
from utils.emojis import Emojis


@dataclass
class Subfaction:
    eng_name: str
    emoji: str
    division_id: int
    poi_id: int
    faction: Faction

    def __hash__(self):
        return hash(self.division_id)

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.division_id == value.division_id


@dataclass
class Subfactions:
    THE_JET_BRIGADE = Subfaction(
        "JET BRIGADE",
        Emojis.Subfactions.jet_brigade,
        1202,
        1203,
        Factions.automaton,
    )
    PREDATOR_STRAIN = Subfaction(
        "PREDATOR STRAIN",
        Emojis.Subfactions.predator_strain,
        1243,
        1245,
        Factions.terminids,
    )
    SPORE_BURST_STRAIN = Subfaction(
        "SPORE BURST STRAIN",
        Emojis.Subfactions.spore_burst_strain,
        1244,
        1386,
        Factions.terminids,
    )
    INCINERATION_CORPS = Subfaction(
        "INCINERATION CORPS",
        Emojis.Subfactions.incineration_corps,
        1248,
        1249,
        Factions.automaton,
    )
    THE_GREAT_HOST = Subfaction(
        "THE GREAT HOST",
        Emojis.Subfactions.the_great_host,
        1269,
        1269,
        Factions.illuminate,
    )
    RUPTURE_STRAIN = Subfaction(
        "RUPTURE STRAIN",
        Emojis.Subfactions.rupture_strain,
        1303,
        1310,
        Factions.terminids,
    )
    DRAGONROACHES = Subfaction(
        "DRAGONROACHES",
        Emojis.Subfactions.dragonroaches,
        1306,
        1309,
        Factions.terminids,
    )
    HIVE_LORDS = Subfaction(
        "HIVE LORDS",
        Emojis.Subfactions.hive_lords,
        1307,
        1308,
        Factions.terminids,
    )
    CYBORGS = Subfaction(
        "CYBORGS",
        Emojis.Subfactions.cyborgs,
        1360,
        1361,
        Factions.automaton,
    )
    MINDLESS_MASSES = Subfaction(
        "MINDLESS MASSES",
        Emojis.Subfactions.mindless_masses,
        1377,
        1378,
        Factions.illuminate,
    )
    APPROPRIATORS = Subfaction(
        "APPROPRIATORS",
        Emojis.Subfactions.appropriators,
        1380,
        1379,
        Factions.illuminate,
    
    )

    _all: tuple[Subfaction] = (
        THE_JET_BRIGADE,
        PREDATOR_STRAIN,
        SPORE_BURST_STRAIN,
        INCINERATION_CORPS,
        THE_GREAT_HOST,
        RUPTURE_STRAIN,
        DRAGONROACHES,
        HIVE_LORDS,
        CYBORGS,
        MINDLESS_MASSES,
        APPROPRIATORS,
    )

    @classmethod
    def get_from_effects_list(cls, active_effects: set) -> set[Subfaction]:
        subfactions = set(
            [
                sf
                for sf in cls._all
                if sf.division_id in (ae.id for ae in active_effects)
            ]
        )
        return subfactions

    @classmethod
    def get_from_dbsf_list(cls, dbsf_list: list) -> list[Subfaction] | Subfaction:
        sfs = [sf for sf in cls._all if sf.division_id in (ae.id for ae in dbsf_list)]
        return sfs if len(sfs) > 1 else sfs[0]
