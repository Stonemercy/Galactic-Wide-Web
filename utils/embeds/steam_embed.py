from disnake import Colour, Embed
from utils.api_wrapper.models import SteamNews
from utils.mixins import EmbedReprMixin


class SteamEmbed(Embed, EmbedReprMixin):
    def __init__(self, steam: SteamNews, language_json: dict):
        super().__init__(title=steam.title, colour=Colour.dark_theme(), url=steam.url)
        self.set_footer(text=language_json["message"].format(message_id=steam.id))
        self.add_field(
            "",
            f"-# Posted <t:{int(steam.published_at.timestamp())}:R>\n-# <t:{int(steam.published_at.timestamp())}:F>",
        )
