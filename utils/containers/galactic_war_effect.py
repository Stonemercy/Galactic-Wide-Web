from disnake import Colour, ui
from utils.data import GalacticWarEffect, Planet
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION
class GWEContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        gwe: GalacticWarEffect,
        planets_with_gwe: list[Planet] | str,
    ):
        components = []
        self.attachments = []
        components.append(
            ui.TextDisplay(f"{gwe.id} - {gwe.effect_description['simplified_name']}")
        )
        components.append(ui.TextDisplay(f"-# {gwe.effect_description['description']}"))

        if gwe.found_enemy:
            components.append(ui.TextDisplay(f"ENEMY DETECTED - **{gwe.found_enemy}**"))

        if gwe.found_stratagem:
            components.append(
                ui.TextDisplay(f"STRATAGEM DETECTED - **{gwe.found_stratagem}**")
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
        components.append(ui.Separator())
        components.append(ui.TextDisplay(f"```py\n{gwe}```"))

        super().__init__(
            *components,
            accent_colour=Colour.dark_theme(),
        )
