from datetime import datetime, timedelta, timezone
from data.lists import CUSTOM_COLOURS
from disnake import Colour
from disnake.ui import Container, Separator, TextDisplay
from utils.api_wrapper.models import Dispatch


class DispatchContainer(Container):
    def __init__(
        self, dispatch_json: dict, dispatch: Dispatch, with_time: bool = False
    ):
        components = []
        title, description = dispatch.title, dispatch.description
        text_display = TextDisplay("")
        if title:
            text_display.content += f"# {title}"
        if description:
            text_display.content += f"\n{description}"
        components.append(text_display)

        extra_text_display = TextDisplay("")
        if with_time or dispatch.published_at < datetime.now(
            tz=timezone.utc
        ) - timedelta(hours=1):
            extra_text_display.content += dispatch_json["with_time"].format(
                timestamp=int(dispatch.published_at.timestamp())
            )
        extra_text_display.content += f"\n-# {dispatch_json['dispatch']} #{dispatch.id}"
        components.extend([Separator(), extra_text_display])

        super().__init__(
            *components,
            accent_colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
        )
