from data.lists import ATTACK_EMBED_ICONS, VICTORY_ICONS, CUSTOM_COLOURS
from disnake import Colour, ui
from utils.api_wrapper.models import GalacticWarEffect, Planet
from utils.dataclasses import PlanetFeatures, RegionChangesJson, SpecialUnits
from utils.emojis import Emojis
from utils.interactables import HDCButton
from utils.mixins import ReprMixin


class RegionChangesContainer(ui.Container, ReprMixin):
    def __init__(self, container_json: RegionChangesJson):
        self.container_json = container_json
        self.colour = Colour.dark_theme()
        self.title = [
            ui.TextDisplay(
                f"# {Emojis.Decoration.left_banner} {self.container_json.container['title']} {Emojis.Decoration.right_banner}",
            )
        ]
        self.victories = [
            ui.TextDisplay(
                f"## {self.container_json.container['victories']} {Emojis.Icons.victory}"
            )
        ]
        self.new_regions = [
            ui.TextDisplay(
                f"## {self.container_json.container['new_regions']} {Emojis.Icons.new_icon}"
            )
        ]
        self.planet_buttons: list[ui.Button] = []
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
                text_display.content += (
                    f"\n-# {su_emoji} **{self.container_json.special_units[su_name]}**"
                )

    def _add_features(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        for planet_feature in PlanetFeatures.get_from_effects_list(
            (ae for ae in active_effects if ae.effect_type == 71)
        ):
            text_display.content += f"\n-# {planet_feature[1]} {planet_feature[0]}"

    def _update_containers(self):
        colour = Colour.dark_theme()
        longest_length = 0
        for container_info in self.container_colours:
            if len(container_info["list"]) - 1 > longest_length:
                longest_length = len(container_info["list"]) - 1
                colour = container_info["colour"]
        planet_button_chunks = [
            self.planet_buttons[i : i + 3]
            for i in range(0, len(self.planet_buttons), 3)
        ]
        super().__init__(
            *(
                self.title
                + self.non_empty_components
                + (
                    [ui.ActionRow(*chunk) for chunk in planet_button_chunks]
                    if self.planet_buttons
                    else []
                )
            ),
            accent_colour=colour,
        )

    def update_containers(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self._update_containers()

        return wrapper

    @property
    def non_empty_components(self) -> list:
        results = []
        for list_ in [self.victories, self.new_regions]:
            if len(list_) > 1:
                results.extend(list_)
        return results

    @property
    def components(self) -> list:
        return self.victories + self.new_regions

    @update_containers
    def add_region_victory(self, region: Planet.Region):
        section = ui.Section(
            ui.TextDisplay(
                self.container_json.container["region_victory"].format(
                    region_emoji=region.emoji,
                    region_name=region.names[self.container_json.lang_code_long],
                    planet_name=region.planet.loc_names[
                        self.container_json.lang_code_long
                    ],
                    faction_name=self.container_json.factions[
                        (
                            region.planet.faction.full_name
                            if not region.planet.event
                            else region.planet.event.faction.full_name
                        )
                    ],
                )
            ),
            accessory=ui.Thumbnail(
                VICTORY_ICONS[
                    (
                        region.planet.faction.full_name.lower()
                        if not region.planet.event
                        else region.planet.event.faction.full_name.lower()
                    )
                ]
            ),
        )
        self._add_features(
            text_display=section.children[0],
            active_effects=region.planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=region.planet.active_effects,
        )
        self.victories.append(ui.Separator())
        self.victories.append(section)

        if region.planet.loc_names[self.container_json.lang_code_long] not in [
            b.label for b in self.planet_buttons
        ]:
            self.planet_buttons.append(
                HDCButton(
                    label=region.planet.loc_names[self.container_json.lang_code_long],
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{region.planet.index}",
                )
            )

    @update_containers
    def add_new_region(self, region: Planet.Region):
        section = ui.Section(
            ui.TextDisplay(
                (
                    self.container_json.container["new_region"].format(
                        region_emoji=region.emoji,
                        region_name=region.names[self.container_json.lang_code_long],
                        planet_name=region.planet.loc_names[
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
                        region.planet.faction.full_name.lower()
                        if not region.planet.event
                        else region.planet.event.faction.full_name.lower()
                    )
                ]
            ),
        )
        if region.description:
            section.children[
                0
            ].content += (
                f"\n-# {region.descriptions[self.container_json.lang_code_long]}"
            )
        self._add_features(
            text_display=section.children[0],
            active_effects=region.planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=region.planet.active_effects,
        )

        self.new_regions.append(ui.Separator())
        self.new_regions.append(section)

        if region.planet.loc_names[self.container_json.lang_code_long] not in [
            b.label for b in self.planet_buttons
        ]:
            self.planet_buttons.append(
                HDCButton(
                    label=region.planet.loc_names[self.container_json.lang_code_long],
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{region.planet.index}",
                )
            )
