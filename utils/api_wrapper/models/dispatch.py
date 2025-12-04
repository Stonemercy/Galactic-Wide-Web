from ...functions import dispatch_format
from ...mixins import ReprMixin
from datetime import datetime


class Dispatch(ReprMixin):
    __slots__ = ("id", "published_at", "full_message")

    def __init__(self, raw_dispatch_data: dict, war_start_timestamp: int) -> None:
        """Organised data of a dispatch"""
        self.id: int = raw_dispatch_data["id"]
        self.published_at: datetime = datetime.fromtimestamp(
            war_start_timestamp + raw_dispatch_data.get("published", 0)
        )
        self.full_message: str = dispatch_format(
            text=raw_dispatch_data.get("message", "")
        )
        split_lines = self.full_message.splitlines(True)
        if split_lines:
            self.title = split_lines[0].replace("*", "")
            self.description = "".join(split_lines[1:]).strip()
        else:
            self.title = "New Dispatch"
            self.description = self.full_message
