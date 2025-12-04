from data.lists import CUSTOM_COLOURS
from disnake import Colour, ui
from utils.api_wrapper.models import Dispatch
from utils.mixins import ReprMixin


class DispatchContainer(ui.Container, ReprMixin):
    def __init__(
        self, dispatch_json: dict, dispatch: Dispatch, with_time: bool = False
    ):
        components = []
        title, description = dispatch.title, dispatch.description
        text_display = ui.TextDisplay(f"# {title}\n{description}")
        components.append(text_display)

        extra_text_display = ui.TextDisplay("")
        if with_time:
            extra_text_display.content += dispatch_json["with_time"].format(
                timestamp=int(dispatch.published_at.timestamp())
            )
        extra_text_display.content += f"\n-# {dispatch_json['dispatch']} #{dispatch.id}"
        components.extend([ui.Separator(), extra_text_display])

        super().__init__(
            *components,
            accent_colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
        )
