from datetime import datetime, timedelta
from ...mixins import ReprMixin
from ...trackers import BaseTrackerEntry
from ...dataclasses import Faction, Factions
from ...functions import health_bar


class Assignment(ReprMixin):
    def __init__(self, raw_assignment_data: dict, war_start_timestamp: int) -> None:
        """Organised data of an Assignment or Major Order"""
        self.id: int = raw_assignment_data["id32"]
        self.title: str = raw_assignment_data["setting"]["overrideTitle"]
        self.briefing: str = (
            (
                raw_assignment_data["setting"]["overrideBrief"]
                if raw_assignment_data["setting"]["overrideBrief"] not in ([], None)
                else ""
            )
            .strip("\n")
            .replace("\n", "\n-# ")
        )
        self.description: str = (
            raw_assignment_data["setting"]["taskDescription"]
            if raw_assignment_data["setting"]["taskDescription"]
            not in ([], None, raw_assignment_data["setting"]["overrideBrief"])
            else ""
        )
        self.tasks: list[Assignment.Task] = []
        for index, task in enumerate(iterable=raw_assignment_data["setting"]["tasks"]):
            self.tasks.append(
                Assignment.Task(
                    task=task, current_progress=raw_assignment_data["progress"][index]
                )
            )
        self.rewards: list[dict] = raw_assignment_data["setting"]["rewards"]
        self.starts_at_datetime: datetime = datetime.fromtimestamp(
            raw_assignment_data["startTime"] + war_start_timestamp
        )
        self.ends_at_datetime: datetime = datetime.now() + timedelta(
            seconds=raw_assignment_data["expiresIn"]
        )
        self.flags: int = raw_assignment_data["setting"]["flags"]

    @property
    def unique_task_types(self) -> set[int]:
        return {t.type for t in self.tasks}

    class Task(ReprMixin):
        """Organised data of an Assignment Task"""

        __slots__ = (
            "faction",
            "target",
            "enemy_id",
            "item_id",
            "item_type",
            "objective",
            "min_players",
            "mission_type",
            "difficulty",
            "planet_index",
            "sector_index",
            "type",
            "progress",
            "tracker",
        )

        def __init__(self, task: dict, current_progress: int | float) -> None:
            self.type: int = task["type"]
            self.progress: int | float = current_progress
            self.values_dict = dict(zip(task["valueTypes"], task["values"]))
            self.faction = self.target = self.enemy_id = self.item_id = (
                self.item_type
            ) = self.objective = self.min_players = self.difficulty = (
                self.mission_type
            ) = self.planet_index = self.sector_index = None
            self.tracker: BaseTrackerEntry | None = None

            if faction := self.values_dict.get(1):
                self.faction: Faction | None = Factions.get_from_identifier(
                    number=faction
                )
            if personal := self.values_dict.get(2):
                self.personal: int = personal
            if target := self.values_dict.get(3):
                self.target: int | float = target
            if enemy_id := self.values_dict.get(4):
                self.enemy_id: int = enemy_id
            if item_id := self.values_dict.get(5):
                self.item_id: int = item_id
            if item_type := self.values_dict.get(6):
                self.item_type: int = item_type
            if objective := self.values_dict.get(7):
                self.objective = objective
            if min_players := self.values_dict.get(8):
                self.min_players: int = min_players
            if difficulty := self.values_dict.get(9):
                self.difficulty: int = difficulty
            if mission_type := self.values_dict.get(10):
                self.mission_type: int = mission_type
            if location_type := self.values_dict.get(11):
                if location_type == 1:
                    self.planet_index: int = self.values_dict.get(12)
                elif location_type == 2:
                    self.sector_index: int = self.values_dict.get(12)

        @property
        def progress_perc(self) -> float:
            """Returns the progress of the task as a float (0-1)"""
            return self.progress / self.target

        @property
        def health_bar(self) -> str:
            """Returns a health_bar based on the task type and progress"""
            anim = False
            increasing = False
            if self.tracker != None:
                anim = True
                increasing = self.tracker.change_rate_per_hour > 0

            match self.type:
                case 1 | 2 | 4 | 5 | 10 | 13 | 14:
                    return health_bar(
                        perc=self.progress_perc,
                        faction=Factions.humans,
                        anim=anim,
                        increasing=increasing,
                    )
                case 3 | 6 | 7 | 9 | 12:
                    return health_bar(
                        perc=self.progress_perc,
                        faction=self.faction or "MO",
                        anim=anim,
                        increasing=increasing,
                    )
                case 15:
                    return health_bar(
                        perc=0.5,
                        faction=(Factions.automaton),
                        empty_colour="green",
                    )
                case _:
                    return
