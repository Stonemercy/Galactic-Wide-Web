from datetime import datetime, timedelta
from random import randint
from utils.functions import health_bar


class TestAssignment:
    def __init__(self):
        self.id: int = randint(1111111111111, 9999999999999)
        self.title = "This is a test Major Order, please ignore."
        self.description = "This would be the description"
        self.tasks = TestTasks()
        self.rewards = [
            {"type": 1, "id32": 897894480, "amount": 50},
            {"type": 1, "id32": 3608481516, "amount": 10000},
        ]
        random_end_time = (datetime.now() + timedelta(days=7)).isoformat()
        self.ends_at = random_end_time
        self.ends_at_datetime = datetime.fromisoformat(self.ends_at)


class TestTasks(list):
    def __init__(self):
        self.extend(
            [
                self.TestType2(),
                self.TestType3(),
                self.TestType11(),
                self.TestType12(),
                self.TestType13(),
                self.TestType15(),
            ]
        )

    class TestType2:
        """Extract with certain items from a certain planet"""

        def __init__(self):
            self.type: int = 2
            self.progress: float = 0.35
            self.values: list = [0, 0, 300000, 0, 3992382197, 0, 0, 0, 200]
            self.value_types: list = ["valueTypes"]

        @property
        def health_bar(self) -> str:
            return health_bar(self.progress, "MO")

    class TestType3:
        """Kill enemies of a type"""

        def __init__(self):
            self.type: int = 3
            self.progress = 0.35
            self.values: list = [4, 0, 20000000, 4211847317, 0, 1978117092]
            self.value_types: list = ["valueTypes"]

        @property
        def health_bar(self) -> str:
            return health_bar(
                self.progress,
                (self.values[0] if self.progress != 1 else "Humans"),
            )

    class TestType11:
        """Liberate a planet"""

        def __init__(self):
            self.type: int = 11
            self.progress: float = 1
            self.values: list = [0, 0, 200]
            self.value_types: list = ["valueTypes"]

    class TestType12:
        """Succeed in defence of # <enemy> planets"""

        def __init__(self):
            self.type: int = 12
            self.progress: float = 0.35
            self.values: list = [5, 4, 0, 200]
            self.value_types: list = ["valueTypes"]

        @property
        def health_bar(self) -> str:
            return health_bar(
                self.progress,
                "MO" if self.progress < 1 else "Humans",
            )

    class TestType13:
        """Hold a planet until the end of the MO"""

        def __init__(self):
            self.type: int = 13
            self.progress: float = 1
            self.values: list = [0, 0, 200]
            self.value_types: list = ["valueTypes"]

    class TestType15:
        """Win more campaigns than lost"""

        def __init__(self):
            self.type: int = 15
            self.progress: float = -2
            self.values: list = ["values"]
            self.value_types: list = ["valueTypes"]

        @property
        def health_bar(self) -> str:
            return health_bar(
                self.progress,
                ("Humans" if self.progress > 0 else "Automaton"),
            )
