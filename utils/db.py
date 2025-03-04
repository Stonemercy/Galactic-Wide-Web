from datetime import datetime, timedelta
from math import sqrt
from typing import Self
from data.lists import language_dict
from dotenv import load_dotenv
from os import getenv
from psycopg2 import connect

from utils.mixins import ReprMixin

load_dotenv("data/.env")
hostname = getenv("DB_hostname")
database = getenv("DB_NAME")
username = getenv("DB_username")
pwd = getenv("DB_pwd")
port_id = getenv("DB_port_id")


class GWWGuild(ReprMixin):
    __slots__ = (
        "id",
        "dashboard_channel_id",
        "dashboard_message_id",
        "announcement_channel_id",
        "patch_notes",
        "language",
        "map_channel_id",
        "map_message_id",
        "major_order_updates",
        "personal_order_updates",
        "detailed_dispatches",
    )

    def __init__(
        self,
        id: int,
        dashboard_channel_id: int,
        dashboard_message_id: int,
        announcement_channel_id: int,
        patch_notes: bool,
        language: str,
        map_channel_id: int,
        map_message_id: int,
        major_order_updates: bool,
        personal_order_updates: bool,
        detailed_dispatches: bool,
    ):
        self.id: int = id
        self.dashboard_channel_id: int = dashboard_channel_id
        self.dashboard_message_id: int = dashboard_message_id
        self.announcement_channel_id: int = announcement_channel_id
        self.patch_notes: bool = patch_notes
        self.language: str = language
        self.map_channel_id: int = map_channel_id
        self.map_message_id: int = map_message_id
        self.major_order_updates: bool = major_order_updates
        self.personal_order_updates: bool = personal_order_updates
        self.detailed_dispatches: bool = detailed_dispatches

    @property
    def language_long(self):
        return {v: k for k, v in language_dict.items()}[self.language]

    @classmethod
    def get_by_id(cls, guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"SELECT * FROM guilds WHERE guild_id = {guild_id}")
                record = curs.fetchone()
                return GWWGuild.new(guild_id) if not record else cls(*record)

    @classmethod
    def get_all(cls) -> list[Self]:
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM guilds")
                records = curs.fetchall()
                return [cls(*record) for record in records] if records else None

    @classmethod
    def new(cls, guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"INSERT INTO guilds (guild_id) VALUES ({guild_id})")
                conn.commit()
                curs.execute(f"SELECT * FROM guilds WHERE guild_id = {guild_id}")
                record = curs.fetchone()
                return cls(*record)

    @classmethod
    def default(cls):
        return cls(0, 0, 0, 0, False, "en", 0, 0, False, False, False)

    def delete(guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"DELETE FROM guilds WHERE guild_id = {guild_id}")
                conn.commit()

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f"""UPDATE guilds SET dashboard_channel_id = {self.dashboard_channel_id},
                    dashboard_message_id = {self.dashboard_message_id},
                    announcement_channel_id = {self.announcement_channel_id},
                    patch_notes = {self.patch_notes},
                    language = '{self.language}',
                    map_channel_id = {self.map_channel_id},
                    map_message_id = {self.map_message_id},
                    major_order_updates = {self.major_order_updates},
                    personal_order_updates = {self.personal_order_updates},
                    detailed_dispatches = {self.detailed_dispatches}
                    where guild_id = {self.id}"""
                )
                conn.commit()


class BotDashboard(ReprMixin):
    __slots__ = ("channel_id", "message_id")

    def __init__(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM bot_dashboard")
                record = curs.fetchone()
                if record:
                    self.channel_id = record[0]
                    self.message_id = record[1]
                else:
                    self.channel_id = 0
                    self.message_id = 0

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"UPDATE bot_dashboard SET message_id = {self.message_id}")
                conn.commit()


