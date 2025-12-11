from disnake import Colour, ui
from utils.api_wrapper.models import GalacticWarEffect, Planet
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

        if gwe.found_enemy:
            components.append(ui.TextDisplay(f"ENEMY DETECTED - **{gwe.found_enemy}**"))

        if gwe.found_stratagem:
            components.append(
                ui.TextDisplay(f"STRATAGEM DETECTED - **{gwe.found_stratagem[0]}**")
            )

        if gwe.found_booster:
            components.append(
                ui.TextDisplay(f"BOOSTER DETECTED - **{gwe.found_booster['name']}**")
            )

        if gwe.count:
            word = "INCREASED" if gwe.count > 0 else "DECREASED"
            components.append(ui.TextDisplay(f"{word} BY {gwe.count}"))

        if gwe.percent != None:
            word = "INCREASED" if gwe.percent > 0 else "DECREASED"
            components.append(ui.TextDisplay(f"{word} BY {gwe.percent}%"))

        active_planets = ""
        if type(planets_with_gwe) == str:
            active_planets = "-# ALL PLANETS"
        elif planets_with_gwe:
            active_planets = "-# " + "\n-# ".join([p.name for p in planets_with_gwe])
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
