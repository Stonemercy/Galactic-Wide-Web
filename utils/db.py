from data.lists import language_dict
from datetime import datetime, timedelta
from dotenv import load_dotenv
from math import sqrt
from os import getenv
from psycopg2 import connect
from typing import Self
from utils.mixins import ReprMixin

load_dotenv(dotenv_path="data/.env")
hostname = getenv(key="DB_hostname")
database = getenv(key="DB_NAME")
username = getenv(key="DB_username")
pwd = getenv(key="DB_pwd")
port_id = getenv(key="DB_port_id")


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
        """Organised data for a Guild in the GWW's database"""
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
    def language_long(self) -> str:
        """Returns the full version of the language's name

        e.g. `en` becomes `English`"""
        return {v: k for k, v in language_dict.items()}[self.language]

    @classmethod
    def get_by_id(cls, guild_id: int) -> Self | None:
        """Get a guild from the DB by their guild ID"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM guilds WHERE guild_id = {guild_id}")
                record = curs.fetchone()
                return None if not record else cls(*record)

    @classmethod
    def get_all(cls) -> list[Self]:
        """Get a list of all the guild entries in the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM guilds")
                records = curs.fetchall()
                return [cls(*record) for record in records] if records else None

    @classmethod
    def new(cls, guild_id: int) -> Self:
        """Insert a new guild into the database and return the entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"INSERT INTO guilds (guild_id) VALUES ({guild_id})")
                conn.commit()
                curs.execute(query=f"SELECT * FROM guilds WHERE guild_id = {guild_id}")
                record = curs.fetchone()
                return cls(*record)

    @classmethod
    def default(cls) -> Self:
        """Return a default class"""
        return cls(0, 0, 0, 0, False, "en", 0, 0, False, False, False)

    def delete(guild_id: int) -> None:
        """Delete a guild from the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"DELETE FROM guilds WHERE guild_id = {guild_id}")
                conn.commit()

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"""UPDATE guilds SET dashboard_channel_id = {self.dashboard_channel_id},
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
    def __init__(self) -> None:
        """Organised data for the bot's mini dashboard"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM bot_dashboard")
                record = curs.fetchone()
                if record:
                    self.channel_id = record[0]
                    self.message_id = record[1]
                else:
                    self.channel_id = 0
                    self.message_id = 0

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"UPDATE bot_dashboard SET message_id = {self.message_id}"
                )
                conn.commit()


class MajorOrder(ReprMixin):
    def __init__(self) -> None:
        """Organised data for the Major Order info in the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM major_order")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"UPDATE major_order SET id = {self.id}")
                conn.commit()


class GlobalEvent(ReprMixin):
    def __init__(self) -> None:
        """Organised data for the Global Events info in the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM global_events")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"UPDATE global_events SET id = {self.id}")
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
        """Organised data for the Campaigns info in the database"""
        self.id: int = id
        self.owner: str = owner
        self.planet_index: int = planet_index
        self.event: bool | None = event
        self.event_type: int | None = event_type
        self.event_faction: str | None = event_faction

    @classmethod
    def get_all(cls) -> list[Self]:
        """Get a list of all the campaign entries in the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM campaigns")
                records = curs.fetchall()
                return [cls(*record) for record in records] if records else None

    def new(
        id: int,
        owner: str,
        planet_index: int,
        event: bool,
        event_type: int,
        event_faction: str,
    ) -> None:
        """Inserts a new entry into the campaigns database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                if event_type == None:
                    event_type = 0
                curs.execute(
                    query=f"INSERT INTO campaigns (id, owner, planet_index, event, event_type, event_faction) VALUES {id, owner, planet_index, event, event_type, f'{event_faction}'}"
                )
                conn.commit()

    def delete(id: int) -> None:
        """Delets a campaign from the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"DELETE FROM campaigns WHERE id = {id}")
                conn.commit()


class Dispatch(ReprMixin):
    def __init__(self) -> None:
        """Organised data for the Dispatch info in the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM dispatches")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self) -> None:
        """Save the changes to the DB"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"UPDATE dispatches SET id = {self.id}")
                conn.commit()


class Steam(ReprMixin):
    def __init__(self) -> None:
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query="SELECT * FROM steam")
                record = curs.fetchone()
                self.id = record[0]

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"UPDATE steam SET id = {self.id}")
                conn.commit()


class FeedbackUser(ReprMixin):
    __slots__ = ("user_id", "banned", "reason", "good_feedback")

    def __init__(
        self, user_id: int, banned: bool, reason: str, good_feedback: bool
    ) -> None:
        """Organised data for the for user feedback info in the database"""
        self.user_id: int = user_id
        self.banned: bool = banned
        self.reason: str = reason
        self.good_feedback: bool = good_feedback

    @classmethod
    def get_by_id(cls, user_id: int) -> Self:
        """Fetch a user by their ID"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM feedback WHERE user_id = {user_id}")
                record = curs.fetchone()
                return FeedbackUser.new(user_id=user_id) if not record else cls(*record)

    @classmethod
    def new(
        cls,
        user_id: int,
        banned: bool = False,
        reason: str = "None Given",
        good_feedback: bool = False,
    ) -> Self:
        """Insert a new user into the feedback database and return the entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT INTO feedback (user_id, banned, reason, good_feedback) VALUES {user_id, banned, reason, good_feedback}"
                )
                conn.commit()
                curs.execute(query=f"SELECT * FROM feedback WHERE user_id = {user_id}")
                result = curs.fetchone()
                return cls(*result) if result else None

    def delete(user_id: int) -> None:
        """Delete a user from the feedback database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"DELETE FROM feedback WHERE id = {user_id}")
                conn.commit()

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"UPDATE feedback SET user_id = {self.user_id}, banned = {self.banned}, reason = '{self.reason}', good_feedback = {self.good_feedback} where user_id = {self.user_id}"
                )
                conn.commit()


class DSS(ReprMixin):
    __slots__ = ("planet_index", "ta1_status", "ta2_status", "ta3_status")

    def __init__(self) -> None:
        """Organised data for the DSS info in the database"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM dss")
                record = curs.fetchone()
                self.planet_index: int = record[0]
                self.ta1_status: int = record[1]
                self.ta2_status: int = record[2]
                self.ta3_status: int = record[3]

    def save_changes(self) -> None:
        """Save any changes made to this entry"""
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"UPDATE dss SET planet_index = {self.planet_index}, ta1_status = {self.ta1_status}, ta2_status = {self.ta2_status}, ta3_status = {self.ta3_status}"
                )
                conn.commit()


class Meridia(ReprMixin):
    def __init__(self) -> None:
        """Organised data for the Meridia database info"""
        with connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id,
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM meridia")
                records = curs.fetchall()
                self.locations: list[Meridia.Location] = [
                    Meridia.Location(*record) for record in records
                ]
        self.now = datetime.now()
        self.last_4_hours = [
            location
            for location in self.locations
            if location.timestamp > self.now - timedelta(hours=4, minutes=5)
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
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT into meridia (timestamp, x, y) VALUES {timestamp, x, y}"
                )
                conn.commit()
                self.locations.append(
                    self.Location(datetime.fromisoformat(timestamp), x, y)
                )
