from dotenv import load_dotenv
from psycopg2 import connect
from os import getenv

load_dotenv("data/.env")
hostname = getenv("DB_hostname")
database = getenv("DB_NAME")
username = getenv("DB_username")
pwd = getenv("DB_pwd")
port_id = getenv("DB_port_id")


class GuildRecord:
    """A class that contains the information of a guild

    Parameters
    ----------
        db_entry (tuple[int, int, int, int, bool, str, int, int]):
            A record from the DB

    Attributes
    ----------
        guild_id: :class:`int`
            The ID of the guild
        dashboard_channel_id: :class:`int`
            The ID of the dashboard channel, if set up. Defaults to `0`
        dashboard_message_id: :class:`int`
            The ID of the dashboard message, if set up. Defaults to `0`
        announcement_channel_id: :class:`int`
            The ID of the announcement channel, if set up. Defaults to `0`
        patch_notes: :class:`bool`
            If the guild wants patch notes sent to the announcement channel. Defaults to `False`
        language: :class:`str`
            The language code the guild uses. Defaults to `en`
        map_channel_id: :class:`int`
            The ID of the map channel, if set up. Defaults to `0`
        map_message_id: :class:`int`
            The ID of the map message, if set up. Defaults to `0`
    """

    __slots__ = (
        "guild_id",
        "dashboard_channel_id",
        "dashboard_message_id",
        "announcement_channel_id",
        "patch_notes",
        "language",
        "map_channel_id",
        "map_message_id",
    )

    def __init__(
        self, db_entry: tuple[int, int, int, int, bool, str, int, int]
    ) -> None:
        self.guild_id: int = db_entry[0]
        self.dashboard_channel_id: int = db_entry[1]
        self.dashboard_message_id: int = db_entry[2]
        self.announcement_channel_id: int = db_entry[3]
        self.patch_notes: bool = db_entry[4]
        self.language: str = db_entry[5]
        self.map_channel_id: int = db_entry[6]
        self.map_message_id: int = db_entry[7]


