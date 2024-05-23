from dotenv import load_dotenv
from psycopg2 import connect
from os import getenv

load_dotenv("data/.env")
hostname = getenv("DB_hostname")
database = getenv("DB_NAME")
username = getenv("DB_username")
pwd = getenv("DB_pwd")
port_id = getenv("DB_port_id")


class Guilds:
    def get_info(guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
                record = curs.fetchone()
                return record

    def insert_new_guild(guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Insert into guilds (guild_id) VALUES (%s)",
                    (guild_id,),
                )

    def update_dashboard(guild_id: int, channel_id: int, message_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set dashboard_channel_id = %s, dashboard_message_id = %s where guild_id = %s",
                    (channel_id, message_id, guild_id),
                )
                conn.commit()

    def update_announcement_channel(guild_id: int, channel_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set announcement_channel_id = %s where guild_id = %s",
                    (channel_id, guild_id),
                )
                conn.commit()

    def update_map(guild_id: int, channel_id: int, message_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set map_channel_id = %s, map_message_id = %s where guild_id = %s",
                    (channel_id, message_id, guild_id),
                )
                conn.commit()

    def update_patch_notes(guild_id: int, patch_notes: bool):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set patch_notes = %s where guild_id = %s",
                    (patch_notes, guild_id),
                )
                conn.commit()

    def update_language(guild_id: int, language: str):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update guilds set language = %s where guild_id = %s",
                    (language, guild_id),
                )
                conn.commit()

    def get_all_guilds():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds")
                records = curs.fetchall()
                return records if records != [] else False

    def get_used_languages() -> list[str]:
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds")
                records = curs.fetchall()
                languages = []
                for i in records:
                    if i[5] not in languages:
                        languages.append(i[5])
                return languages

    def remove_from_db(guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Delete from guilds where guild_id = %s", (guild_id,))

    def dashboard_not_setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Select * from guilds where dashboard_channel_id = 0 or dashboard_message_id = 0"
                )
                results = curs.fetchall()
                return results

    def feed_not_setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds where announcement_channel_id = 0")
                results = curs.fetchall()
                return results

    def patch_notes_not_setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds where patch_notes = false")
                results = curs.fetchall()
                return results


class BotDashboard:
    def get_info():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM bot_dashboard")
                record = curs.fetchone()
                return record if record else False

    def set_message(message_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update bot_dashboard set message_id = %s",
                    (message_id,),
                )

    def set_react_role(message_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update bot_dashboard set react_role_message_id = %s",
                    (message_id,),
                )


class MajorOrders:
    def setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into major_orders (id) VALUES (%s)", (0,))

    def get_last_id():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM major_orders")
                record = curs.fetchone()
                return record[0] if record != None else None

    def set_new_id(id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update major_orders set id = %s",
                    (id,),
                )
                conn.commit()


class Campaigns:
    def get_all():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from campaigns")
                records = curs.fetchall()
                return records

    def get_campaign(id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from campaigns where id = %s", (id,))
                record = curs.fetchone
                return record

    def new_campaign(id: int, planet_name: str, owner: str, planet_index: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Insert into campaigns (id, planet_name, owner, planet_index) VALUES (%s, %s, %s, %s)",
                    (id, planet_name, owner, planet_index),
                )
                conn.commit()

    def update_campaign(liberation: float = None):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Update campaigns set liberation= %s", (liberation,))
                conn.commit()

    def remove_campaign(id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Delete from campaigns where ID = %s",
                    (id,),
                )
                conn.commit()


class Dispatches:
    def setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into dispatches (id) VALUES (%s)", (0,))

    def get_last_id():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM dispatches")
                record = curs.fetchone()
                return record[0] if record != None else None

    def set_new_id(id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update dispatches set id = %s",
                    (id,),
                )
                conn.commit()


class Steam:
    def setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Insert into steam (id) VALUES (%s)", (0,))

    def get_last_id():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT * FROM steam")
                record = curs.fetchone()
                return record[0] if record != None else None

    def set_new_id(id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Update steam set id = %s",
                    (id,),
                )
                conn.commit()
