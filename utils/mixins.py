from disnake import Embed


class ReprMixin:
    """Class to clearly represent objects"""

    def __repr__(object):
        if object.__dict__:
            items = (f"    {k} = {v!r}" for k, v in object.__dict__.items())
        if hasattr(object, "__slots__"):
            if object.__slots__ != ():
                items = (
                    f"    {slot} = {getattr(object, slot)!r}"
                    for slot in object.__slots__
                )
        else:
            items = []
        return f"<{object.__class__.__name__}:\n" + "\n".join(items) + "\n>"


class EmbedReprMixin:
    """Class to clearly represent disnake.Embed objects"""

    def __repr__(object: Embed):
        items = (f"{k} = {v}" for k, v in object.to_dict().items())
        return f"<{object.__class__.__name__}: {{{', '.join(items)}}}>"


class GWEReprMixin:
    """Class to clearly represent data.GalacticWarEffect objects"""

    def __repr__(object):
        if object.__dict__:
            items = (f"    {k} = {v!r}" for k, v in object.__dict__.items())
        if hasattr(object, "__slots__"):
            if object.__slots__ != ():
                items = (
                    f"    {slot} = {getattr(object, slot)!r}"
                    for slot in object.__slots__
                    if getattr(object, slot) != None
                )
                empty_slots = [
                    slot for slot in object.__slots__ if getattr(object, slot) == None
                ]
        else:
            items = []
        return (
            f"<{object.__class__.__name__}:\n"
            + "\n".join(items)
            + f"\n>"
            + f"\nEMPTY ATTRIBUTES: {empty_slots}"
        )

    def pretty_print(self):
        base_str = (
            f"**{self.id}**:"
            f"\n    Effect Name: **{self.planet_effect['name']}**"
            f"\n    {self.effect_description['simplified_name']}"
        )
        if self.planet_effect["description_long"]:
            base_str += f"\n    Effect Description: **{self.planet_effect['description_long']}**"
        if self.planet_effect["description_short"]:
            base_str += f"\n    Effect Description: **{self.planet_effect['description_short']}**"
        if self.faction:
            base_str += f"\n    Faction: **{self.faction.full_name}**"
        if self.found_enemy:
            base_str += f"\n    Enemy Found: **{self.found_enemy}**"
        if self.found_stratagem:
            base_str += f"\n    Stratagem Found: **{self.found_stratagem}**"
        if self.found_booster:
            base_str += f"\n    Booster Found: **{self.found_booster['name']}**"
        if self.count:
            base_str += f"\n    Count: **{self.count:+}**"
        if self.percent:
            base_str += f"\n    Percent: **{self.percent:+}%**"
        return base_str
