from re import sub

faction_emojis = {
    "Terminids": "<:tc:1229360523217342475>",
    "Automaton": "<:ac:1229360519689801738>",
    "Illuminate": "<:ic:1246938273734197340>",
    "Humans": "<:hc:1229362077974401024>",
    "MO": "<:moc:1229360522181476403>",
    "empty": "<:nc:1229450109901606994>",
}


def health_bar(
    perc: float,
    race: str | int,
    reverse: bool = False,
    empty_colour="empty",
):
    perc = min(perc, 1)
    if reverse:
        perc = 1 - perc
    faction_numbers = {
        1: "Humans",
        2: "Terminids",
        3: "Automaton",
        4: "Illuminate",
    }
    if race in faction_numbers:
        race = faction_numbers[race]
    health_icon = faction_emojis[race]
    progress_bar = health_icon * int((perc * 10))
    while perc < 1:
        progress_bar += faction_emojis[empty_colour]
        perc += 0.1
    return progress_bar


def short_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, 2)
    return "{:.{}f}{}".format(num, 2, ["", "K", "M", "B", "T", "Q"][magnitude])


def steam_format(content: str):
    replacements = {
        "": [
            "[/h1]",
            "[/h2]",
            "[/h3]",
            "[/h4]",
            "[/h5]",
            "[/h6]",
            "[/quote]",
            "[list]",
            "[list]\n",
            "[/list]",
            "[/*]",
        ],
        "# ": ["[h1]"],
        "## ": ["[h2]"],
        "### ": ["[h3]", "[h4]", "[h5]", "[h6]"],
        "*": ["[i]", "[/i]"],
        "**": ["<i=1>", "<i=3>", "</i>", "[b]", "[/b]"],
        "> ": ["[quote]"],
        "__": ["[u]", "[/u]"],
        "- ": ["[*]\n", "[*]"],
    }
    for replacement, replacees in replacements.items():
        for replacee in replacees:
            content = content.replace(replacee, replacement)
    content = sub(r"\[url=(.+?)](.+?)\[/url\]", r"[\2]\(\1\)", content)
    content = sub(r"\[img\](.*?)\[\/img\]", r"", content)
    content = sub(
        r"\[previewyoutube=(.+);full\]\[/previewyoutube\]",
        "[YouTube](https://www.youtube.com/watch?v=" + r"\1)",
        content,
    )
    content = sub(r"\[img\](.*?\..{3,4})\[/img\]\n\n", "", content)
    return content


def split_long_string(text: str) -> list[str]:
    """Splits a string into 1024 lenth chunks"""
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
