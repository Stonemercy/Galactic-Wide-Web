from datetime import datetime, timedelta
from dotenv import load_dotenv
from math import sqrt
from os import getenv
from psycopg2 import connect
from utils.mixins import ReprMixin

load_dotenv(dotenv_path=".env")
HOSTNAME = getenv(key="DB_HOSTNAME")
DATABASE = getenv(key="DBV1_NAME")
USERNAME = getenv(key="DB_USERNAME")
PWD = getenv(key="DB_PWD")
PORT_ID = getenv(key="DB_PORT_ID")


class Meridia(ReprMixin):
    def __init__(self) -> None:
        """Organised data for the Meridia database info"""
        with connect(
            host=HOSTNAME,
            dbname=DATABASE,
            user=USERNAME,
            password=PWD,
            port=PORT_ID,
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM meridia")
                records = curs.fetchall()
                self.locations: list[Meridia.Location] = [
                    Meridia.Location(*record) for record in records
                ]
        now = datetime.now()
        self.last_4_hours = [
            location
            for location in self.locations
            if location.timestamp > now - timedelta(hours=4, minutes=5)
        ]

    @property
    def speed(self) -> float:
        "Returns Meridia's speed in Super Units per second"
        current_location = self.locations[-1]
        location_four_hours_ago = self.locations[-16]
        time_difference = (
            current_location.timestamp - location_four_hours_ago.timestamp
        ).total_seconds()
        delta_x = current_location.x - location_four_hours_ago.x
        delta_y = current_location.y - location_four_hours_ago.y
        distance_moved = sqrt(delta_x**2 + delta_y**2)
        return distance_moved / time_difference  # in super units per second

    class Location(ReprMixin):
        def __init__(self, timestamp: datetime, x: float, y: float) -> None:
            """A timestamped location"""
            self.timestamp: datetime = timestamp
            self.x: float = x
            self.y: float = y
            self.as_tuple: tuple[float, float] = (self.x, self.y)

    def new_location(self, timestamp, x, y) -> None:
        """Add a new location entry into the database"""
        with connect(
            host=HOSTNAME, dbname=DATABASE, user=USERNAME, password=PWD, port=PORT_ID
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT into meridia (timestamp, x, y) VALUES {timestamp, x, y}"
                )
                conn.commit()
                self.locations.append(
                    self.Location(datetime.fromisoformat(timestamp), x, y)
                )
