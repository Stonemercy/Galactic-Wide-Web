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
