from collections import deque
from typing import Any
from utils.mixins import ReprMixin


class BaseTrackerEntry(ReprMixin):
    def __init__(self, value: int | float, max_entries: int = 15):
        self.value: int | float = value
        self.max_entries: int = max_entries
        self.changes_list: deque = deque(maxlen=self.max_entries)

    def update_data(self, new_value: int | float) -> None:
        delta: int | float = new_value - self.value
        if not self.changes_list:
            self.changes_list.extend([delta] * self.max_entries)
        else:
            self.changes_list.append(delta)
        self.value: int | float = new_value

    @property
    def change_rate_per_hour(self) -> int | float:
        if not self.changes_list:
            return 0
        return sum(self.changes_list) * (60 / len(self.changes_list))

    @property
    def seconds_until_complete(self) -> int:
        rate: int | float = self.change_rate_per_hour
        if rate > 0:
            return int(((1 - self.value) / rate) * 3600)
        elif rate < 0:
            return abs(int(((self.value) / rate) * 3600))
        return 0


class BaseTracker(ReprMixin):
    def __init__(self) -> None:
        self._raw_dict: dict | dict[Any, BaseTrackerEntry] = {}

    def add_entry(self, key, value) -> None:
        if key not in self._raw_dict:
            self._raw_dict[key] = BaseTrackerEntry(value=value)
        else:
            entry: BaseTrackerEntry = self._raw_dict[key]
            entry.update_data(new_value=value)

    def get_entry(self, key) -> BaseTrackerEntry | None:
        return self._raw_dict.get(key)

    def remove_entry(self, key) -> None:
        if key in self._raw_dict:
            self._raw_dict.pop(key)

    def all_keys(self) -> list:
        return list(self._raw_dict.keys())

    def as_dict(self) -> dict:
        return {k: v.value for k, v in self._raw_dict.items()}
