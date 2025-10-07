from data.lists import (
    ATTACK_EMBED_ICONS,
    DEFENCE_EMBED_ICONS,
    VICTORY_ICONS,
    LOSS_ICONS,
    CUSTOM_COLOURS,
)
from disnake import Colour, ui
from utils.dataclasses import CampaignChangesJson, PlanetFeatures, SpecialUnits
from utils.data import Campaign, GalacticWarEffect, Planet
from utils.emojis import Emojis
from utils.interactables import HDCButton
from utils.mixins import ReprMixin


class CampaignChangesContainer(ui.Container, ReprMixin):
    def __init__(self, json: CampaignChangesJson):
        self.json = json
        self.colour = Colour.dark_theme()
        self.title = [
            ui.TextDisplay(
                f"# {Emojis.Decoration.left_banner} {self.json.container['title']} {Emojis.Decoration.right_banner}"
            )
        ]
        self.victories = [
            ui.TextDisplay(
                f"## {self.json.container['victories']} {Emojis.Icons.victory}"
            )
        ]
        self.losses = [
            ui.TextDisplay(
                f"## {self.json.container['losses']} {Emojis.Decoration.alert_icon}"
            ),
        ]
        self.new_campaigns = [
            ui.TextDisplay(
                f"## {self.json.container['new_campaigns']} {Emojis.Icons.new_icon}"
            )
        ]
        self.planet_buttons: list[ui.Button] | list = []
        self.container_colours = [
            {"list": self.victories, "colour": Colour.brand_green()},
            {"list": self.losses, "colour": Colour.brand_red()},
            {
                "list": self.new_campaigns,
                "colour": Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
            },
        ]

    def _add_special_units(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        for su_name, su_emoji in SpecialUnits.get_from_effects_list(
            active_effects=active_effects
        ):
            text_display.content += (
                f"\n> -# {su_emoji} **{self.json.special_units[su_name]}**"
            )

    def _add_regions(self, text_display: ui.TextDisplay, regions: list[Planet.Region]):
        for region in regions:
            text_display.content += (
                f"\n> -# {region.emoji} {region.type} **{region.name}**"
            )

    def _add_features(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        for feature_name, feature_emoji in PlanetFeatures.get_from_effects_list(
            (ae for ae in active_effects if ae.effect_type == 71)
        ):
            text_display.content += f"\n> -# {feature_emoji} **{feature_name}**"

    def _add_gambit(
        self,
        text_display: ui.TextDisplay,
        gambit_planet=Planet,
    ):
        if gambit_planet.regen_perc_per_hour < 0.03:
            text_display.content += f"\n> -# :chess_pawn: {self.json.container['gambit']}: **{gambit_planet.loc_names[self.json.lang_code_long]}**"

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
    def non_empty_components(self):
        results = []
        for list_ in [self.victories, self.losses, self.new_campaigns]:
            if len(list_) > 1:
                results.extend(list_)
        return results

    @property
    def components(self) -> list:
        return self.victories + self.losses + self.new_campaigns

    @update_containers
    def add_liberation_victory(self, planet: Planet, taken_from: str):
        section = ui.Section(
            ui.TextDisplay(
                self.json.container["liberated"].format(
                    planet_name=planet.loc_names[self.json.lang_code_long],
                    faction_name=self.json.factions[taken_from],
                )
            ),
            accessory=ui.Thumbnail(VICTORY_ICONS[taken_from.lower()]),
        )
        self._add_features(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self.victories.append(ui.Separator())
        self.victories.append(section)

        if planet.loc_names[self.json.lang_code_long] not in [
            b.label for b in self.planet_buttons
        ]:
            self.planet_buttons.append(
                HDCButton(
                    label=planet.loc_names[self.json.lang_code_long],
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{planet.index}",
                )
            )

    @update_containers
    def add_defence_victory(
        self, planet: Planet, defended_against: str, hours_remaining: int
    ):
        section = ui.Section(
            ui.TextDisplay(
                self.json.container["defended"].format(
                    planet_name=planet.loc_names[self.json.lang_code_long],
                    faction_name=self.json.factions[defended_against],
                )
            ),
            accessory=ui.Thumbnail(VICTORY_ICONS[defended_against.lower()]),
        )
        if hours_remaining != 0:
            section.children[0].content += self.json.container[
                "ahead_of_schedule"
            ].format(
                hours_remaining=f"{hours_remaining:.0f}",
            )
        self._add_features(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self.victories.append(ui.Separator())
        self.victories.append(section)

        if planet.loc_names[self.json.lang_code_long] not in [
            b.label for b in self.planet_buttons
        ]:
            self.planet_buttons.append(
                HDCButton(
                    label=planet.loc_names[self.json.lang_code_long],
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{planet.index}",
                )
            )

    @update_containers
    def add_new_campaign(self, campaign: Campaign, gambit_planets: dict[int, Planet]):
        if campaign.planet.event:
            section = ui.Section(
                ui.TextDisplay(
                    (
                        self.json.container["defend"].format(
                            planet_name=campaign.planet.loc_names[
                                self.json.lang_code_long
                            ],
                            emojis=campaign.planet.exclamations,
                        )
                        + self.json.container["invasion_level"].format(
                            level=campaign.planet.event.level,
                            emoji=campaign.planet.event.level_exclamation,
                        )
                        + self.json.container["ends"].format(
                            timestamp=int(
                                campaign.planet.event.end_time_datetime.timestamp()
                            )
                        )
                    )
                ),
                accessory=ui.Thumbnail(
                    DEFENCE_EMBED_ICONS[campaign.faction.full_name.lower()]
                ),
            )

            self._add_special_units(
                text_display=section.children[0],
                active_effects=campaign.planet.active_effects,
            )

            self._add_regions(
                text_display=section.children[0],
                regions=campaign.planet.regions.values(),
            )

            if campaign.planet.index in gambit_planets:
                self._add_gambit(
                    text_display=section.children[0],
                    gambit_planet=gambit_planets[campaign.planet.index],
                )

            # last step
            self.new_campaigns.append(ui.Separator())
            self.new_campaigns.append(section)

            if campaign.planet.loc_names[self.json.lang_code_long] not in [
                b.label for b in self.planet_buttons
            ]:
                self.planet_buttons.append(
                    HDCButton(
                        label=campaign.planet.loc_names[self.json.lang_code_long],
                        link=f"https://helldiverscompanion.com/#hellpad/planets/{campaign.planet.index}",
                    )
                )
        else:
            section = ui.Section(
                ui.TextDisplay(
                    (
                        self.json.container["liberate"].format(
                            planet_name=campaign.planet.loc_names[
                                self.json.lang_code_long
                            ],
                            emojis=campaign.faction.emoji
                            + campaign.planet.exclamations,
                        )
                        + self.json.container["resistance"].format(
                            regen=f"{campaign.planet.regen_perc_per_hour:+.2%}"
                        )
                    )
                ),
                accessory=ui.Thumbnail(
                    ATTACK_EMBED_ICONS[campaign.faction.full_name.lower()]
                ),
            )
            self._add_features(
                text_display=section.children[0],
                active_effects=campaign.planet.active_effects,
            )
            self._add_special_units(
                text_display=section.children[0],
                active_effects=campaign.planet.active_effects,
            )
            self._add_regions(
                text_display=section.children[0],
                regions=campaign.planet.regions.values(),
            )

            # last step
            self.new_campaigns.append(ui.Separator())
            self.new_campaigns.append(section)

            if campaign.planet.loc_names[self.json.lang_code_long] not in [
                b.label for b in self.planet_buttons
            ]:
                self.planet_buttons.append(
                    HDCButton(
                        label=campaign.planet.loc_names[self.json.lang_code_long],
                        link=f"https://helldiverscompanion.com/#hellpad/planets/{campaign.planet.index}",
                    )
                )

    @update_containers
    def add_planet_lost(self, planet: Planet):
        section = ui.Section(
            ui.TextDisplay(
                self.json.container["planet_lost"].format(
                    planet_name=planet.loc_names[self.json.lang_code_long],
                    emojis=planet.exclamations,
                    faction_name=planet.faction.full_name,
                )
            ),
            accessory=ui.Thumbnail(LOSS_ICONS[planet.faction.full_name.lower()]),
        )
        self._add_features(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=planet.active_effects,
        )
        self.losses.append(ui.Separator())
        self.losses.append(section)

        if planet.loc_names[self.json.lang_code_long] not in [
            b.label for b in self.planet_buttons
        ]:
            self.planet_buttons.append(
                HDCButton(
                    label=planet.loc_names[self.json.lang_code_long],
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{planet.index}",
                )
            )
