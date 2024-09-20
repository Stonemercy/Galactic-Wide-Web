from datetime import datetime
from json import load
from disnake.ext import commands, tasks
from utils.db import GuildsDB
from main import GalacticWideWebBot
from data.lists import json_dict


class ListGenCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.list_gen.start()
        self.load_json.start()

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
        self.bot.ready_time = datetime.now()

    @list_gen.before_loop
    async def before_message_gen(self):
        await self.bot.wait_until_ready()

    @tasks.loop(count=1)
    async def load_json(self):
        self.bot.json_dict = json_dict.copy()
        json_load_start = datetime.now()
        status = "load_json status:\n"
        for key, values in json_dict.copy().items():
            if "path" not in values:
                for second_key, second_values in values.items():
                    if "path" in second_values:
                        with open(second_values["path"], encoding="UTF-8") as json_file:
                            self.bot.json_dict[key][second_key] = load(json_file)
                            status += f"{key} - {second_key} - {'LOADED' if second_values else 'FAILED'}\n"
                            continue
                continue
            else:
                with open(values["path"], encoding="UTF-8") as json_file:
                    self.bot.json_dict[key] = load(json_file)
                    status += f"{key} - {'LOADED' if values else 'FAILED'}\n"
        if "FAILED" in status:
            return await self.bot.moderator_channel.send(
                f"<@{self.bot.owner_id}>\n{status}"
            )
        self.bot.logger.info(
            f"json loaded in {(datetime.now() - json_load_start).total_seconds():.5f} seconds"
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(ListGenCog(bot))
