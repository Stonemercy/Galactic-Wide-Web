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
