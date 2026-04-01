from utils.dataclasses.enums import CampaignType
from ...mixins import ReprMixin
from ...dataclasses import Faction
from .planet import Planet


class Campaign(ReprMixin):
    __slots__ = ("id", "planet", "type", "count", "progress", "faction")

    def __init__(self, raw_campaign_data: dict, campaign_planet) -> None:
        """Organised data for a campaign"""
        self.id: int = raw_campaign_data["id"]
        self.planet: Planet = campaign_planet
        self._type: int = raw_campaign_data["type"]
        self.type: CampaignType = CampaignType(self._type)
        self.count: int = raw_campaign_data["count"]
        self.progress: float = (
            (1 - (self.planet.health / self.planet.max_health))
            if not self.planet.event
            else self.planet.event.progress
        )
        self.faction: Faction = (
            self.planet.event.faction if self.planet.event else self.planet.faction
        )

    def __eq__(self, value):
        return self.id == value.id

    def __hash__(self):
        return hash(self.id)
