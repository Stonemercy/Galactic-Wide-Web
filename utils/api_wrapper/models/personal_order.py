from datetime import datetime, timedelta
from ...mixins import ReprMixin
from ...dataclasses import Faction, Factions


class PersonalOrder(ReprMixin):
    __slots__ = (
        "id",
        "expiration_datetime",
        "title",
        "brief",
        "description",
        "tasks",
        "rewards",
        "flags",
    )

    def __init__(self, personal_order: dict, json_dict: dict):
        self.id: int = personal_order["id32"]
        self.expiration_secs_from_now: int = personal_order["expiresIn"]
        self.expiration_datetime: datetime = datetime.now() + timedelta(
            seconds=self.expiration_secs_from_now,
        )
        self.title: str = personal_order["setting"]["overrideTitle"]
        self.brief: str = personal_order["setting"]["overrideBrief"]
        self.description: str = personal_order["setting"]["taskDescription"]
        self.tasks: list[PersonalOrder.Task] = [
            self.Task(task, json_dict) for task in personal_order["setting"]["tasks"]
        ]
        self.rewards: list[PersonalOrder.Reward] = [
            self.Reward(reward) for reward in personal_order["setting"]["rewards"]
        ]
        self.flags: int = personal_order["setting"]["flags"]

    class Task(ReprMixin):
        __slots__ = (
            "type",
            "values_dict",
            "faction",
            "target",
            "enemy_id",
            "item_id",
            "objective",
            "difficulty",
            "planet_index",
            "sector_index",
            "found_enemy",
            "found_stratagem",
            "found_booster",
        )

        def __init__(self, task: dict, json_dict: dict):
            self.type: int = task["type"]
            self.values: dict = task["values"]
            self.value_types: dict = task["valueTypes"]
            self.values_dict = dict(zip(task["valueTypes"], task["values"]))
            self.faction = self.target = self.enemy_id = self.item_id = (
                self.objective
            ) = self.value8 = self.difficulty = self.value10 = self.planet_index = (
                self.sector_index
            ) = self.found_enemy = self.found_stratagem = self.found_booster = None
            if faction := self.values_dict.get(1):
                self.faction: Faction | None = Factions.get_from_identifier(
                    number=faction
                )
            if personal := self.values_dict.get(2):
                self.personal = personal
            if target := self.values_dict.get(3):
                self.target: int | float = target
            if enemy_id := self.values_dict.get(4):
                self.enemy_id: int = enemy_id
                self.found_enemy = json_dict["enemy_ids"].get(str(self.enemy_id), None)
            if self.values_dict.get(6):
                self.mix_id = self.values_dict.get(5)
                for wing_stratagems in json_dict["stratagems"].values():
                    for wing_strat_name, wing_strat_stats in wing_stratagems.items():
                        if wing_strat_stats["id"] == self.mix_id:
                            self.found_stratagem: tuple[str, dict] = (
                                wing_strat_name,
                                wing_strat_stats,
                            )
                            break
                if not self.found_stratagem:
                    if booster := json_dict["items"]["boosters"].get(
                        str(self.mix_id), {}
                    ):
                        self.found_booster: dict = booster
            if objective := self.values_dict.get(7):
                self.objective = objective
            if value8 := self.values_dict.get(8):
                self.value8 = value8
                print(f"VALUE8 USED: {self.type, self.value8 = }")
            if difficulty := self.values_dict.get(9):
                self.difficulty = difficulty
            if value10 := self.values_dict.get(10):
                self.value10 = value10
                print(f"VALUE10 USED: {self.type, self.value10 = }")
            if location_type := self.values_dict.get(11):
                if location_type == 1:
                    self.planet_index: int = self.values_dict.get(12)
                elif location_type == 2:
                    self.sector_index: int = self.values_dict.get(12)

    class Reward(ReprMixin):
        __slots__ = ("type", "amount")

        def __init__(self, reward: dict):
            self.type: int = reward["type"]
            self.amount: int = reward["amount"]
