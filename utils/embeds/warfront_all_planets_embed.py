from disnake import Colour, Embed
from utils.data import Planets
from utils.dataclasses import Factions
from utils.mixins import EmbedReprMixin


class WarfrontAllPlanetsEmbed(Embed, EmbedReprMixin):
    def __init__(self, planets: Planets, faction: str):
        planets_list = sorted(
            [p for p in planets.values() if p.current_owner.full_name == faction],
            key=lambda planet: planet.stats["playerCount"],
            reverse=True,
        )
        super().__init__(
            title=f"All planets for {faction}",
            colour=Colour.from_rgb(*Factions.get_from_identifier(name=faction).colour),
            description=f"There are **{len(planets_list)}** planets under {faction} control",
        )
        name = "Planets list"
        value = " - ".join([f"**{p.name}**" for p in planets_list])
        self.add_field(name=name, value=value)
