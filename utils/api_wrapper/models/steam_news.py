from datetime import datetime
from ...mixins import ReprMixin


class SteamNews(ReprMixin):
    def __init__(self, raw_steam_data: dict) -> None:
        """Organised data for a Steam announcements"""
        self.id: int = int(raw_steam_data["gid"])
        self.title: str = raw_steam_data["title"]
        self.author: str = raw_steam_data["author"]
        self.url: str = raw_steam_data["url"]
        self.published_at: datetime = datetime.fromtimestamp(raw_steam_data["date"])
