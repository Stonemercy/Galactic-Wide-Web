from math import floor
from utils.dataclasses.factions import Faction
from utils.emojis import Emojis


def health_bar(
    perc: float,
    faction: Faction | str,
    reverse: bool = False,
    empty_colour="empty",
):
    perc = min(perc, 1)
    if reverse:
        perc = 1 - perc
    name_to_check = (
        faction.full_name.lower() if type(faction) == Faction else faction.lower()
    )
    health_icon = getattr(Emojis.FactionColours, name_to_check)
    perc_round = floor(perc * 10)
    progress_bar = health_icon * perc_round
    while perc_round < 10:
        progress_bar += getattr(Emojis.FactionColours, empty_colour.lower())
        perc_round += 1
    return progress_bar


def short_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, 2)
    return "{:.{}f}{}".format(num, 2, ["", "K", "M", "B", "T", "Q"][magnitude])


def dispatch_format(text: str):
    replacements = [
        "<i=1>",
        "<I=1>",
        "<i=3>",
        "</i>",
        "</i=1>",
        "<i=1",
        "</i=3>",
        "<i>",
    ]
    for replacement in replacements:
        text = text.replace(replacement, "**")

    return text


def split_long_string(text: str) -> list[str]:
    """Splits a string into 1024 length chunks"""
    parts = []
    while len(text) > 1024:
        split_index = text.rfind("\n", 0, 1024)
        if split_index == -1:
            split_index = 1024
        parts.append(text[:split_index].rstrip())
        text = text[split_index:].lstrip("\n")
    if text:
        parts.append(text)
    return parts


def compare_translations(reference: dict, target: dict, path="") -> list[str]:
    """Compares dictionaries and returns a list of all differences with their keys"""
    diffs = []
    all_keys = set(reference.keys()).union(target.keys())
    for key in all_keys:
        full_path = f"{path}.{key}" if path else key
        ref_val = reference.get(key)
        tgt_val = target.get(key)
        if isinstance(ref_val, dict) and isinstance(tgt_val, dict):
            diffs.extend(
                compare_translations(reference=ref_val, target=tgt_val, path=full_path)
            )
        elif key not in target:
            diffs.append(f"Missing in target: `{full_path}`")
        elif key not in reference:
            diffs.append(f"Extra in target: `{full_path}`")
        elif ref_val == tgt_val:
            diffs.append(f"Untranslated: `{full_path}`")
    return diffs


def out_of_normal_range(before: int | float, after: int | float) -> bool:
    """Returns a bool based on if the `after` is 25% more or less than the `before`

    Args:
        before (`int` | `float`)
        after (`int` | `float`)

    Returns:
        `bool`
    """
    return after < before * 0.75 or after > before * 1.25
