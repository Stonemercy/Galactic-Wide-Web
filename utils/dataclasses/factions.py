from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class Faction:
    number: int
    full_name: str
    singular: str
    plural: str
    colour: tuple

    @property
    def emoji(self):
        return getattr(Emojis.Factions, self.full_name.lower())

    def __hash__(self):
        return hash(self.number)


class Factions:
    humans: Faction = Faction(
        1,
        "Humans",
        "human",
        "humans",
        (107, 183, 234),
    )
    terminids: Faction = Faction(
        2,
        "Terminids",
        "terminid",
        "terminids",
        (234, 167, 43),
    )
    automaton: Faction = Faction(
        3,
        "Automaton",
        "automaton",
        "automaton",
        (252, 108, 115),
    )
    illuminate: Faction = Faction(
        4,
        "Illuminate",
        "illuminate",
        "illuminate",
        (107, 59, 187),
    )
    all: list[Faction] = [
        humans,
        terminids,
        automaton,
        illuminate,
    ]

    @staticmethod
    def get_from_identifier(name: str = None, number: int = None) -> Faction | None:
        matching_list = []
        if name:
            matching_list = [
                f for f in Factions.all if f.full_name.lower() == name.lower()
            ]
        elif number:
            matching_list = [f for f in Factions.all if f.number == number]
        return matching_list[0] if matching_list != [] else None
