from utils.dataclasses.enums import SpaceStationType, SpaceStationType
from ...functions import arrowhead_format
from ...trackers import BaseTrackerEntry
from ...emojis import Emojis
from .galactic_war import GalacticWarEffect
from .planet import Planet
from datetime import datetime, timezone


class SpaceStation:
    def __init__(
        self, raw_space_station_data: dict, planet: Planet, war_start_timestamp: int
    ) -> None:
        """Organised data for a Space Station"""
        self.name: str = "UNKNOWN SPACE STATION"
        self.id: int = raw_space_station_data.get("id32", 0)
        self.type: SpaceStationType = SpaceStationType(self.id)
        self.planet: Planet = planet
        self.flags: int = raw_space_station_data.get("flags")
        self.move_timer_timestamp: int = raw_space_station_data.get(
            "currentElectionEndWarTime"
        )
        self.move_timer_datetime: datetime = datetime.fromtimestamp(
            war_start_timestamp + self.move_timer_timestamp, tz=timezone.utc
        )
        self.tactical_actions: list[SpaceStation.TacticalAction] = [
            SpaceStation.TacticalAction(
                tactical_action_raw_data=ta_raw_data, war_start_time=war_start_timestamp
            )
            for ta_raw_data in raw_space_station_data.get("tacticalActions")
        ]
        self.active_effects: list[GalacticWarEffect] = []
        self.votes: SpaceStation.Votes | None = None

    def get_ta_by_name(self, name: str):
        if name in [ta.name for ta in self.tactical_actions]:
            return [ta for ta in self.tactical_actions if ta.name == name][0]
        else:
            return None

    def __repr__(self):
        return f"SpaceStation:\n    {self.id = }\n    {self.name = }\n    {self.planet = })"

    class TacticalAction:
        def __init__(self, tactical_action_raw_data: dict, war_start_time: int) -> None:
            """A Tactical Action for a Space Station"""
            self.id: int = tactical_action_raw_data.get("id32", 0)
            self.name: str = tactical_action_raw_data.get(
                "name", "Unnamed Tactical Action"
            )
            self.description: str = tactical_action_raw_data.get("description", "")
            self.status: int = tactical_action_raw_data.get("status", 0)
            self.status_end: int = tactical_action_raw_data.get(
                "statusExpireAtWarTimeSeconds", 0
            )
            self.status_end_datetime: datetime = datetime.fromtimestamp(
                war_start_time + self.status_end, tz=timezone.utc
            )
            self.strategic_description: str = arrowhead_format(
                text=tactical_action_raw_data.get("strategicDescription", "")
            )
            self.cost: list[SpaceStation.TacticalAction.Cost] = [
                DSS.TacticalAction.Cost(cost=cost)
                for cost in tactical_action_raw_data.get("cost", [])
            ]
            self.cost_changes: dict[str, BaseTrackerEntry] = {}
            self.emoji = getattr(
                Emojis.SpaceStations.DSS, self.name.lower().replace(" ", "_"), ""
            )

        class Cost:
            def __init__(self, cost: dict[str,]) -> None:
                """Organised data for the cost of a Tactical Action"""
                self.item: str = {
                    2985106497: "Rare Sample",
                    3992382197: "Common Sample",
                    3608481516: "Requisition Slip",
                }.get(cost.get("itemMixId"), "Unknown")
                self.target: int = cost.get("targetValue")
                self.current: float = cost.get("currentValue")
                if self.target and self.current:
                    self.progress: float = self.current / self.target
                else:
                    self.progress = 1.0
                self.max_per_seconds: tuple[int, int] = (
                    cost.get("maxDonationAmount"),
                    cost.get("maxDonationPeriodSeconds"),
                )

    class Votes:
        def __init__(self, planets: dict[int, Planet], raw_votes_data: dict):
            self.total_votes: int = sum([o["count"] for o in raw_votes_data["options"]])
            self.available_planets: list[tuple[Planet, int]] = []
            for option in raw_votes_data["options"]:
                planet = planets.get(option["metaId"])
                if planet:
                    self.available_planets.append((planet, option["count"]))


class DSS(SpaceStation):
    def __init__(
        self, raw_dss_data: dict, planet: Planet, war_start_timestamp: int
    ) -> None:
        """Organised data for the DSS"""
        super().__init__(
            raw_space_station_data=raw_dss_data,
            planet=planet,
            war_start_timestamp=war_start_timestamp,
        )
        self.name = "Democracy Space Station"
