from dataclasses import dataclass
from typing import Self
from psycopg2 import connect
from psycopg2.extras import Json, DictCursor
from utils.mixins import ReprMixin
from utils.dataclasses import Languages, Config


def connection():
    return connect(
        host=Config.DB_HOSTNAME,
        dbname=Config.DATABASE,
        user=Config.DB_USERNAME,
        password=Config.DB_PWD,
        port=Config.DB_PORT_ID,
    )


class BotDashboard(ReprMixin):
    __slots__ = ("channel_id", "message_id")

    def __init__(self):
        self.channel_id = None
        self.message_id = None
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(query=f"SELECT * FROM bot.dashboard LIMIT 1")
                record: tuple[int, int] = curs.fetchone()
                if record:
                    self.channel_id, self.message_id = record

    def save_changes(self):
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"UPDATE bot.dashboard SET channel_id = {self.channel_id}, message_id = {self.message_id}"
                )
                conn.commit()


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
                record: tuple[int, int, list[int], int] = curs.fetchone()
                if record:
                    (
                        self.dispatch_id,
                        self.global_event_id,
                        self.major_order_ids,
                        self.patch_notes_id,
                    ) = record

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


class GWWGuild(ReprMixin):
    def __init__(self, row: dict):
        self.guild_id = row.get("guild_id")
        self.language: str = row.get("language", "en")
        self.feature_keys = row.get("feature_keys", [])
        self.features: list[Feature] = []
        if len(row) > 3:
            features_dict: dict[str, dict[str, int]] = {}
            for key, value in row.items():
                if "__" in key and value is not None:
                    feature, field = key.split("__", 1)
                    if not features_dict.get(feature):
                        features_dict[feature] = {}
                    features_dict[feature][field] = value
            for feature, values in features_dict.items():
                self.features.append(
                    Feature(
                        feature,
                        self.guild_id,
                        values.get("channel_id"),
                        values.get("message_id"),
                    )
                )

    @property
    def language_long(self) -> str:
        """Returns the full version of the language's name

        e.g. `en` becomes `English`"""
        return {lang.short_code: lang.full_name for lang in Languages.all}[
            self.language
        ]

    def update_features(self):
        update_feature_keys = False
        with connection() as conn:
            with conn.cursor() as curs:
                for feature in self.features:
                    if feature.name not in self.feature_keys:
                        update_feature_keys = True
                        self.feature_keys.append(feature.name)
                        match feature.name:
                            case "dashboards" | "maps":
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
        return cls({"guild_id": 0, "language": "en", "feature_keys": []})


class GWWGuilds(list[GWWGuild], ReprMixin):
    def __init__(self, fetch_all: bool = False):
        if fetch_all:
            with connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as curs:
                    curs.execute(
                        (
                            "SELECT "
                            "g.guild_id, g.language, g.feature_keys, "
                            "d.channel_id AS dashboards__channel_id, d.message_id AS dashboards__message_id, "
                            "m.channel_id AS maps__channel_id, m.message_id AS maps__message_id, "
                            "wa.channel_id AS war_announcements__channel_id, "
                            "dss.channel_id AS dss_announcements__channel_id, "
                            "ra.channel_id AS region_announcements__channel_id, "
                            "pn.channel_id AS patch_notes__channel_id, "
                            "mo.channel_id AS major_order_updates__channel_id, "
                            "dd.channel_id AS detailed_dispatches__channel_id "
                            "FROM discord.guilds g "
                            "LEFT JOIN feature.dashboards d ON g.guild_id = d.guild_id "
                            "LEFT JOIN feature.maps m ON g.guild_id = m.guild_id "
                            "LEFT JOIN feature.war_announcements wa ON g.guild_id = wa.guild_id "
                            "LEFT JOIN feature.dss_announcements dss ON g.guild_id = dss.guild_id "
                            "LEFT JOIN feature.region_announcements ra ON g.guild_id = ra.guild_id "
                            "LEFT JOIN feature.patch_notes pn ON g.guild_id = pn.guild_id "
                            "LEFT JOIN feature.major_order_updates mo ON g.guild_id = mo.guild_id "
                            "LEFT JOIN feature.detailed_dispatches dd ON g.guild_id = dd.guild_id"
                        )
                    )
                    records = curs.fetchall()
                    if records:
                        for record in records:
                            record_dict = dict(record)
                            self.append(GWWGuild(record_dict))

    @staticmethod
    def unique_languages() -> list[str]:
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT DISTINCT language FROM discord.guilds")
                records = curs.fetchall()
                return [record[0] for record in records]

    def get_specific_guild(id: int) -> GWWGuild | None:
        with connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as curs:
                curs.execute(
                    (
                        "SELECT "
                        "g.guild_id, g.language, g.feature_keys, "
                        "d.channel_id AS dashboards__channel_id, d.message_id AS dashboards__message_id, "
                        "m.channel_id AS maps__channel_id, m.message_id AS maps__message_id, "
                        "wa.channel_id AS war_announcements__channel_id, "
                        "dss.channel_id AS dss_announcements__channel_id, "
                        "ra.channel_id AS region_announcements__channel_id, "
                        "pn.channel_id AS patch_notes__channel_id, "
                        "mo.channel_id AS major_order_updates__channel_id, "
                        "dd.channel_id AS detailed_dispatches__channel_id "
                        "FROM discord.guilds g "
                        "LEFT JOIN feature.dashboards d ON g.guild_id = d.guild_id "
                        "LEFT JOIN feature.maps m ON g.guild_id = m.guild_id "
                        "LEFT JOIN feature.war_announcements wa ON g.guild_id = wa.guild_id "
                        "LEFT JOIN feature.dss_announcements dss ON g.guild_id = dss.guild_id "
                        "LEFT JOIN feature.region_announcements ra ON g.guild_id = ra.guild_id "
                        "LEFT JOIN feature.patch_notes pn ON g.guild_id = pn.guild_id "
                        "LEFT JOIN feature.major_order_updates mo ON g.guild_id = mo.guild_id "
                        f"LEFT JOIN feature.detailed_dispatches dd ON g.guild_id = dd.guild_id WHERE g.guild_id = {id}"
                    )
                )
                record = curs.fetchone()
                if record:
                    return GWWGuild(dict(record))
        return None

    def add(
        guild_id: int,
        language: str,
        feature_keys: list[str],
    ) -> GWWGuild:
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT INTO discord.guilds (guild_id, language, feature_keys) VALUES (%s, %s, %s)",
                    vars=(guild_id, language, feature_keys),
                )
                conn.commit()
        return GWWGuilds.get_specific_guild(guild_id)


@dataclass
class PlanetRegion(ReprMixin):
    settings_hash: int
    owner: str
    planet_index: int


class PlanetRegions(list[PlanetRegion], ReprMixin):
    def __init__(self):
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM war.regions")
                records = curs.fetchall()
                if records:
                    for record in records:
                        self.append(PlanetRegion(*record))

    def add(self, region) -> None:
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"INSERT INTO war.regions (settings_hash, owner, planet_index) VALUES (%s, %s, %s)",
                    vars=(
                        region.settings_hash,
                        region.owner.full_name,
                        region.planet_index,
                    ),
                )
                conn.commit()
        self.append(region)

    def delete(self, region):
        with connection() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    query=f"DELETE FROM war.regions WHERE settings_hash = {region.settings_hash}"
                )
                conn.commit()
            if region in self:
                self.remove(region)


class Databases:
    def __init__(self) -> None:
        self.war_info = WarInfo()
        self.war_campaigns = WarCampaigns()
        self.dss_info = DSSInfo()
        self.planet_regions = PlanetRegions()
