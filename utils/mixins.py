from disnake import Embed


class ReprMixin:
    """Class to clearly represent objects"""

    def __repr__(object):
        items = (f"{k} = {v}" for k, v in object.__dict__.items())
        return f"<{object.__class__.__name__}: {{{', '.join(items)}}}>"


class EmbedReprMixin:
    """Class to clearly represent Embeds"""

    def __repr__(object: Embed):
        items = (f"{k} = {v}" for k, v in object.to_dict().items())
        return f"<{object.__class__.__name__}: {{{', '.join(items)}}}>"
