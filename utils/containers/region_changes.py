from data.lists import ATTACK_EMBED_ICONS, VICTORY_ICONS, CUSTOM_COLOURS
from disnake import Colour, ui
from utils.data import GalacticWarEffect, Planet
from utils.dataclasses import PlanetEffects, RegionChangesJson, SpecialUnits
from utils.emojis import Emojis
from utils.interactables import HDCButton
from utils.mixins import ReprMixin


class RegionChangesContainer(ui.Container, ReprMixin):
    def __init__(self, container_json: RegionChangesJson):
        self.container_json = container_json
        self.colour = Colour.dark_theme()
        self.title = [
            ui.TextDisplay(
                f"{Emojis.Decoration.left_banner} {self.container_json.container['title']} {Emojis.Decoration.right_banner}",
            )
        ]
        self.victories = [
            ui.Section(
                ui.TextDisplay(
                    f"## {self.container_json.container['victories']} {Emojis.Icons.victory}"
                ),
                accessory=HDCButton(),
            )
        ]
        self.new_regions = [
            ui.Section(
                ui.TextDisplay(
                    f"## {self.container_json.container['new_regions']} {Emojis.Icons.new_icon}"
                ),
                accessory=HDCButton(),
            )
        ]
        self.container_colours = [
            {"list": self.victories, "colour": Colour.brand_green()},
            {
                "list": self.new_regions,
                "colour": Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
            },
        ]

    def _add_special_units(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        if special_units := SpecialUnits.get_from_effects_list(
            active_effects=active_effects
        ):
            for su_name, su_emoji in special_units:
                text_display.content += f"\n> -# {su_emoji} **{self.container_json.special_units[su_name]}**"

    def _add_features(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        for ae in active_effects:
            if ae.effect_type == 71:
                planet_effects = PlanetEffects.get_from_effects_list([ae])
                if planet_effects:
                    planet_effect = list(planet_effects)[0]
                    text_display.content += (
                        f"\n> -# {planet_effect[1]} **{planet_effect[0]}**"
                    )
                    if ae.planet_effect["description_long"]:
                        text_display.content += (
                            f"\n> -# {ae.planet_effect['description_long']}"
                        )
                    if ae.planet_effect["description_short"]:
                        text_display.content += (
                            f"\n> -# {ae.planet_effect['description_short']}"
                        )

    def _update_containers(self):
        colour = Colour.dark_theme()
        longest_length = 0
        for container_info in self.container_colours:
            if len(container_info["list"]) - 1 > longest_length:
                longest_length = len(container_info["list"]) - 1
                colour = container_info["colour"]
        super().__init__(*self.non_empty_components, accent_colour=colour)

    def update_containers(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self._update_containers()

        return wrapper

    @property
    def non_empty_components(self):
        results = []
        for list_ in [self.victories, self.new_regions]:
            if len(list_) > 1:
                results.extend(list_)
        return results

    @property
    def components(self) -> list:
        return self.victories + self.new_regions

    @update_containers
    def add_region_victory(self, planet: Planet, region: Planet.Region):
        section = ui.Section(
            ui.TextDisplay(
                self.container_json.container["region_victory"].format(
                    region_name=region.name,
                    planet_name=planet.loc_names[self.container_json.lang_code_long],
                    faction_name=self.container_json.factions[
                        (
                            planet.faction.full_name
                            if not planet.event
                            else planet.event.faction.full_name
                        )
                    ],
                )
            ),
            accessory=ui.Thumbnail(
                VICTORY_ICONS[
                    (
                        planet.faction.full_name.lower()
                        if not planet.event
                        else planet.event.faction.full_name.lower()
                    )
                ]
            ),
        )
        self._add_features(
            text_display=section.children[0], active_effects=planet.active_effects
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self.victories.append(ui.Separator())
        self.victories.append(section)

    @update_containers
    def add_new_region(self, planet: Planet, region: Planet.Region):
        section = ui.Section(
            ui.TextDisplay(
                (
                    self.container_json.container["new_region"].format(
                        region_name=region.name,
                        planet_name=planet.loc_names[
                            self.container_json.lang_code_long
                        ],
                    )
                    + self.container_json.container["resistance"].format(
                        regen=f"{region.regen_perc_per_hour:.2%}"
                    )
                )
            ),
            accessory=ui.Thumbnail(
                ATTACK_EMBED_ICONS[
                    (
                        planet.faction.full_name.lower()
                        if not planet.event
                        else planet.event.faction.full_name.lower()
                    )
                ]
            ),
        )
        if region.description:
            section.children[0].content += f"\n-# {region.description}"
        self._add_features(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )

        self.new_regions.append(ui.Separator())
        self.new_regions.append(section)
