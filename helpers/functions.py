def health_bar(current_health: int, max_health: int, atk_def: str = "def"):
    if atk_def not in ["atk", "def"]:
        return ""
    prog_dict = {
        "def": {10: "🟦", 7: "🟩", 5: "🟨", 3: "🟧", 1: "🟥"},
        "atk": {9: "🟥", 6: "🟧", 4: "🟨", 2: "🟩", 1: "🟦"},
    }
    prog_dict = prog_dict[atk_def]
    perc = int((current_health / max_health) * 10)
    prog_ico = ""
    for i in prog_dict:
        if perc >= i:
            prog_ico = prog_dict[i]
            break
        else:
            continue
    progress_bar = prog_ico * perc
    while len(progress_bar) < 10:
        progress_bar += "⬛"
    return progress_bar
