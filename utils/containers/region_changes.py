from data.lists import ATTACK_EMBED_ICONS, VICTORY_ICONS, CUSTOM_COLOURS
from disnake import Colour
from disnake.ui import (
    ActionRow,
    Button,
    Container,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)
from utils.api_wrapper.models import Planet
from utils.dataclasses import PlanetFeature, RegionChangesJson, Subfaction
from utils.emojis import Emojis
from utils.interactables import HDCButton
from utils.mixins import ReprMixin


class RegionChangesContainer(Container, ReprMixin):
    def __init__(self, container_json: RegionChangesJson):
        self.container_json = container_json
        self.colour = Colour.dark_theme()
        self.title = [
            TextDisplay(
                f"# {Emojis.Decoration.left_banner} {self.container_json.container['title']} {Emojis.Decoration.right_banner}",
            )
        ]
        self.victories = [
            TextDisplay(
                f"## {self.container_json.container['victories']} {Emojis.Icons.victory}"
            )
        ]
        self.new_regions = [
            TextDisplay(
                f"## {self.container_json.container['new_regions']} {Emojis.Icons.new_icon}"
            )
        ]
        self.planet_buttons: list[Button] = []
        self.container_colours = [
            {"list": self.victories, "colour": Colour.brand_green()},
            {
                "list": self.new_regions,
                "colour": Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
            },
        ]

    def _add_subfactions(self, text_display: TextDisplay, subfactions: set[Subfaction]):
        for sf in subfactions:
            text_display.content += (
                f"\n-# {sf.emoji} **{self.container_json.subfactions[sf.eng_name]}**"
            )

    def _add_features(
        self, text_display: TextDisplay, planet_features: list[PlanetFeature]
    ):
        for feature in planet_features:
            text_display.content += f"\n-# {feature.emoji} {feature.name}"

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
                    [ActionRow(*chunk) for chunk in planet_button_chunks]
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
        section = Section(
            TextDisplay(
                self.container_json.container["region_victory"].format(
                    region_emoji=region.emoji,
                    region_name=region.names.get(
                        self.container_json.lang_code_long, region.name
                    ),
                    planet_name=region.planet.names.get(
                        self.container_json.lang_code_long, region.planet.name
                    ),
                    faction_name=self.container_json.factions[
                        (
                            f"{region.planet.faction.full_name}_plural"
                            if not region.planet.event
                            else f"{region.planet.event.faction.full_name}_plural"
                        )
                    ],
                )
            ),
            accessory=Thumbnail(
                VICTORY_ICONS.get(
                    (
                        region.planet.faction.full_name.lower()
                        if not region.planet.event
                        else region.planet.event.faction.full_name.lower()
                    ),
                    VICTORY_ICONS["default"],
                )
            ),
        )
        self._add_features(
            text_display=section.children[0],
            planet_features=region.planet.planet_features,
        )
        self._add_subfactions(
            text_display=section.children[0],
            subfactions=region.planet.subfactions,
        )
        self.victories.append(Separator())
        self.victories.append(section)

        if region.planet.names.get(
            self.container_json.lang_code_long, region.planet.name
        ) not in [b.label for b in self.planet_buttons]:
            self.planet_buttons.append(
                HDCButton(
                    label=region.planet.names.get(
                        self.container_json.lang_code_long, region.planet.name
                    ),
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{region.planet.index}",
                )
            )

    @update_containers
    def add_new_region(self, region: Planet.Region):
        section = Section(
            TextDisplay(
                (
                    self.container_json.container["new_region"].format(
                        region_emoji=region.emoji,
                        region_name=region.names.get(
                            self.container_json.lang_code_long, region.name
                        ),
                        planet_name=region.planet.names.get(
                            self.container_json.lang_code_long, region.planet.name
                        ),
                    )
                    + self.container_json.container["resistance"].format(
                        regen=f"{region.regen_perc_per_hour:.2%}"
                    )
                )
            ),
            accessory=Thumbnail(
                ATTACK_EMBED_ICONS.get(
                    (
                        region.planet.faction.full_name.lower()
                        if not region.planet.event
                        else region.planet.event.faction.full_name.lower()
                    ),
                    ATTACK_EMBED_ICONS["default"],
                )
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
            planet_features=region.planet.planet_features,
        )
        self._add_subfactions(
            text_display=section.children[0],
            subfactions=region.planet.subfactions,
        )

        self.new_regions.append(Separator())
        self.new_regions.append(section)

        if region.planet.names.get(
            self.container_json.lang_code_long, region.planet.name
        ) not in [b.label for b in self.planet_buttons]:
            self.planet_buttons.append(
                HDCButton(
                    label=region.planet.names.get(
                        self.container_json.lang_code_long, region.planet.name
                    ),
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{region.planet.index}",
                )
            )
