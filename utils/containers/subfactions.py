from disnake import Colour, ui
from utils.api_wrapper.models.planet import Planet
from utils.dataclasses.factions import Factions
from utils.dataclasses.subfactions import Subfaction
from utils.interactables import HDCButton
from utils.interactables.subfactions_string_select import SubfactionsStringSelect
from utils.interactables.wiki_button import WikiButton


class SubfactionsContainer(ui.Container):
    def __init__(self, subfaction: Subfaction, planets: dict[int, Planet]):
        self.components = []

        title_section = ui.Section(
            ui.TextDisplay(f"# {subfaction.emoji} {subfaction.eng_name.title()}"),
            accessory=WikiButton(
                link=f"https://helldivers.wiki.gg/wiki/{subfaction.eng_name.title().replace(' ', '_')}",
            ),
        )
        self.components.extend([title_section, ui.Separator()])

        self.components.append(ui.TextDisplay(f"Planets with this subfaction active:"))
        if planets_with_sf := sorted(
            [
                p
                for p in planets.values()
                if subfaction in p.subfactions
                and (p.faction != Factions.humans or p.active_campaign)
            ],
            key=lambda x: x.stats.player_count,
            reverse=True,
        ):
            for planet in planets_with_sf:
                self.components.extend(
                    [
                        ui.Section(
                            ui.TextDisplay(
                                (
                                    f"\n- {planet.faction.emoji} {planet.name}"
                                    f"\n-# {planet.stats.player_count:,} Heroes"
                                )
                            ),
                            accessory=HDCButton(
                                label="HDC",
                                link=f"https://helldiverscompanion.com/#hellpad/planets/{planet.index}",
                            ),
                        ),
                        ui.Separator(),
                    ]
                )
            colour = max(
                [p.faction for p in planets_with_sf],
                key=[p.faction for p in planets_with_sf].count,
            ).colour
        else:
            self.components.append(ui.TextDisplay(f"- None"))
            colour = Factions.humans.colour

        self.components.append(ui.ActionRow(SubfactionsStringSelect(planets=planets)))

        super().__init__(
            *self.components,
            accent_colour=Colour.from_rgb(*colour),
        )