class GuildsDB:
    """A class that contains methods to manipulate guild DB data."""

    def get_info(guild_id: int) -> GuildRecord:
        """Get the data for a single guild from the DB

        Parameters
        ----------
            guild_id (int): The ID of the guild

        Returns
        ----------
            :class:`GuildRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
                record = curs.fetchone()
                return GuildRecord(record) if record else None

    def insert_new_guild(guild_id: int) -> GuildRecord:
        """Insert a new guild into the DB

        Parameters
        ----------
            guild_id (int): The ID of the guild

        Returns
        ----------
            :class:`GuildRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Insert into guilds (guild_id) VALUES (%s)",
                    (guild_id,),
                )
                conn.commit()
                results = GuildsDB.get_info(guild_id)
                return results if results else None

    def update_dashboard(guild_id: int, channel_id: int, message_id: int) -> None:
        """Update the dashboard channel and message ID's for a single guild

        Parameters
        ----------
            guild_id (int): The ID of the guild
            channel_id (int): The ID of the dashboard's channel
            message_id (int): The ID of the dashboard's message

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set dashboard_channel_id = %s, dashboard_message_id = %s where guild_id = %s",
                    (channel_id, message_id, guild_id),
                )

    def update_announcement_channel(guild_id: int, channel_id: int) -> None:
        """Update the announcement channel ID for a single guild

        Parameters
        ----------
            guild_id (int): The ID of the guild
            channel_id (int): The ID of the announcement channel

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set announcement_channel_id = %s where guild_id = %s",
                    (channel_id, guild_id),
                )

    def update_map(guild_id: int, channel_id: int, message_id: int) -> None:
        """Update the map channel and message ID's for a single guild

        Parameters
        ----------
            guild_id (int): The ID of the guild
            channel_id (int): The ID of the map's channel
            message_id (int): The ID of the map's message

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set map_channel_id = %s, map_message_id = %s where guild_id = %s",
                    (channel_id, message_id, guild_id),
                )

    def update_patch_notes(guild_id: int, patch_notes: bool) -> None:
        """Update the patch notes choice for a single guild

        Parameters
        ----------
            guild_id (int): The ID of the guild
            patch_notes (bool): Whether the guild wants patch notes sent

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set patch_notes = %s where guild_id = %s",
                    (patch_notes, guild_id),
                )

    def update_language(guild_id: int, language: str) -> None:
        """Update the language choice for a single guild

        Parameters
        ----------
            guild_id (int): The ID of the guild
            language (str): The language code of the guild (e.g. 'en')

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set language = %s where guild_id = %s",
                    (language, guild_id),
                )

    def get_all_guilds() -> list[GuildRecord]:
        """Returns a list of :class:`GuildRecord`'s for each guild in the DB.

        Returns
        ----------
            list[:class:`GuildRecord`]
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds")
                records = curs.fetchall()
                return (
                    [GuildRecord(record) for record in records]
                    if records != []
                    else None
                )

    def get_used_languages() -> list[str]:
        """Get a list of unique languages used in the DB.

        Currently implemented languages:
            `en`
            `fr`
            `de`

        Returns
        ----------
            list[:class:`str`]
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds")
                records = curs.fetchall()
                languages = list(set([record[5] for record in records]))
                return languages

    def remove_from_db(guild_id: int):
        """Remove a guild from the DB

        Parameters
        ----------
            guild_id (int): The ID of the guild

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Delete from guilds where guild_id = %s", (guild_id,))

    def dashboard_not_setup() -> int:
        """Get the amount of guilds without the dashboard setup

        Returns
        ----------
            :class:`int`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Select * from guilds where dashboard_channel_id = 0 or dashboard_message_id = 0"
                )
                results = curs.fetchall()
                return len(results)

    def feed_not_setup() -> int:
        """Get the amount of guilds without the announcements feed setup

        Returns
        ----------
            :class:`int`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds where announcement_channel_id = 0")
                results = curs.fetchall()
                return len(results)

    def patch_notes_not_setup() -> int:
        """Get the amount of guilds without the patch_notes enabled

        Returns
        ----------
            :class:`int`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds where patch_notes = false")
                results = curs.fetchall()
                return len(results)

    def maps_not_setup() -> int:
        """Get the amount of guilds without the map setup

        Returns
        ----------
            :class:`int`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds where map_message_id = 0")
                results = curs.fetchall()
                return len(results)


class BotDashboardRecord:
    """A class that contains the information of the bot dashboard

    Parameters
    ----------
        db_entry (tuple[int, int, int]):
            A record from the DB

    Attributes
    ----------
        channel_id: :class:`int`
            The ID of the bot dashboard channel, if set up. Defaults to `0`
        message_id: :class:`int`
            The ID of the bot dashboard message, if set up. Defaults to `0`
        react_role_message_id: :class:`int`
            The ID of the react-role message, if set up. Defaults to `0`
    """

    def __init__(self, db_entry: tuple[int, int, int]) -> None:
        self.channel_id: int = db_entry[0]
        self.message_id: int = db_entry[1]
        self.react_role_message_id: int = db_entry[2]


class BotDashboardDB:
    """A class that contains methods to manipulate bot dashboard DB data."""

    def get_info() -> BotDashboardRecord:
        """Get the bot dashboard info from the DB

        Returns
        ----------
            :class:`BotDashboardRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM bot_dashboard")
                record = curs.fetchone()
                return BotDashboardRecord(record) if record else None

    def set_message(message_id: int) -> None:
        """Set the bot dashboard message ID

        Parameters
        ----------
            message_id (int): The ID of the bot dashboard's message

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update bot_dashboard set message_id = %s",
                    (message_id,),
                )

    def set_react_role(message_id: int) -> None:
        """Update the react-role message ID

        Parameters
        ----------
            message_id (int): The ID of the react-role message

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update bot_dashboard set react_role_message_id = %s",
                    (message_id,),
                )


