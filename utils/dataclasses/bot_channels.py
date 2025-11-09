from dataclasses import dataclass
from disnake import TextChannel
from disnake.ext import commands
from utils.dataclasses.config import Config


@dataclass
class BotChannels:
    moderator_channel: TextChannel | None = None
    waste_bin_channel: TextChannel | None = None
    api_changes_channel: TextChannel | None = None

    async def get_channels(self, bot: commands.AutoShardedInteractionBot):
        channels = [
            ("moderator_channel", Config.MODERATION_CHANNEL_ID),
            ("waste_bin_channel", Config.WASTE_BIN_CHANNEL_ID),
            ("api_changes_channel", Config.API_CHANGES_CHANNEL_ID),
        ]
        for attr_name, channel_id in channels:
            channel = getattr(self, attr_name)
            attempts = 0
            while not channel and attempts < 3:
                try:
                    channel = bot.get_channel(channel_id) or await bot.fetch_channel(
                        channel_id
                    )
                    setattr(self, attr_name, channel)
                except Exception:
                    attempts += 1
