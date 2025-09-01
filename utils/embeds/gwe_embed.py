from data.lists import stratagem_id_dict
from disnake import Colour, Embed
from utils.data import GalacticWarEffect, Planet
from utils.mixins import EmbedReprMixin


class GalacticWarEffectEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        gwe: GalacticWarEffect,
        planets_with_gwe: list[Planet] | str,
        json_dict: dict,
    ):
        super().__init__(
            title=f"{gwe.id} - {gwe.effect_description['name']}",
            description=gwe.effect_description["description"],
            colour=Colour.dark_theme(),
        )
        if enemy := json_dict["enemies"]["enemy_ids"].get(
            str(gwe.hash_id or gwe.resource_hash)
        ):
            self.add_field("ENEMY DETECTED", enemy, inline=False)
        if stratagem := stratagem_id_dict.get(gwe.mix_id):
            self.add_field("STRATAGEM DETECTED", stratagem, inline=False)
        if booster := json_dict["items"]["boosters"].get(str(gwe.mix_id)):
            self.add_field("BOOSTER DETECTED", booster["name"], inline=False)
        if gwe.count:
            self.add_field("INCREASED/DECREASED BY", f"{gwe.count:+}", inline=False)
        if gwe.percent != None:
            self.add_field("INCREASED/DECREASED BY", f"{gwe.percent:+}%", inline=False)
        active_planets = ""
        if type(planets_with_gwe) == str:
            active_planets = "-# ALL PLANETS"
        elif planets_with_gwe:
            active_planets = "-# " + "\n-# ".join([p.name for p in planets_with_gwe])
        else:
            active_planets = "-# None"
        self.add_field("Active on", active_planets, inline=False)
        self.add_field("", f"```py\n{gwe.__repr__()}```")
