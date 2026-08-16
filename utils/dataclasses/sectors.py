from random import choice
from utils.api_wrapper.models import Planet
from utils.dataclasses import Faction, Factions

DIM_FACTION_COLOURS: dict[str, tuple[int, int, int]] = {
    faction.full_name: tuple(int(colour / 2.5) for colour in faction.colour)
    for faction in Factions.all
}


class Sector:
    def __init__(self, starting_planet: Planet):
        self.name = starting_planet.sector
        self.planets: list[Planet] = [starting_planet]

    @property
    def faction(self) -> Faction:
        planet_factions = [
            p.faction if p.event is None else p.event.faction for p in self.planets
        ]
        if len(set(planet_factions)) == 1:
            return planet_factions[0]
        return max(
            [pf for pf in planet_factions if pf != Factions.humans],
            key=planet_factions.count,
        )

    @property
    def coordinates(self) -> tuple[int, int]:
        return choice(self.planets).map_waypoints

    @property
    def gloomed(self) -> bool:
        return len([p for p in self.planets if p.in_gloom]) > 0

    @property
    def voided(self) -> bool:
        return len([p for p in self.planets if 1376 in p.active_effects]) > 0

    @property
    def map_colour(self) -> tuple[int, int, int]:
        if self.faction == Factions.humans:
            return None
        if any(p.active_campaign for p in self.planets) and not self.voided:
            return DIM_FACTION_COLOURS[self.faction.full_name]
        else:
            return tuple(
                int(i / 2) for i in DIM_FACTION_COLOURS[self.faction.full_name]
            )

    def __str__(self):
        return (
            "Sector("
            f"\n    name={self.name}"
            f"\n    planets={[(p.index, p.name, p.faction.full_name if p.event is None else p.event.faction.full_name) for p in self.planets]})"
            f"\n    faction={self.faction.full_name}"
            f"\n    voided={self.voided}"
            f"\n    gloomed={self.gloomed}"
        )


class Sectors:
    def __init__(self):
        self.all_sectors: list[Sector] = []

    def get_sector(self, sector_name: str) -> Sector | None:
        return next((s for s in self.all_sectors if s.name == sector_name), None)

    def add_sector(self, sector_planet: Planet) -> Sector | None:
        self.all_sectors.append(Sector(sector_planet))

    def __iter__(self):
        return (s.name for s in self.all_sectors)
