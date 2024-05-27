from datetime import datetime
from logging import getLogger
from disnake import PartialMessage
from disnake.ext import commands, tasks
from helpers.db import Guilds

logger = getLogger("disnake")


class ListGenCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_gen.start()

    def cog_unload(self):
        self.message_gen.stop()

    @tasks.loop(count=1)
    async def message_gen(self):
        start_time = datetime.now()
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return
        dashboard_messages: list[PartialMessage] = self.bot.get_cog(
            "DashboardCog"
        ).messages
        announcement_channels: list = self.bot.get_cog("AnnouncementsCog").channels
        patch_channels: list = self.bot.get_cog("AnnouncementsCog").patch_channels
        map_messages: list[PartialMessage] = self.bot.get_cog("MapCog").messages
        war_updates_channels: list = self.bot.get_cog("WarUpdatesCog").channels
        guilds_done = 0
        for guild in guilds:
            guilds_done += 1
            if guild[1] != 0:
                try:
                    dashboard_channel = self.bot.get_channel(
                        guild[1]
                    ) or await self.bot.fetch_channel(guild[1])
                    dashboard_message = dashboard_channel.get_partial_message(guild[2])
                    dashboard_messages.append(dashboard_message)
                except:
                    pass
            if guild[3] != 0:
                try:
                    announcement_channel = self.bot.get_channel(
                        guild[3]
                    ) or await self.bot.fetch_channel(guild[3])
                    announcement_channels.append(announcement_channel)
                    war_updates_channels.append(announcement_channel)
                    if guild[4] != False:
                        patch_channels.append(announcement_channel)
                except:
                    pass
            if guild[6] != 0:
                if guild[6] == guild[1] and guild[1] != 0:
                    try:
                        map_channel = dashboard_channel
                    except:
                        pass
                else:
                    try:
                        map_channel = self.bot.get_channel(
                            guild[6]
                        ) or await self.bot.fetch_channel(guild[6])
                    except:
                        pass
                try:
                    map_message = map_channel.get_partial_message(guild[7])
                    map_messages.append(map_message)
                except:
                    pass
        logger.info(
            (
                f"message_gen finished going through {guilds_done} guilds in {(datetime.now() - start_time).total_seconds():.2} seconds. "
                f"Dashboards: {len(dashboard_messages)}. "
                f"Announcement channels: {len(announcement_channels)}. "
                f"Patch channels: {len(patch_channels)}. "
                f"Maps: {len(map_messages)}. "
            )
        )

    @message_gen.before_loop
    async def before_bot_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(ListGenCog(bot))
