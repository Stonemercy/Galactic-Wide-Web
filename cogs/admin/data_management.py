from datetime import datetime, time
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.db import GWWGuild


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.channel_message_gen.start()
        self.pull_from_api.start()

    def cog_unload(self):
        self.channel_message_gen.stop()
        self.pull_from_api.stop()

    @tasks.loop(count=1)
    async def channel_message_gen(self):
        start_time = datetime.now()
        for data_list in (
            self.bot.dashboard_messages,
            self.bot.announcement_channels,
            self.bot.patch_channels,
            self.bot.map_messages,
            self.bot.major_order_channels,
        ):
            data_list.clear()
        guilds: list[GWWGuild] = GWWGuild.get_all()
        if not guilds:
            return self.bot.logger.error(
                f"{self.qualified_name} | list_gen | {guilds = }"
            )
        guilds_done = 0
        for guild in guilds:
            if guild.dashboard_channel_id != 0:
                try:
                    dashboard_channel = self.bot.get_channel(
                        guild.dashboard_channel_id
                    ) or await self.bot.fetch_channel(guild.dashboard_channel_id)
                    dashboard_message = dashboard_channel.get_partial_message(
                        guild.dashboard_message_id
                    )
                    self.bot.dashboard_messages.append(dashboard_message)
                except:
                    pass
            if guild.announcement_channel_id != 0:
                try:
                    announcement_channel = self.bot.get_channel(
                        guild.announcement_channel_id
                    ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                    self.bot.announcement_channels.append(announcement_channel)
                    if guild.patch_notes:
                        self.bot.patch_channels.append(announcement_channel)
                    if guild.major_order_updates:
                        self.bot.major_order_channels.append(announcement_channel)
                except:
                    pass
            if guild.map_channel_id != 0:
                if guild.map_channel_id == guild.dashboard_channel_id:
                    map_channel = dashboard_channel
                else:
                    try:
                        map_channel = self.bot.get_channel(
                            guild.map_channel_id
                        ) or await self.bot.fetch_channel(guild.map_channel_id)
                    except:
                        pass
                try:
                    map_message = map_channel.get_partial_message(guild.map_message_id)
                    self.bot.map_messages.append(map_message)
                except:
                    pass
            guilds_done += 1
        self.bot.logger.info(
            (
                f"message_gen completed | "
                f"{guilds_done} guilds in {(datetime.now() - start_time).total_seconds():.2f} seconds | "
                f"{len(self.bot.dashboard_messages)} dashboards ({(len(self.bot.dashboard_messages) / guilds_done):.0%}) | "
                f"{len(self.bot.announcement_channels)} announcement channels ({(len(self.bot.announcement_channels) / guilds_done):.0%}) | "
                f"{len(self.bot.patch_channels)} patch channels ({(len(self.bot.patch_channels) / guilds_done):.0%}) | "
                f"{len(self.bot.map_messages)} maps ({(len(self.bot.map_messages) / guilds_done):.0%}) | "
                f"{len(self.bot.major_order_channels)} MO channels ({(len(self.bot.major_order_channels) / guilds_done):.0%})"
            )
        )
        self.bot.c_n_m_loaded = True
        await self.pull_from_api()

    @channel_message_gen.before_loop
    async def before_message_gen(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=j, minute=i, second=45) for j in range(24) for i in range(59)]
    )
    async def pull_from_api(self):
        await self.bot.data.pull_from_api(self.bot)

    @pull_from_api.before_loop
    async def before_pull_from_api(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
