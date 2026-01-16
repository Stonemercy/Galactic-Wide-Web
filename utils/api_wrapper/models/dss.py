from ...mixins import ReprMixin
from ...functions import dispatch_format
from ...trackers import BaseTrackerEntry
from ...emojis import Emojis
from .planet import Planet
from datetime import datetime


class DSS(ReprMixin):
    def __init__(self, raw_dss_data: dict, planet, war_start_timestamp: int) -> None:
        """Organised data for the DSS"""
        self.planet: Planet = planet
        self.flags: int = raw_dss_data["flags"]
        self.move_timer_timestamp: int = raw_dss_data["currentElectionEndWarTime"]
        self.move_timer_datetime: datetime = datetime.fromtimestamp(
            war_start_timestamp + self.move_timer_timestamp
        )
        self.tactical_actions: list[DSS.TacticalAction] = [
            DSS.TacticalAction(
                tactical_action_raw_data=tactical_action_raw_data,
                war_start_time=war_start_timestamp,
            )
            for tactical_action_raw_data in raw_dss_data["tacticalActions"]
        ]
        self.votes: None | DSS.Votes = None

    def get_ta_by_name(self, name: str):
        if name in [ta.name for ta in self.tactical_actions]:
            return [ta for ta in self.tactical_actions if ta.name == name][0]
        else:
            return None

    class TacticalAction(ReprMixin):
        def __init__(self, tactical_action_raw_data: dict, war_start_time: int) -> None:
            """A Tactical Action for the DSS"""
            self.id: int = tactical_action_raw_data["id32"]
            self.name: str = tactical_action_raw_data["name"]
            self.description: str = tactical_action_raw_data["description"]
            self.status: int = tactical_action_raw_data["status"]
            self.status_end: int = tactical_action_raw_data[
                "statusExpireAtWarTimeSeconds"
            ]
            self.status_end_datetime: datetime = datetime.fromtimestamp(
                war_start_time + self.status_end
            )
            self.strategic_description: str = dispatch_format(
                text=tactical_action_raw_data["strategicDescription"]
            )
            self.cost: list[DSS.TacticalAction.Cost] = [
                DSS.TacticalAction.Cost(cost=cost)
                for cost in tactical_action_raw_data["cost"]
            ]
            self.cost_changes: dict[str, BaseTrackerEntry] = {}
            self.emoji = getattr(Emojis.DSS, self.name.lower().replace(" ", "_"), "")

        class Cost(ReprMixin):
            def __init__(self, cost) -> None:
                """Organised data for the cost of a Tactical Action"""
                self.item: str = {
                    2985106497: "Rare Sample",
                    3992382197: "Common Sample",
                    3608481516: "Requisition Slip",
                }.get(cost["itemMixId"], "Unknown")
                self.target: int = cost["targetValue"]
                self.current: float = cost["currentValue"]
                self.progress: float = self.current / self.target
                self.max_per_seconds: tuple = (
                    cost["maxDonationAmount"],
                    cost["maxDonationPeriodSeconds"],
                )

    class Votes(ReprMixin):
        def __init__(self, planets: dict[int, Planet], raw_votes_data: dict):
            self.total_votes: int = sum([o["count"] for o in raw_votes_data["options"]])
            self.available_planets: list[tuple[Planet, int]] = []
            for option in raw_votes_data["options"]:
                planet = planets.get(option["metaId"])
                if planet:
                    self.available_planets.append((planet, option["count"]))
