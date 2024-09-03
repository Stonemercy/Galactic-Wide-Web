from datetime import datetime
from disnake.ext import commands, tasks
from utils.db import Guilds
from main import GalacticWideWebBot


class ListGenCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.list_gen.start()

    @tasks.loop(count=1)
    async def list_gen(self):
        start_time = datetime.now()
        for data_list in (
            self.bot.dashboard_messages,
            self.bot.dashboard_channels,
            self.bot.announcement_channels,
            self.bot.patch_channels,
            self.bot.map_messages,
            self.bot.map_channels,
        ):
            data_list.clear()
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return self.bot.logger.error(f"ListGenCog, list_gen, guilds == False")
        guilds_done = 0
        for guild in guilds:
            if guild[1] != 0:
                try:
                    dashboard_channel = self.bot.get_channel(
                        guild[1]
                    ) or await self.bot.fetch_channel(guild[1])
                    dashboard_message = dashboard_channel.get_partial_message(guild[2])
                    self.bot.dashboard_messages.append(dashboard_message)
                except:
                    pass
            if guild[3] != 0:
                try:
                    announcement_channel = self.bot.get_channel(
                        guild[3]
                    ) or await self.bot.fetch_channel(guild[3])
                    self.bot.announcement_channels.append(announcement_channel)
                    if guild[4] != False:
                        self.bot.patch_channels.append(announcement_channel)
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
                    self.bot.map_messages.append(map_message)
                except:
                    pass
            guilds_done += 1
        self.bot.logger.info(
            (
                f"\nmessage_gen finished going through {guilds_done} guilds in {(datetime.now() - start_time).total_seconds():.2f} seconds.\n"
                f"Dashboards: {len(self.bot.dashboard_messages)}.\n"
                f"Announcement channels: {len(self.bot.announcement_channels)}.\n"
                f"Patch channels: {len(self.bot.patch_channels)}.\n"
                f"Maps: {len(self.bot.map_messages)}."
            )
        )

    @list_gen.before_loop
    async def before_message_gen(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(ListGenCog(bot))
