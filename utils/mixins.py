from disnake import Embed


class ReprMixin:
    """Class to clearly represent objects"""

    def __repr__(object):
        if object.__dict__:
            items = (f"{k} = {v}" for k, v in object.__dict__.items())
        elif object.__slots__:
            items = (f"{slot} = {getattr(object, slot)}" for slot in object.__slots__)
        return f"<{object.__class__.__name__}: {{{', '.join(items)}}}>"


class EmbedReprMixin:
    """Class to clearly represent disnake.Embeds"""

    def __repr__(object: Embed):
        items = (f"{k} = {v}" for k, v in object.to_dict().items())
        return f"<{object.__class__.__name__}: {{{', '.join(items)}}}>"