class MajorOrderRecord:
    """A class that contains the ID of the last major order

    Parameters
    ----------
        db_entry (tuple[int]):
            A record from the DB

    Attributes
    ----------
        id: :class:`int`
            The ID of the major order.
    """

    def __init__(self, db_entry: tuple[int]) -> None:
        self.id = db_entry[0]

    def __repr__(self):
        return f"MajorOrderRecord(id={self.id})"


class MajorOrderDB:
    """A class that contains methods to manipulate major order DB data."""

    def setup() -> MajorOrderRecord:
        """Sets the ID to 0

        Returns
        ----------
            :class:`MajorOrderRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into major_order (id) VALUES (%s)", (0,))
                conn.commit()
                result = MajorOrderDB.get_last()
                return result

    def get_last() -> MajorOrderRecord:
        """Gets the current stored ID

        Returns
        ----------
            :class:`MajorOrderRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM major_order")
                record = curs.fetchone()
                return MajorOrderRecord(record) if record else None

    def set_new_id(id: int) -> None:
        """Sets the ID to the supplied integer

        Parameters
        ----------
            id (int): The ID of the Major Order

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update major_order set id = %s",
                    (id,),
                )


class CampaignRecord:
    """A class that contains the information of a campaign

    Parameters
    ----------
        db_entry (tuple[int, str, str, int]):
            A record from the DB

    Attributes
    ----------
        id: :class:`int`
            The ID of the campaign.
        planet_name: :class:`str`
            The name of the planet the campaign is on
        owner: :class:`str`
            Owner of the planet the campaign is on
        planet_index: :class:`int`
            The index of the planet the campaign is on
    """

    def __init__(self, db_entry: tuple[int, str, str, int]) -> None:
        self.id = db_entry[0]
        self.planet_name = db_entry[1]
        self.owner = db_entry[2]
        self.planet_index = db_entry[3]


class CampaignsDB:
    """A class that contains methods to manipulate campaigns DB data."""

    def get_all() -> list[CampaignRecord]:
        """Returns a list of :class:`CampaignRecord`'s for each campaign in the DB.

        Returns
        ----------
            list[:class:`CampaignRecord`]
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from campaigns")
                records = curs.fetchall()
                return (
                    [CampaignRecord(record) for record in records]
                    if records != []
                    else None
                )

    def get_campaign(id: int) -> CampaignRecord:
        """Returns a :class:`CampaignRecord`'s if the campaign is found in the DB.

        Parameters
        ----------
            id (int): The ID of the Campaign
        Returns
        ----------
            :class:`CampaignRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from campaigns where id = %s", (id,))
                record = curs.fetchone
                return CampaignRecord(record) if record else None

    def new_campaign(id: int, planet_name: str, owner: str, planet_index: int) -> None:
        """Insert a new Campaign into the DB

        Parameters
        ----------
            id (int): The ID of the Campaign
            planet_name (str): The name of the Planet the Campaign is on
            owner (str): The Current Owner of the Planet the Campaign is on
            planet_index (int): The index of the Planet the Campaign is on

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Insert into campaigns (id, planet_name, owner, planet_index) VALUES (%s, %s, %s, %s)",
                    (id, planet_name, owner, planet_index),
                )

    def remove_campaign(id: int) -> None:
        """Remove a Campaign from the DB

        Parameters
        ----------
            id (int): The ID of the Campaign

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Delete from campaigns where ID = %s",
                    (id,),
                )


class DispatchRecord:
    """A class that contains the ID of the latest dispatch

    Parameters
    ----------
        db_entry (tuple[int]):
            A record from the DB

    Attributes
    ----------
        id: :class:`int`
            The ID of the Dispatch"""

    def __init__(self, db_entry: tuple[int]):
        self.id = db_entry[0]


