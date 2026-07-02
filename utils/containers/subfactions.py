from disnake import Colour
from disnake.ui import ActionRow, Container, Section, Separator, TextDisplay
from utils.api_wrapper.models import Planet
from utils.dataclasses import Factions, Subfaction
from utils.interactables import HDCButton, SubfactionsStringSelect, WikiButton


class SubfactionsContainer(Container):
    def __init__(self, subfaction: Subfaction, planets: dict[int, Planet]):
        self.components = []

        title_section = Section(
            TextDisplay(f"# {subfaction.emoji} {subfaction.eng_name.title()}"),
            accessory=WikiButton(
                link=f"https://helldivers.wiki.gg/wiki/{subfaction.eng_name.title().replace(' ', '_')}",
            ),
        )
        self.components.extend([title_section, Separator()])

        self.components.append(TextDisplay(f"Planets with this subfaction active:"))
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
                        Section(
                            TextDisplay(
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
                        Separator(),
                    ]
                )
            colour = max(
                [p.faction for p in planets_with_sf],
                key=[p.faction for p in planets_with_sf].count,
            ).colour
        else:
            self.components.append(TextDisplay(f"- None"))
            colour = Factions.humans.colour

        self.components.append(ActionRow(SubfactionsStringSelect(planets=planets)))

        super().__init__(
            *self.components,
            accent_colour=Colour.from_rgb(*colour),
        )
