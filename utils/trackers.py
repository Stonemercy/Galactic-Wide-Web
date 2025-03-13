from random import uniform
from utils.mixins import ReprMixin


class LiberationTrackerEntry(ReprMixin):
    def __init__(
        self,
        planet_index: int,
        liberation: float,
        max_entries: int = 15,
    ) -> None:
        """An entry for the Liberation Tracker"""
        self.liberation = liberation
        self.planet_index = planet_index
        self.changes_list = []
        self.max_entries = max_entries

    def update_liberation(self, new_liberation: float) -> None:
        """Update an entry's data

        If it's a campaign's first entry, the data fills up with numbers within 10% of the first change
        e.g. change is 0.10%, the list fills up with numbers from 0.09% to 0.11%
        """
        if not self.changes_list:
            lower_range = (new_liberation - self.liberation) / 1.1
            upper_range = (new_liberation - self.liberation) * 1.1
            while len(self.changes_list) < self.max_entries:
                self.changes_list.append(uniform(lower_range, upper_range))

        while len(self.changes_list) > self.max_entries:
            self.changes_list.pop(0)
        self.changes_list.append(new_liberation - self.liberation)
        self.liberation = new_liberation

    @property
    def rate_per_hour(self) -> float:
        """The entry's rate of change per hour"""
        return sum(self.changes_list) * (60 / self.max_entries)


class LiberationChangesTracker(ReprMixin):
    def __init__(self) -> None:
        """A tracker for planet liberation changes"""
        self._raw_dict = {}
        self.has_data = False

    def add_new_entry(self, planet_index: int, liberation: float) -> None:
        """Adds a new entry to the tracker"""
        if planet_index not in self._raw_dict:
            self._raw_dict[planet_index] = LiberationTrackerEntry(
                planet_index=planet_index, liberation=liberation
            )

    def get_by_index(self, planet_index: int) -> LiberationTrackerEntry | None:
        """Gets an entry by planet index, returning `None` if not present"""
        if planet_index in self._raw_dict:
            return self._raw_dict[planet_index]

    def update_liberation(self, planet_index: int, new_liberation: float):
        """Update a planet's liberation rate"""
        if planet_index in self.tracked_planets:
            entry: LiberationTrackerEntry = self._raw_dict[planet_index]
            entry.update_liberation(new_liberation=new_liberation)
        if not self.has_data:
            self.has_data = True

    def remove_entry(self, planet_index: int):
        """Remove a campaign entry from the tracker"""
        if planet_index in self._raw_dict:
            self._raw_dict.pop(planet_index, None)

    @property
    def tracked_planets(self):
        return self._raw_dict.keys()
