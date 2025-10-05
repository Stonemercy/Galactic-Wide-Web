def dict_empty(source: dict):
    for v in source.values():
        if type(v) == dict:
            if not dict_empty(v):
                return False
        else:
            return False
    return True
