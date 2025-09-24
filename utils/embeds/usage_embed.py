from datetime import datetime
from disnake import Colour, Embed
from utils.mixins import EmbedReprMixin


# DOESNT NEED LOCALIZATION
class UsageEmbed(Embed, EmbedReprMixin):
    def __init__(self, command_usage: dict, guilds_joined: int):
        super().__init__(title="Daily Usage", colour=Colour.dark_theme())
        for command_name, usage in command_usage.items():
            self.add_field(f"/{command_name}", f"Used **{usage}** times", inline=False)
        self.add_field("Guilds joined", guilds_joined, inline=False)
        self.add_field(
            "", f"-# as of <t:{int(datetime.now().timestamp())}:R>", inline=False
        )
