from disnake import Colour
from disnake.ui import Container, Separator, TextDisplay
from utils.api_wrapper.models import GalacticWarEffect, Planet
from utils.dataclasses import PlanetFeatures, Subfactions
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION
class GWEContainer(Container, ReprMixin):
    def __init__(
        self,
        gwe: GalacticWarEffect,
        planets_with_gwe: list[Planet] | str,
        with_planets_list: bool = True,
        with_pretty_print: bool = True,
    ):
        self.components = []
        self.components.append(
            TextDisplay(f"{gwe.id} - {gwe.effect_description['simplified_name']}")
        )
        content = ""
        if gwe.name:
            content += f"\n**{gwe.name}**"
        if gwe.short_description:
            content += f"\n{gwe.short_description}"
        if gwe.long_description:
            content += f"\n-# {gwe.long_description}"
        if gwe.fluff_description:
            content += f"\n-# {gwe.fluff_description}"
        if gwe.resource:
            content += f"\n{gwe.resource}"

        if feature := PlanetFeatures.all.get(gwe.id):
            content += f"\n**{feature.name}** {feature.emoji}"

        if subfaction_poi := next(
            (sf for sf in Subfactions._all if sf.token_effect_id == gwe.id), None
        ):
            content += f"\n**{subfaction_poi.eng_name}** {subfaction_poi.emoji}"

        if gwe.found_enemy and gwe.found_enemy.upper() not in content:
            subfaction = [
                sf for sf in Subfactions._all if sf.resource_hash == gwe.resource_hash
            ]
            if subfaction:
                sf = subfaction[0]
                enemy_text = f"**{sf.eng_name}** {sf.emoji}"
            else:
                enemy_text = f"**{gwe.found_enemy}**"
            content += f"\nEnemy: {enemy_text}"

        if gwe.found_stratagem and gwe.found_stratagem not in content:
            content += f"\nStratagem: **{gwe.found_stratagem}**"

        if gwe.stratagem_category:
            content += f"\nStratagem Category: **{gwe.stratagem_category}**"

        if gwe.found_booster and gwe.found_booster not in content:
            content += f"\nBooster: **{gwe.found_booster}**"

        if gwe.count:
            count = "Count" if gwe.effect_type != 32 else "Uses per mission"
            content += f"\n{count}: **{gwe.count:+,}**"
        if gwe.percent:
            percent = gwe.percent
            match gwe.effect_type:
                case 1 | 72:
                    percent -= 100
            content += f"\nPercent: **{percent:+,}%**"

        if with_planets_list:
            active_planets = ""
            if isinstance(planets_with_gwe, str):
                active_planets = "-# ALL PLANETS"
            elif planets_with_gwe:
                active_planets = "-# " + "\n-# ".join(
                    [f"#{p.index} - {p.name}" for p in planets_with_gwe]
                )
            else:
                active_planets = "-# None"
            content += f"\n**Active on**\n{active_planets}"

        self.components.append(TextDisplay(content))

        if with_pretty_print:
            self.components.append(Separator())
            self.components.append(TextDisplay(f"```py\n{gwe}```"))

        super().__init__(
            *self.components,
            accent_colour=Colour.dark_theme(),
        )
