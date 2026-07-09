from datetime import datetime, timezone
from re import DOTALL, match
from utils.functions import arrowhead_format
from utils.mixins import ReprMixin


class Dispatch(ReprMixin):
    __slots__ = ("id", "published_at", "full_message")

    def __init__(self, raw_dispatch_data: dict, war_start_timestamp: int) -> None:
        """Organised data of a dispatch"""
        self.id: int = raw_dispatch_data["id"]
        self.published_at: datetime = datetime.fromtimestamp(
            war_start_timestamp + raw_dispatch_data.get("published", 0), tz=timezone.utc
        )
        self.raw_message = raw_dispatch_data.get("message", "")
        self.full_message: str = arrowhead_format(text=self.raw_message)

        self.title: str = ""
        title_match = match(r"^<i=3>(.*?)</i>\s*", self.raw_message, DOTALL)
        if title_match:
            self.title = arrowhead_format(title_match.group(1).strip()).lstrip("\n")
            self.raw_message = self.raw_message[title_match.end() :].lstrip("\n")

        self.description: str = arrowhead_format(self.raw_message)
