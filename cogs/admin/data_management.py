from asyncio import sleep
from datetime import datetime, time
from os import getenv
from aiohttp import ClientSession
from disnake.ext import commands, tasks
from utils.db import GuildsDB
from main import GalacticWideWebBot

api = getenv("API")
backup_api = getenv("BU_API")


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.channel_message_gen.start()
        self.pull_from_api.start()

    def cog_unload(self):
        self.pull_from_api.stop()

    @tasks.loop(count=1)
    async def channel_message_gen(self):
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
        guilds = GuildsDB.get_all_guilds()
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
                f"{len(self.bot.map_messages)} maps ({(len(self.bot.map_messages) / guilds_done):.0%})"
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
        start_time = datetime.now()
        api_to_use = api
        async with ClientSession(headers={"Accept-Language": "en-GB"}) as session:
            async with session.get(f"{api_to_use}") as r:
                if r.status != 200:
                    api_to_use = backup_api
                    self.bot.logger.critical("API/USING BACKUP")
                    await self.bot.moderator_channel.send(f"API/USING BACKUP\n{r}")

            async with session.get(f"{api_to_use}") as r:
                if r.status != 200:
                    self.bot.logger.critical("API/BACKUP FAILED")
                    return await self.bot.moderator_channel.send(
                        f"API/BACKUP FAILED\n{r}"
                    )

                for endpoint in list(self.bot.data_dict.keys()):
                    if endpoint == "thumbnails":
                        async with session.get(
                            "https://helldivers.news/api/planets"
                        ) as r:
                            if r.status == 200:
                                self.bot.data_dict["thumbnails"] = await r.json()
                            else:
                                self.bot.logger.error(f"API/THUMBNAILS, {r.status}")
                        continue
                    try:
                        async with session.get(f"{api_to_use}/api/v1/{endpoint}") as r:
                            if r.status == 200:
                                if endpoint == "dispatches":
                                    json = await r.json()
                                    if not json[0]["message"]:
                                        continue
                                self.bot.data_dict[endpoint] = await r.json()
                            else:
                                self.bot.logger.error(
                                    f"API/{endpoint.upper()}, {r.status}"
                                )
                                await self.bot.moderator_channel.send(
                                    f"API/{endpoint.upper()}\n{r}"
                                )
                            await sleep(2)
                    except Exception as e:
                        self.bot.logger.error(f"API/{endpoint.upper()}, {e}")
                        await self.bot.moderator_channel.send(
                            f"API/{endpoint.upper()}\n{r}"
                        )
        self.bot.logger.info(
            (
                f"pull_from_api complete | "
                f"Completed in {(datetime.now() - start_time).total_seconds():.2f} seconds | "
                f"{len(self.bot.data_dict['assignments']) = } | "
                f"{len(self.bot.data_dict['campaigns']) = } | "
                f"{len(self.bot.data_dict['dispatches']) = } | "
                f"{len(self.bot.data_dict['planets']) = } | "
                f"{len(self.bot.data_dict['steam']) = } | "
                f"{len(self.bot.data_dict['thumbnails']) = } | "
            )
        )
        if not self.bot.data_loaded:
            now = datetime.now()
            if now < self.bot.ready_time:
                self.bot.logger.info(
                    f"setup complete | self.bot.ready_time: {self.bot.ready_time.strftime('%H:%M:%S')} -> {now.strftime('%H:%M:%S')}"
                )
                self.bot.ready_time = now
            self.bot.data_loaded = True

    @pull_from_api.before_loop
    async def before_pull_from_api(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
