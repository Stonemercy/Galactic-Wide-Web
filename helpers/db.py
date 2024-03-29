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
                record = curs.fetchall()
                if len(record) > 1:
                    print(f"{guild_id} has more than one record in the db")
                return record if record != [] else False

    def set_info(guild_id: int, channel_id: int = None, message_id: int = None):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                in_db = Guilds.get_info(guild_id)
                if not in_db:
                    curs.execute(
                        "Insert into guilds (guild_id, channel_id, message_id) VALUES (%s, %s, %s)",
                        (guild_id, 0, 0),
                    )
                    conn.commit()
                if channel_id is not None:
                    curs.execute(
                        "Update guilds set channel_id = %s where guild_id = %s",
                        (channel_id, guild_id),
                    )
                if message_id is not None:
                    curs.execute(
                        "Update guilds set message_id = %s where guild_id = %s",
                        (message_id, guild_id),
                    )

    def get_all_info():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Select * from guilds")
                records = curs.fetchall()
                return records if records != [] else False

    def remove_from_db(guild_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Delete from guilds where guild_id = %s", (guild_id,))

    def not_setup():
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "Select * from guilds where channel_id = 0 or message_id = 0"
                )
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

    def set_info(channel_id: int, message_id: int):
        with connect(
            host=hostname, dbname=database, user=username, password=pwd, port=port_id
        ) as conn:
            with conn.cursor() as curs:
                curs.execute("Delete from bot_dashboard")
                conn.commit()
                curs.execute(
                    "Insert into bot_dashboard (channel_id, message_id) VALUES (%s, %s)",
                    (channel_id, message_id),
                )
