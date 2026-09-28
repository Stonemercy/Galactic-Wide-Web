from disnake import Colour
from disnake.ui import ActionRow, Container, Separator, TextDisplay
from utils.api_wrapper.models import Planet
from utils.dataclasses import Factions, Subfaction
from utils.interactables import SubfactionsStringSelect


class SubfactionsContainer(Container):
    def __init__(self, subfaction: Subfaction, planets: dict[int, Planet]):
        self.components = []

        title_text_display = TextDisplay(
            f"# {subfaction.emoji} [{subfaction.eng_name.title()}](<https://helldivers.wiki.gg/wiki/Special:Search?search={subfaction.eng_name.title().replace(' ', '_')}>)"
        )
        self.components.extend([title_text_display, Separator()])

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
            planets_text = ""
            for planet in planets_with_sf:
                planets_text += (
                    f"\n- {planet.faction.emoji} [**{planet.name}**](<https://helldivers.wiki.gg/wiki/Special:Search?search={planet.name.replace(' ', '_')}>)"
                    f"\n-# {planet.stats.player_count:,} Heroes\n"
                )
            self.components.append(TextDisplay(planets_text))
            colour = subfaction.faction.colour
        else:
            self.components.append(TextDisplay(f"- None"))
            colour = Factions.humans.colour

        self.components.append(ActionRow(SubfactionsStringSelect(planets=planets)))

        super().__init__(
            *self.components,
            accent_colour=Colour.from_rgb(*colour),
        )
