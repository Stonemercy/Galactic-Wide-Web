from disnake import Embed


class ReprMixin:
    """Class to clearly represent objects"""

    def __repr__(object):
        if object.__dict__:
            items = (f"    {k} = {v!r}" for k, v in object.__dict__.items())
        if hasattr(object, "__slots__"):
            items = (
                f"    {slot} = {getattr(object, slot)!r}" for slot in object.__slots__
            )
        else:
            items = []
        return f"<{object.__class__.__name__}:\n" + "\n".join(items) + "\n>"


class EmbedReprMixin:
    """Class to clearly represent disnake.Embeds"""

    def __repr__(object: Embed):
        items = (f"{k} = {v}" for k, v in object.to_dict().items())
        return f"<{object.__class__.__name__}: {{{', '.join(items)}}}>"
