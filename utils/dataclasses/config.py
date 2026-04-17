from json import loads
from os import getenv


class Config:
    BOT_TOKEN: str = getenv("TOKEN")
    BETA_BOT_TOKEN: str = getenv("BETA_TOKEN")
    SUPPORT_SERVER_ID: int = int(getenv("SUPPORT_SERVER"))
    MODERATION_CHANNEL_ID: int = int(getenv("MODERATION_CHANNEL"))
    WASTE_BIN_CHANNEL_ID: int = int(getenv("WASTE_BIN_CHANNEL"))
    API_CHANGES_CHANNEL_ID: int = int(getenv("API_CHANGES_CHANNEL"))

    DB_HOSTNAME: str = getenv("DB_HOSTNAME")
    DATABASE: str = getenv("DBV2_NAME")
    DB_USERNAME: str = getenv("DB_USERNAME")
    DB_PWD: str = getenv("DB_PWD")
    DB_PORT_ID: str = getenv("DB_PORT_ID")

    AUTHED_API_HEADERS: dict[str, str] = loads(getenv("AUTHED_API_HEADERS"))
    AUTHED_API_URL: str = getenv("AUTHED_API_URL")
