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
