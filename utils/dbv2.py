from dataclasses import dataclass
from typing import Self
from dotenv import load_dotenv
from data.lists import language_dict
from os import getenv
from psycopg2 import connect
from psycopg2.extras import Json
from utils.mixins import ReprMixin

load_dotenv(dotenv_path=".env")
hostname = getenv(key="DB_HOSTNAME")
database = getenv(key="DB_NAME")
database = "GWW V2"
username = getenv(key="DB_USERNAME")
pwd = getenv(key="DB_PWD")
port_id = getenv(key="DB_PORT_ID")


def connection():
    return connect(
        host=hostname, dbname=database, user=username, password=pwd, port=port_id
    )


class BotDashboard(ReprMixin):
    __slots__ = ("channel_id", "message_id")

    def __init__(self):
        self.channel_id = None
        self.message_id = None
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM bot.dashboard LIMIT 1")
                record = curs.fetchone()
                if record:
                    self.channel_id: int = record[0]
                    self.message_id: int = record[1]


class WarInfo(ReprMixin):
    __slots__ = ("dispatch_id", "global_event_id", "major_order_ids", "patch_notes_id")

    def __init__(self):
        self.dispatch_id = None
        self.global_event_id = None
        self.major_order_ids = None
        self.patch_notes_id = None
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM war.info LIMIT 1")
                record = curs.fetchone()
                if record:
                    self.dispatch_id: int = record[0]
                    self.global_event_id: int = record[1]
                    self.major_order_ids: list[int] = record[2]
                    self.patch_notes_id: int = record[3]

    def save_changes(self) -> None:
        with connection() as conn:
            with conn.cursor() as curs:
                set_clause = ", ".join(f"{attr} = %s" for attr in self.__slots__)
                values = tuple(getattr(self, attr) for attr in self.__slots__)
                curs.execute(f"UPDATE war.info SET {set_clause}", values)
                conn.commit()


@dataclass
class WarCampaign(ReprMixin):
    campaign_id: int
    planet_index: int
    planet_owner: str
    event: bool
    event_type: int
    event_faction: str

    def delete(self):
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"DELETE FROM war.campaigns WHERE campaign_id = {self.campaign_id}"
                )
                conn.commit()


class WarCampaigns(list[WarCampaign], ReprMixin):
    def __init__(self):
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM war.campaigns")
                records = curs.fetchall()
                if records:
                    for record in records:
                        self.append(WarCampaign(*record))

    def add(
        self,
        campaign_id: int,
        planet_index: int,
        planet_owner: str,
        event: bool,
        event_type: int,
        event_faction: str,
    ) -> None:
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT INTO war.campaigns (campaign_id, planet_index, planet_owner, event, event_type, event_faction) VALUES (%s, %s, %s, %s, %s, %s)",
                    vars=(
                        campaign_id,
                        planet_index,
                        planet_owner,
                        event,
                        event_type,
                        event_faction,
                    ),
                )

                conn.commit()
        self.append(
            WarCampaign(
                campaign_id,
                planet_index,
                planet_owner,
                event,
                event_type,
                event_faction,
            )
        )


class DSSInfo(ReprMixin):
    __slots__ = ("planet_index", "tactical_action_statuses")

    def __init__(self):
        self.planet_index = None
        self.tactical_action_statuses = {}
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM war.dss LIMIT 1")
                record = curs.fetchone()
                if record:
                    self.planet_index: int = record[0]
                    self.tactical_action_statuses: dict[int, int] = {
                        int(k): v for k, v in record[1].items()
                    }

    def save_changes(self) -> None:
        with connection() as conn:
            with conn.cursor() as curs:
                set_clause = ", ".join(f"{attr} = %s" for attr in self.__slots__)
                values = tuple(
                    (
                        Json(getattr(self, attr))
                        if isinstance(getattr(self, attr), dict)
                        else getattr(self, attr)
                    )
                    for attr in self.__slots__
                )
                curs.execute(f"UPDATE war.dss SET {set_clause}", values)
                conn.commit()


@dataclass
class Feature(ReprMixin):
    name: str
    guild_id: int
    channel_id: int
    message_id: int | None = None

    def disable(self):
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"DELETE FROM feature.{self.name} WHERE guild_id = {self.guild_id}"
                )
                conn.commit()


