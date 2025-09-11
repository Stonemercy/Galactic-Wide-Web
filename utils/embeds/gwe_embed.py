from data.lists import stratagem_id_dict
from disnake import Colour, Embed, File
from utils.data import GalacticWarEffect, Planet
from utils.mixins import EmbedReprMixin


class GalacticWarEffectEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        gwe: GalacticWarEffect,
        planets_with_gwe: list[Planet] | str,
    ):
        super().__init__(
            title=f"{gwe.id} - {gwe.effect_description['simplified_name']}",
            description=gwe.effect_description["description"],
            colour=Colour.dark_theme(),
        )
        if gwe.found_enemy:
            self.add_field("ENEMY DETECTED", gwe.found_enemy, inline=False)
            try:
                self.set_thumbnail(
                    file=File(
                        f"resources/Planet Effects/{gwe.found_enemy.replace(' ', '_')}.png"
                    )
                )
            except:
                pass
        if gwe.found_stratagem:
            self.add_field("STRATAGEM DETECTED", gwe.found_stratagem, inline=False)
            strat_path = (
                gwe.found_stratagem.replace("/", "_").replace(" ", "_").replace('"', "")
            )
            self.set_thumbnail(file=File(f"resources/stratagems/{strat_path}.png"))
        if gwe.found_booster:
            self.add_field(
                "BOOSTER DETECTED",
                f"{gwe.found_booster['name']}\n-# {gwe.found_booster['description']}",
                inline=False,
            )
            self.set_thumbnail(
                file=File(
                    f"resources/boosters/{gwe.found_booster['name'].replace(' ', '_')}.png"
                )
            )
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
