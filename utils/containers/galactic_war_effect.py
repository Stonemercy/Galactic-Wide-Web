from disnake import Colour, ui
from utils.api_wrapper.models import GalacticWarEffect, Planet
from utils.dataclasses import Subfactions
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION
class GWEContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        gwe: GalacticWarEffect,
        planets_with_gwe: list[Planet] | str,
        with_pretty_print: bool = True,
    ):
        components = []
        self.attachments = []
        components.append(
            ui.TextDisplay(f"{gwe.id} - {gwe.effect_description['simplified_name']}")
        )
        if gwe.name:
            components.append(ui.TextDisplay(f"{gwe.name}"))
        if gwe.short_description:
            components.append(ui.TextDisplay(f"{gwe.short_description}"))
        if gwe.long_description:
            components.append(ui.TextDisplay(f"{gwe.long_description}"))
        if gwe.fluff_description:
            components.append(ui.TextDisplay(f"{gwe.fluff_description}"))
        if gwe.resource:
            components.append(ui.TextDisplay(f"{gwe.resource}"))

        if gwe.found_enemy:
            enemy = str(gwe.found_enemy)
            subfaction = [
                sf for sf in Subfactions._all if sf.eng_name.lower() == enemy.lower()
            ]
            if subfaction:
                sf = subfaction[0]
                enemy_text = f"**{sf.eng_name}** {sf.emoji}"
            else:
                enemy_text = f"**{gwe.found_enemy}**"
            components.append(ui.TextDisplay(f"ENEMY DETECTED - {enemy_text}"))

        if gwe.found_stratagem:
            components.append(
                ui.TextDisplay(f"STRATAGEM DETECTED - **{gwe.found_stratagem}**")
            )

        if gwe.found_booster:
            components.append(
                ui.TextDisplay(f"BOOSTER DETECTED - **{gwe.found_booster['name']}**")
            )

        active_planets = ""
        if type(planets_with_gwe) == str:
            active_planets = "-# ALL PLANETS"
        elif planets_with_gwe:
            active_planets = "-# " + "\n-# ".join(
                [p.names.get("en-GB", str(p.index)) for p in planets_with_gwe]
            )
        else:
            active_planets = "-# None"
        components.append(ui.TextDisplay(f"Active on\n{active_planets}"))
        if with_pretty_print:
            components.append(ui.Separator())
            components.append(ui.TextDisplay(f"```py\n{gwe}```"))

        super().__init__(
            *components,
            accent_colour=Colour.dark_theme(),
        )
