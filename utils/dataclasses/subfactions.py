from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class Subfaction:
    eng_name: str
    emoji: str
    division_id: int

    def __hash__(self):
        return hash(self.division_id)

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.division_id == value.division_id


@dataclass
class Subfactions:
    THE_JET_BRIGADE = Subfaction("JET BRIGADE", Emojis.Subfactions.jet_brigade, 1202)
    PREDATOR_STRAIN = Subfaction(
        "PREDATOR STRAIN", Emojis.Subfactions.predator_strain, 1243
    )
    GLOOM_BURSTER_STRAIN = Subfaction(
        "GLOOM BURSTER STRAIN", Emojis.Subfactions.gloom_burster_strain, 1244
    )
    INCINERATION_CORPS = Subfaction(
        "INCINERATION CORPS", Emojis.Subfactions.incineration_corps, 1248
    )
    THE_GREAT_HOST = Subfaction(
        "THE GREAT HOST", Emojis.Subfactions.the_great_host, 1269
    )
    RUPTURE_STRAIN = Subfaction(
        "RUPTURE STRAIN", Emojis.Subfactions.rupture_strain, 1303
    )
    DRAGONROACHES = Subfaction("DRAGONROACHES", Emojis.Subfactions.dragonroaches, 1306)
    HIVE_LORDS = Subfaction("HIVE LORDS", Emojis.Subfactions.hive_lords, 1307)
    CYBORGS = Subfaction("CYBORGS", Emojis.Subfactions.cyborgs, 1360)
    MINDLESS_MASSES = Subfaction(
        "MINDLESS MASSES", Emojis.Subfactions.mindless_masses, 1377
    )  # fix emoji
    APPROPRIATORS = Subfaction(
        "APPROPRIATORS", Emojis.Subfactions.appropriators, 1380
    )  # fix emoji

    _all = (
        THE_JET_BRIGADE,
        PREDATOR_STRAIN,
        GLOOM_BURSTER_STRAIN,
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
