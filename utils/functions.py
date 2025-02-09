from re import sub


def health_bar(perc: float, race: str | int, reverse: bool = False):
    perc = perc * 10
    if reverse:
        perc = 10 - perc
    perc = int(perc)
    faction_numbers = {
        1: "Humans",
        2: "Terminids",
        3: "Automaton",
        4: "Illuminate",
    }
    if race in faction_numbers:
        race = faction_numbers[race]
    health_icon = {
        "Terminids": "<:tc:1229360523217342475>",
        "Automaton": "<:ac:1229360519689801738>",
        "Illuminate": "<:ic:1246938273734197340>",
        "Humans": "<:hc:1229362077974401024>",
        "MO": "<:moc:1229360522181476403>",
    }[race]
    progress_bar = health_icon * perc
    while perc < 10:
        progress_bar += "<:nc:1229450109901606994>"
        perc += 1
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