class DispatchesDB:
    """A class that contains methods to manipulate Dispatches DB data."""

    def setup() -> DispatchRecord:
        """Setup the Dispatches DB

        Returns
        ----------
            :class:`DispatchRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into dispatches (id) VALUES (%s)", (0,))
                conn.commit()
                result = DispatchesDB.get_last()
                return result

    def get_last() -> DispatchRecord:
        """Gets the latest record from the Dispatches DB

        Returns
        ----------
            :class:`DispatchRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM dispatches")
                record = curs.fetchone()
                return DispatchRecord(record) if record else None

    def set_new_id(id: int) -> None:
        """Sets the ID for the Dispatches DB

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update dispatches set id = %s",
                    (id,),
                )


class SteamRecord:
    def __init__(self, db_entry: tuple[int]) -> None:
        """A class that contains the ID of the latest steam patch notes

        Parameters
        ----------
            db_entry (tuple[int]):
                A record from the DB

        Attributes
        ----------
            id: :class:`int`
                The ID of the steam patch notes"""
        self.id = db_entry[0]


class SteamDB:
    """A class that contains methods to manipulate steam DB data."""

    def setup() -> int:
        """Setup the Steam DB

        Returns
        ----------
            :class:`SteamRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into steam (id) VALUES (%s)", (0,))
                conn.commit()
                result = SteamDB.get_last()
                return result

    def get_last() -> SteamRecord:
        """Get the last Patch Notes' ID

        Returns
        ----------
            :class:`SteamRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM steam")
                record = curs.fetchone()
                return SteamRecord(record) if record else None

    def set_new_id(id: int) -> None:
        """Sets the latest Patch Notes' ID

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update steam set id = %s",
                    (id,),
                )


class FeedbackRecord:
    """A class that contains the information of a user that has provided feedback

    Parameters
    ----------
        db_entry (tuple[int, bool, str, bool]):
            A record from the DB

    Attributes
    ----------
        user_id: :class:`int`
            The ID of the user
        banned: :class:`bool`
            If the user is banned from giving feedback. Defaults to `False`
        reason: :class:`str`
            The reason the user is banned.
        good_feedback: :class:`bool`
            If the user has given good feedback. Defaults to `False`
    """

    def __init__(self, db_entry: tuple[int, bool, str, bool]) -> None:
        self.user_id: int = db_entry[0]
        self.banned: bool = db_entry[1]
        self.reason: str = db_entry[2]
        self.good_feedback: bool = db_entry[3]


class FeedbackDB:
    """A class that contains methods to manipulate feedback DB data."""

    def new_user(user_id: int) -> FeedbackRecord:
        """Insert a new user into the DB

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            :class:`FeedbackRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into feedback (user_id) VALUES (%s)", (user_id,))
                conn.commit()
                user = FeedbackDB.get_user(user_id)
                return user if user else None

    def get_user(user_id: int) -> FeedbackRecord:
        """Get a user from the feedback DB

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            :class:`FeedbackRecord`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM feedback where user_id = %s", (user_id,))
                record = curs.fetchone()
                return FeedbackRecord(record) if record else None

    def ban_user(user_id: int) -> None:
        """Ban a user from providing feedback

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update feedback set banned = True where user_id = %s",
                    (user_id,),
                )

    def set_reason(user_id: int, reason: str) -> None:
        """Set a reason for why a user was banned from providing feedback

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update feedback set reason = %s where user_id = %s",
                    (reason, user_id),
                )

    def unban_user(user_id: int) -> None:
        """Unban a user from providing feedback

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update feedback set banned = False, reason = null where user_id = %s",
                    (user_id,),
                )

    def good_user(user_id: int) -> None:
        """Set a user as a good feedback provider

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update feedback set good_feedback = True where user_id = %s",
                    (user_id,),
                )

    def not_good_user(user_id: int) -> None:
        """Unset a user as a good feedback provider

        Parameters
        ----------
            user_id (int): The ID of the user

        Returns
        ----------
            `None`
        """
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update feedback set good_feedback = False where user_id = %s",
                    (user_id,),
                )
