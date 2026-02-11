from disnake import Colour, Embed
from utils.api_wrapper.models import Planet
from utils.dataclasses import Factions
from utils.mixins import EmbedReprMixin


class WarfrontAllPlanetsEmbed(Embed, EmbedReprMixin):
    def __init__(self, planets: dict[int, Planet], faction: str):
        planets_list = sorted(
            [p for p in planets.values() if p.faction.full_name == faction],
            key=lambda planet: planet.stats.player_count,
            reverse=True,
        )
        super().__init__(
            title=f"All planets for {faction}",
            colour=Colour.from_rgb(*Factions.get_from_identifier(name=faction).colour),
            description=f"There are **{len(planets_list)}** planets under {faction} control",
        )
        name = "Planets list"
        value = " - ".join(
            [f"**{p.names.get('en-GB', str(p.index))}**" for p in planets_list]
        )
        self.add_field(name=name, value=value)
