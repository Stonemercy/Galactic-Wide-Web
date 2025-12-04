from enum import Enum


class RegionType(Enum):
    SETTLEMENT = 1
    TOWN = 2
    CITY = 3
    MEGA_CITY = 4


class EndpointBase(Enum):
    HELLDIVERS = "https://api.live.prod.thehelldiversgame.com/api/"
    STEAM_PLAYER_COUNT = (
        "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
    )
    STEAM_NEWS = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=553850&count=20&maxlength=0&format=json"


DEFENCE_LEVEL_EXCLAMATION_DICT = {
    0: "",
    5: "!",
    20: "!!",
    33: "!!!",
    50: " :warning:",
    100: " :skull:",
    250: " :skull_crossbones:",
}

ENDPOINTS = {
    "global_stats": "https://api.live.prod.thehelldiversgame.com/api/Stats/War/{war_id}/Summary",
}
