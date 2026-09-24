from dataclasses import dataclass, field
from utils.dataclasses import Faction, Factions
from utils.emojis import Emojis


@dataclass
class Subfaction:
    resource_hash: int
    eng_name: str
    emoji: str
    division_effect_id: int
    token_effect_id: int
    faction: Faction
    enemy_ids: list[int] = field(default_factory=list)

    def __hash__(self):
        return hash(self.resource_hash)

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.resource_hash == value.resource_hash


@dataclass
class Subfactions:
    THE_JET_BRIGADE = Subfaction(
        2922304745,
        "JET BRIGADE",
        Emojis.Subfactions.jet_brigade,
        1202,
        1203,
        Factions.automaton,
    )
    PREDATOR_STRAIN = Subfaction(
        2313485354,
        "PREDATOR STRAIN",
        Emojis.Subfactions.predator_strain,
        1243,
        1245,
        Factions.terminids,
        [
            3029738043,
            1229149324,
            4106686024,
            112786645,
        ],
    )
    SPORE_BURST_STRAIN = Subfaction(
        2745424799,
        "SPORE BURST STRAIN",
        Emojis.Subfactions.spore_burst_strain,
        1244,
        1386,
        Factions.terminids,
        [
            1210082392,
            333947844,
            2842755544,
            1428114468,
            2745424799,
            2115960485,
            512390556,
            1939105083,
            3764892677,
        ],
    )
    INCINERATION_CORPS = Subfaction(
        1703232728,
        "INCINERATION CORPS",
        Emojis.Subfactions.incineration_corps,
        1248,
        1249,
        Factions.automaton,
        [
            2861014363,
            1127649354,
            585039032,
            75849082,
            1262004523,
            3498181594,
            1784440447,
            364931179,
            2090691137,
            1181272016,
        ],
    )
    THE_GREAT_HOST = Subfaction(
        0,  # doesn't have a type 40 effect
        "THE GREAT HOST",
        Emojis.Subfactions.the_great_host,
        1269,
        1269,
        Factions.illuminate,
    )
    RUPTURE_STRAIN = Subfaction(
        2423391486,
        "RUPTURE STRAIN",
        Emojis.Subfactions.rupture_strain,
        1303,
        1310,
        Factions.terminids,
        [
            3903153972,
            2270698456,
            953392591,
        ],
    )
    DRAGONROACHES = Subfaction(
        2681574458,
        "DRAGONROACHES",
        Emojis.Subfactions.dragonroaches,
        1306,
        1309,
        Factions.terminids,
        [1378841226],
    )
    HIVE_LORDS = Subfaction(
        424440415,
        "HIVE LORDS",
        Emojis.Subfactions.hive_lords,
        1307,
        1308,
        Factions.terminids,
        [3929716830],
    )
    CYBORGS = Subfaction(
        141977090,
        "CYBORGS",
        Emojis.Subfactions.cyborgs,
        1360,
        1361,
        Factions.automaton,
        [
            23741406,
            1371180916,
            4066406510,
        ],
    )
    MINDLESS_MASSES = Subfaction(
        35348659,
        "MINDLESS MASSES",
        Emojis.Subfactions.mindless_masses,
        1377,
        1378,
        Factions.illuminate,
    )
    APPROPRIATORS = Subfaction(
        3792924074,
        "APPROPRIATORS",
        Emojis.Subfactions.appropriators,
        1380,
        1379,
        Factions.illuminate,
        [
            3776682558,
            1870840792,
            3621116014,
        ],
    )
    INVASION_FLEET = Subfaction(
        872028856,
        "INVASION FLEET",
        Emojis.Subfactions.invasion_fleet,
        1413,
        1414,
        Factions.illuminate,
    )
    HEAVY_SEAF_PRESENCE = Subfaction(
        3126357841,
        "HEAVY SEAF PRESENCE",
        Emojis.Subfactions.heavy_seaf_presence,
        1401,
        1400,
        Factions.humans,
    )
    VOTE_SNATCHERS = Subfaction(
        4253783814,
        "VOTE SNATCHERS",
        Emojis.Subfactions.vote_snatchers,
        1402,
        1403,
        Factions.illuminate,
        [
            2118086817,
            3922421925,
        ],
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
        INVASION_FLEET,
        HEAVY_SEAF_PRESENCE,
        VOTE_SNATCHERS,
    )

    @classmethod
    def get_from_effects_list(cls, active_effects: set) -> set[Subfaction]:
        return set(
            [
                sf
                for sf in cls._all
                if sf.resource_hash in (ae.resource_hash for ae in active_effects)
            ]
        )

    @classmethod
    def get_from_enemy_id(cls, enemy_id: int | None) -> Subfaction | None:
        if enemy_id is None:
            return None
        return next((sf for sf in cls._all if enemy_id in sf.enemy_ids), None)
