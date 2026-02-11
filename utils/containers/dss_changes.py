from data.lists import CUSTOM_COLOURS
from disnake import Colour, ui
from utils.dataclasses import DSSChangesJson, DSSImages, SpecialUnits, PlanetFeatures
from utils.api_wrapper.models import DSS, GalacticWarEffect, Planet
from utils.emojis import Emojis
from utils.functions import short_format
from utils.interactables import HDCButton
from utils.mixins import ReprMixin


STATUSES = {0: "inactive", 1: "preparing", 2: "active", 3: "on_cooldown"}

AMOUNT_PER_COST = {
    "Requisition Slip": 50_000,
    "Common Sample": 75,
    "Rare Sample": 50,
}


class DSSChangesContainer(ui.Container, ReprMixin):
    def __init__(self, json: DSSChangesJson):
        self.json = json
        self.colour = Colour.from_rgb(*CUSTOM_COLOURS["DSS"])
        self.title = [
            ui.Section(
                ui.TextDisplay(f"# {self.json.container['title']} {Emojis.DSS.icon}"),
                accessory=HDCButton(
                    label="HDC/space_stations",
                    link="https://helldiverscompanion.com/#hellpad/stations",
                ),
            )
        ]
        self.sections = []

    def _add_special_units(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        if special_units := SpecialUnits.get_from_effects_list(
            active_effects=active_effects
        ):
            for su_name, su_emoji in special_units:
                text_display.content += (
                    f"\n-# {su_emoji} **{self.json.special_units[su_name]}**"
                )

    def _add_regions(self, text_display: ui.TextDisplay, regions: list[Planet.Region]):
        for region in sorted(regions, key=lambda x: x.availability_factor):
            text_display.content += f"\n-# {region.emoji} {self.json.regions[str(region.type.value)]} **{region.names[self.json.lang_code_long]}**"

    def _add_features(
        self, text_display: ui.TextDisplay, active_effects: set[GalacticWarEffect]
    ):
        for planet_feature in PlanetFeatures.get_from_effects_list(
            (ae for ae in active_effects if ae.effect_type == 71)
        ):
            text_display.content += f"\n-# {planet_feature[1]} {planet_feature[0]}"

    def _add_gambit(
        self,
        text_display: ui.TextDisplay,
        gambit_planet: Planet,
    ):
        if gambit_planet.regen_perc_per_hour < 0.03:
            text_display.content += f"\n-# {self.json.container['gambit']}: {gambit_planet.names.get(self.json.lang_code_long, str(gambit_planet.index))}"

    def _update_containers(self):
        super().__init__(*(self.title + self.sections), accent_colour=self.colour)

    def update_containers(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self._update_containers()

        return wrapper

    @update_containers
    def dss_moved(self, before_planet: Planet, after_planet: Planet):
        section = ui.Section(
            ui.TextDisplay(
                self.json.container["has_moved"].format(
                    planet_name1=before_planet.names.get(
                        self.json.lang_code_long, str(before_planet.index)
                    ),
                    planet_name2=after_planet.names.get(
                        self.json.lang_code_long, str(after_planet.index)
                    ),
                    emojis=after_planet.exclamations,
                )
            ),
            accessory=ui.Thumbnail(
                "https://media.discordapp.net/attachments/1212735927223590974/1417530135292280854/DSS_moved.png?ex=68cad150&is=68c97fd0&hm=893a42a4a8f7c594bf708abd7d0edd98eb9f33be4f26543207d6171fd0e1f27b&=&format=webp&quality=lossless"
            ),
        )
        self._add_features(
            text_display=section.children[0],
            active_effects=after_planet.active_effects,
        )
        self._add_special_units(
            text_display=section.children[0],
            active_effects=after_planet.active_effects,
        )
        self._add_regions(
            text_display=section.children[0],
            regions=after_planet.regions.values(),
        )

        self.sections.append(ui.Separator())
        self.sections.append(section)

    @update_containers
    def ta_status_changed(self, tactical_action: DSS.TacticalAction):
        section = ui.Section(
            ui.TextDisplay(
                self.json.container["ta_status_change"].format(
                    ta_name=self.json.container["tactical_actions"]
                    .get(tactical_action.name, {})
                    .get("name", tactical_action.name),
                    status=self.json.container[STATUSES[tactical_action.status]],
                )
            ),
            accessory=ui.Thumbnail(
                DSSImages.get(
                    ta_name=tactical_action.name,
                    status=STATUSES.get(tactical_action.status),
                )
                if tactical_action.name.count("_") == 0
                else "https://cdn.discordapp.com/attachments/1212735927223590974/1422512588973015081/0xa92d559bf3ae174.png?ex=68dcf196&is=68dba016&hm=6d361df60c5c8b49467f549fa599f018039887cb355f329f1575ba701bcd7d60&"
            ),
        )
        if tactical_action.status == 1:
            for cost in tactical_action.cost:
                section.children[
                    0
                ].content += f"\n-# Requires **{short_format(cost.target * AMOUNT_PER_COST[cost.item])}** {cost.item} to activate"
        elif tactical_action.status == 2:
            section.children[0].content += (
                f"\n{self.json.container['tactical_actions'].get(tactical_action.name, {}).get('description', tactical_action.description)}"
                + f"\n{self.json.container['expires']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            )
        elif tactical_action.status == 3:
            section.children[
                0
            ].content += f"\n-# {self.json.container['prep_starts']} **<t:{int(tactical_action.status_end_datetime.timestamp())}:R>**"
        self.sections.append(ui.Separator())
        self.sections.append(section)