class MajorOrder(ReprMixin):
    __slots__ = "id"

    def __init__(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM major_order")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"UPDATE major_order SET id = {self.id}")
                conn.commit()


class GlobalEvent(ReprMixin):
    __slots__ = "id"

    def __init__(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM global_events")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"UPDATE global_events SET id = {self.id}")
                conn.commit()


class Campaign(ReprMixin):
    __slots__ = ("id", "owner", "planet_index", "event", "event_type", "event_faction")

    def __init__(
        self,
        id: int,
        owner: str,
        planet_index: int,
        event: bool,
        event_type: int,
        event_faction: str,
    ):
        self.id: int = id
        self.owner: str = owner
        self.planet_index: int = planet_index
        self.event: bool | None = event
        self.event_type: int | None = event_type
        self.event_faction: str | None = event_faction

    @classmethod
    def get_all(cls) -> list:
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM campaigns")
                records = curs.fetchall()
                return [cls(*record) for record in records] if records else None

    def new(
        id: int,
        owner: str,
        planet_index: int,
        event: bool,
        event_type: int,
        event_faction: str,
    ):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                if event_type == None:
                    event_type = 0
                curs.execute(
                    f"INSERT INTO campaigns (id, owner, planet_index, event, event_type, event_faction) VALUES {id, owner, planet_index, event, event_type, f'{event_faction}'}"
                )
                conn.commit()
                curs.execute

    def delete(id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"DELETE FROM campaigns WHERE id = {id}")
                conn.commit()


class Dispatch(ReprMixin):
    __slots__ = "id"

    def __init__(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM dispatches")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"UPDATE dispatches SET id = {self.id}")
                conn.commit()


class Steam(ReprMixin):
    __slots__ = "id"

    def __init__(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM steam")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"UPDATE steam SET id = {self.id}")
                conn.commit()


class FeedbackUser(ReprMixin):
    __slots__ = ("user_id", "banned", "reason", "good_feedback")

    def __init__(self, user_id: int, banned: bool, reason: str, good_feedback: bool):
        self.user_id = user_id
        self.banned = banned
        self.reason = reason
        self.good_feedback = good_feedback

    @classmethod
    def get_by_id(cls, user_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"SELECT * FROM feedback WHERE user_id = {user_id}")
                record = curs.fetchone()
                return FeedbackUser.new(user_id) if not record else cls(*record)

    @classmethod
    def new(
        cls,
        user_id: int,
        banned: bool = False,
        reason: str = "None Given",
        good_feedback: bool = False,
    ):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f"INSERT INTO feedback (user_id, banned, reason, good_feedback) VALUES {user_id, banned, reason, good_feedback}"
                )
                conn.commit()
                curs.execute(f"SELECT * FROM feedback WHERE user_id = {user_id}")
                result = curs.fetchone()
                return cls(*result) if result else None

    def delete(user_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"DELETE FROM feedback WHERE id = {user_id}")
                conn.commit()

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f"UPDATE feedback SET user_id = {self.user_id}, banned = {self.banned}, reason = '{self.reason}', good_feedback = {self.good_feedback} where user_id = {self.user_id}"
                )
                conn.commit()


class DSS(ReprMixin):
    __slots__ = ("planet_index", "ta1_status", "ta2_status", "ta3_status")

    def __init__(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"SELECT * FROM dss")
                record = curs.fetchone()
                self.planet_index = record[0]
                self.ta1_status = record[1]
                self.ta2_status = record[2]
                self.ta3_status = record[3]

    def save_changes(self):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f"UPDATE dss SET planet_index = {self.planet_index}, ta1_status = {self.ta1_status}, ta2_status = {self.ta2_status}, ta3_status = {self.ta3_status}"
                )
                conn.commit()


class Meridia(ReprMixin):
    __slots__ = "locations"

    def __init__(self):
        with connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id,
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(f"SELECT * FROM meridia")
                records = curs.fetchall()
                self.locations = [self.Location(*record) for record in records]
        self.now = datetime.now()
        self.last_4_hours = [
            location
            for location in self.locations
            if location.timestamp > self.now - timedelta(hours=4, minutes=5)
        ]

    @property
    def speed(self):
        "returns speed in units per second"
        current_location = self.locations[-1]
        location_four_hours_ago = self.locations[-16]
        time_difference = (
            current_location.timestamp - location_four_hours_ago.timestamp
        ).total_seconds()
        delta_x = current_location.x - location_four_hours_ago.x
        delta_y = current_location.y - location_four_hours_ago.y
        distance_moved = sqrt(delta_x**2 + delta_y**2)
        return distance_moved / time_difference  # in units per second

    class Location(ReprMixin):
        def __init__(self, timestamp, x, y):
            self.timestamp: datetime = timestamp
            self.x = x
            self.y = y
            self.as_tuple = (self.x, self.y)

    def new_location(self, timestamp, x, y):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f"INSERT into meridia (timestamp, x, y) VALUES {timestamp, x, y}"
                )
                conn.commit()
                self.locations.append(
                    self.Location(datetime.fromisoformat(timestamp), x, y)
                )