class GWWGuild(ReprMixin):
    def __init__(
        self,
        guild_id: int,
        language: str,
        feature_keys: list[str],
    ):
        self.guild_id = guild_id
        self.language = language
        self.feature_keys = feature_keys
        self.features: list[Feature] = []
        if feature_keys:
            self.get_features()

    @property
    def language_long(self) -> str:
        """Returns the full version of the language's name

        e.g. `en` becomes `English`"""
        return {v: k for k, v in language_dict.items()}[self.language]

    def get_features(self):
        with connection() as conn:
            with conn.cursor() as curs:
                for feature_key in self.feature_keys:
                    curs.execute(
                        query=f"SELECT * FROM feature.{feature_key} WHERE guild_id = {self.guild_id}"
                    )
                    record = curs.fetchone()
                    if record:
                        self.features.append(
                            Feature(feature_key, self.guild_id, *record[1:])
                        )

    def update_features(self):
        update_feature_keys = False
        with connection() as conn:
            with conn.cursor() as curs:
                for feature in self.features:
                    if feature.name not in self.feature_keys:
                        update_feature_keys = True
                        self.feature_keys.append(feature.name)
                        match feature.name:
                            case "dashboard" | "map":
                                curs.execute(
                                    f"INSERT INTO feature.{feature.name} (guild_id, channel_id, message_id) VALUES (%s, %s, %s)",
                                    (
                                        self.guild_id,
                                        feature.channel_id,
                                        feature.message_id,
                                    ),
                                )
                            case _:
                                curs.execute(
                                    f"INSERT INTO feature.{feature.name} (guild_id, channel_id) VALUES (%s, %s)",
                                    (self.guild_id, feature.channel_id),
                                )
                for feature_key in self.feature_keys.copy():
                    if feature_key not in [f.name for f in self.features]:
                        curs.execute(
                            f"DELETE FROM feature.{feature_key} WHERE guild_id = %s",
                            (self.guild_id,),
                        )
                        self.feature_keys.remove(feature_key)
                        update_feature_keys = True
                if update_feature_keys:
                    curs.execute(
                        "UPDATE discord.guilds SET feature_keys = %s WHERE guild_id = %s",
                        (self.feature_keys, self.guild_id),
                    )
                conn.commit()

    def save_changes(self) -> None:
        """Save changes to the database"""
        with connection() as conn:
            with conn.cursor() as curs:
                set_clause = ", ".join(
                    f"{attr} = %s"
                    for attr in self.__dict__.keys()
                    if attr != "features"
                )
                values = tuple(
                    getattr(self, attr)
                    for attr in self.__dict__.keys()
                    if attr != "features"
                )
                curs.execute(
                    f"UPDATE discord.guilds SET {set_clause} WHERE guild_id = %s",
                    values + (self.guild_id,),
                )
                conn.commit()

    def reset(self) -> None:
        """Reset this entry to default"""
        self.language = "en"
        for feature_key in self.feature_keys:
            with connection() as conn:
                with conn.cursor() as curs:
                    curs.execute(
                        query=f"DELETE FROM feature.{feature_key} WHERE guild_id = {self.guild_id}"
                    )
                conn.commit()
        self.features = []
        self.feature_keys = []
        self.save_changes()

    def delete(self):
        with connection() as conn:
            with conn.cursor() as curs:
                for feature_key in self.feature_keys:
                    curs.execute(
                        query=f"DELETE FROM feature.{feature_key} WHERE guild_id = {self.guild_id}"
                    )
                curs.execute(
                    query=f"DELETE FROM discord.guilds WHERE guild_id = {self.guild_id}"
                )
                conn.commit()

    @classmethod
    def default(cls) -> Self:
        """Return a default class"""
        return cls(0, "en", [])


class GWWGuilds(list[GWWGuild], ReprMixin):
    def __init__(self, fetch_all: bool = False):
        if fetch_all:
            with connection() as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM discord.guilds")
                    records = curs.fetchall()
                    if records:
                        for record in records:
                            self.append(GWWGuild(*record))

    @property
    def unique_languages(self) -> list[str]:
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT DISTINCT language FROM discord.guilds")
                records = curs.fetchall()
                return [record[0] for record in records]

    def get_specific_guild(id: int) -> GWWGuild | None:
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"SELECT * FROM discord.guilds WHERE guild_id = {id}"
                )
                record = curs.fetchone()
                if record:
                    return GWWGuild(*record)
        return None

    def add(
        guild_id: int,
        language: str,
        feature_keys: list[str],
    ) -> GWWGuild:
        print(guild_id, feature_keys)
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT INTO discord.guilds (guild_id, language, feature_keys) VALUES (%s, %s, %s)",
                    vars=(guild_id, language, feature_keys),
                )
                conn.commit()
        return GWWGuild(guild_id, language, feature_keys)
