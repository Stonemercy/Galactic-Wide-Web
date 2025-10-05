from math import floor
from utils.dataclasses import Faction
from utils.emojis import Emojis


def health_bar(
    perc: float,
    faction: Faction | str,
    reverse: bool = False,
    empty_colour: str = "empty",
    anim: bool = False,
    increasing: bool = False,
):
    perc = min(perc, 1)
    if reverse:
        perc = 1 - perc
    if anim:
        health_icon = getattr(
            Emojis.FactionColoursAnim,
            (
                f"{faction.full_name.lower()}_{'increasing' if increasing else 'decreasing'}"
                if type(faction) == Faction
                else f"{faction.lower()}_{'increasing' if increasing else 'decreasing'}"
            ),
        )
    else:
        health_icon = getattr(
            Emojis.FactionColours,
            (
                faction.full_name.lower()
                if type(faction) == Faction
                else faction.lower()
            ),
        )
    perc_round = floor(perc * 10)
    progress_bar = health_icon * perc_round
    while perc_round < 10:
        progress_bar += getattr(Emojis.FactionColours, empty_colour.lower())
        perc_round += 1
    return progress_bar
