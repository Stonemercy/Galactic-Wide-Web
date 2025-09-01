from data.lists import custom_colours
from disnake import Colour, Embed
from utils.data import Dispatch
from utils.mixins import EmbedReprMixin


class DispatchEmbed(Embed, EmbedReprMixin):
    def __init__(
        self, language_json: dict, dispatch: Dispatch, with_time: bool = False
    ):
        super().__init__(
            title="NEW DISPATCH", colour=Colour.from_rgb(*custom_colours["MO"])
        )
        self.title, self.description = dispatch.title[:256], dispatch.description
        if with_time:
            self.add_field(
                "Send Time", f"<t:{int(dispatch.published_at.timestamp())}:R>"
            )
        self.set_footer(text=language_json["message"].format(message_id=dispatch.id))
