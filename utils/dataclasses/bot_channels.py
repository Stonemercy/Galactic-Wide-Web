from dataclasses import dataclass
from disnake import TextChannel
from disnake.ext import commands


@dataclass
class BotChannels:
    moderator_channel: TextChannel | None = None
    waste_bin_channel: TextChannel | None = None
    api_changes_channel: TextChannel | None = None

    @property
    def all(self) -> list:
        return [
            self.moderator_channel,
            self.waste_bin_channel,
            self.api_changes_channel,
        ]

    async def get_channels(self, bot: commands.AutoShardedInteractionBot, config):
        channels = [
            (
                "moderator_channel",
                config.MODERATION_CHANNEL_ID,
            ),
            (
                "waste_bin_channel",
                config.WASTE_BIN_CHANNEL_ID,
            ),
            (
                "api_changes_channel",
                config.API_CHANGES_CHANNEL_ID,
            ),
        ]
        for attr_name, channel_id in channels:
            channel = getattr(self, attr_name)
            while not channel:
                channel = bot.get_channel(channel_id) or await bot.fetch_channel(
                    channel_id
                )
            setattr(self, attr_name, channel)
