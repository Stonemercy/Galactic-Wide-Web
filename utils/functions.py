from math import floor
from re import sub, DOTALL
from utils.emojis import Emojis


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
    health_icon = getattr(Emojis.FactionColours, race.lower())
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


def steam_format(text: str):
    # Remove empty paragraphs and standalone [p][/p] tags
    text = sub(r"\[p\]\[/p\]", "\n", text)
    text = sub(r"\[p\]\s*\[/p\]", "\n", text)

    # Convert headers with better spacing
    text = sub(r"\[h1\](.*?)\[/h1\]", r"# \1\n", text)
    text = sub(r"\[h2\](.*?)\[/h2\]", r"## \1\n", text)
    text = sub(r"\[h3\](.*?)\[/h3\]", r"### \1\n", text)
    text = sub(r"\[p\]\[b\](.*?)\[/b\]\[/p\]", r"### \1\n", text)

    # Convert bold and italic text
    text = sub(r"\[b\](.*?)\[/b\]", r"**\1**", text)
    text = sub(r"\[i\](.*?)\[/i\]", r"*\1*", text)

    # Convert URLs
    text = sub(r'\[url="(.*?)"\](.*?)\[/url\]', r"[\2](\1)", text)
    text = sub(r"\[url\](.*?)\[/url\]", r"\1", text)

    # Convert lists with better formatting
    # Handle list items with paragraphs
    text = sub(r"\[\*\]\[p\](.*?)\[/p\]\[/\*\]", r"• \1", text, flags=DOTALL)
    text = sub(r"\[\*\](.*?)\[/\*\]", r"• \1\n", text, flags=DOTALL)

    # Remove list container tags
    text = sub(r"\[list\]", "", text)
    text = sub(r"\[/list\]", "\n", text)

    # Convert remaining paragraph tags - handle them differently for better formatting
    # First, handle paragraphs that are standalone (not in lists)
    text = sub(r"\[p\](.*?)\[/p\](?!\s*\[)", r"\1\n", text, flags=DOTALL)
    # Then handle any remaining paragraph tags
    text = sub(r"\[p\](.*?)\[/p\]", r"\1\n", text, flags=DOTALL)

    # Clean up bullet point formatting and ensure proper line breaks
    text = sub(r"•\s*\n\s*", "• ", text)  # Remove newlines immediately after bullets
    text = sub(
        r"(• .*?)\n(?=• )", r"\1\n", text
    )  # Ensure single line breaks between bullets

    # Fix the overview section formatting - convert bullet points to a more readable format
    # Look for the pattern where we have bullets right after headers
    text = sub(
        r"(# \*\*Overview\*\*)\n(• .*?)(?=\n\n|\n#)",
        lambda m: m.group(1) + "\n" + m.group(2).replace("• ", "• "),
        text,
        flags=DOTALL,
    )

    # Improve line breaks and spacing
    text = sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Multiple newlines to double
    text = sub(r"^\s*\n+", "", text)  # Remove leading newlines
    text = sub(r"\n+\s*$", "", text)  # Remove trailing newlines

    # Add proper spacing around sections
    text = sub(r"(# .*?)\n+(?=•)", r"\1\n", text)  # H1 header to bullets
    text = sub(r"(## .*?)\n+(?=•)", r"\1\n", text)  # Header to bullets
    text = sub(r"(### .*?)\n+(?=•)", r"\1\n", text)  # Subheader to bullets
    text = sub(r"(\n• .*?)\n+(?=#)", r"\1\n\n", text)  # Bullets to H1 header
    text = sub(r"(\n• .*?)\n+(?=##)", r"\1\n\n", text)  # Bullets to header
    text = sub(r"(\n• .*?)\n+(?=###)", r"\1\n\n", text)  # Bullets to subheader

    # Add spacing between headers and regular paragraphs
    text = sub(r"(# .*?)\n+(?=\w)", r"\1\n", text)  # H1 to paragraph
    text = sub(r"(## .*?)\n+(?=\w)", r"\1\n", text)  # H2 to paragraph
    text = sub(r"(### .*?)\n+(?=\w)", r"\1\n", text)  # H3 to paragraph

    # Add spacing between paragraphs and headers
    text = sub(r"(\w.*?)\n+(?=#)", r"\1\n\n", text)  # Paragraph to H1
    text = sub(r"(\w.*?)\n+(?=##)", r"\1\n\n", text)  # Paragraph to H2
    text = sub(r"(\w.*?)\n+(?=###)", r"\1\n\n", text)  # Paragraph to H3

    # Fix spacing between sections
    text = sub(r"(\n• .*?)\n+(?=\n• )", r"\1\n", text)
    text = sub(r"(# .*?)\n+(# )", r"\1\n\n\2", text)  # H1 to H1
    text = sub(r"(## .*?)\n+(## )", r"\1\n\n\2", text)  # H2 to H2
    text = sub(r"(### .*?)\n+(### )", r"\1\n\n\2", text)  # H3 to H3

    # Clean up any remaining tags that weren't converted
    text = sub(r"\[.*?\]", "", text)

    # Final cleanup - ensure consistent spacing and fix any remaining formatting issues
    text = sub(r"\n{3,}", "\n\n", text)  # No more than 2 consecutive newlines
    text = sub(
        r"(\n• .*?)\n{2,}(?=• )", r"\1\n", text
    )  # Single space between bullet points

    # Clean up whitespace around bullet points
    text = sub(r"• +", "• ", text)  # Remove extra spaces after bullets
    text = sub(r"• • +", "• ", text)  # Remove extra bullets
    text = sub(r"\n+• ", "\n• ", text)  # Ensure single newline before bullets
    text = sub(r"• ", "\n• ", text)  # Ensure single newline before bullets

    # Ensure proper spacing for standalone paragraphs
    text = sub(r"(\w.*?)\n(\w)", r"\1\n\n\2", text)  # Add spacing between paragraphs
    text = sub(r"\n\n\n", "\n\n", text)  # But don't allow triple spacing

    return text


def dispatch_format(text: str):
    replacements = ["<i=1>", "<I=1>", "<i=3>", "</i>"]
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
