from asyncio import sleep
from datetime import datetime
from logging import getLogger
from os import getenv
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import AnnouncementEmbed, Dashboard
from helpers.functions import dashboard_maps, pull_from_api

logger = getLogger("disnake")


class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.faction_colour = {
            "Automaton": (252, 76, 79),
            "automaton": (126, 38, 22),
            "Terminids": (253, 165, 58),
            "terminids": (126, 82, 29),
            "Illuminate": (116, 163, 180),
            "illuminate": (58, 81, 90),
            "Humans": (36, 205, 76),
            "humans": (18, 102, 38),
        }

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def force_update_dashboard(self, inter: AppCmdInter):
        logger.critical(
            f"AdminCommandsCog, force_update_dashboard command used by {inter.author.id} - {inter.author.name}"
        )
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        data = await pull_from_api(
            get_campaigns=True,
            get_assignments=True,
            get_planet_events=True,
            get_planets=True,
            get_war_state=True,
        )
        for data_key, data_value in data.items():
            if data_value == None and data_key != "planet_events":
                logger.error(
                    f"AdminCommandsCog, force_update_dashboard, {data_key} has returned {data_value}"
                )
                return await inter.send(f"{data_key} return None", ephemeral=True)
        languages = Guilds.get_used_languages()
        dashboard_dict = {}
        for lang in languages:
            dashboard = Dashboard(data, lang)
            dashboard_dict[lang] = dashboard
        chunked_messages = [
            self.bot.get_cog("DashboardCog").messages[i : i + 50]
            for i in range(0, len(self.bot.get_cog("DashboardCog").messages), 50)
        ]
        update_start = datetime.now()
        dashboards_updated = 0
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(
                    self.bot.get_cog("DashboardCog").update_message(
                        message, dashboard_dict
                    )
                )
                dashboards_updated += 1
            await sleep(1.025)
        logger.info(
            f"Forced updates of {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )
        await inter.send(
            f"Attempted to update {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def force_update_maps(self, inter: AppCmdInter):
        logger.critical(
            f"AdminCommandsCog, force_update_maps command used by {inter.author.id} - {inter.author.name}"
        )
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        maps_updated = 0
        data = await pull_from_api(
            get_campaigns=True,
            get_planets=True,
        )
        for data_key, data_value in data.items():
            if data_value == None:
                logger.error(
                    f"AdminCommandsCog, force_update_maps, {data_key} has returned {data_value}"
                )
                return await inter.send(f"{data_key} return None", ephemeral=True)
        channel = self.bot.get_channel(1242843098363596883)
        map_embeds = await dashboard_maps(data, channel)
        messages = self.bot.get_cog("MapCog").messages
        chunked_messages = [messages[i : i + 50] for i in range(0, len(messages), 50)]
        update_start = datetime.now()
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(
                    self.bot.get_cog("MapCog").update_message(message, map_embeds)
                )
                maps_updated += 1
            await sleep(1.025)
        logger.info(
            f"Forced updates of {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )
        await inter.send(
            f"Attempted to update {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def send_announcement(self, inter: AppCmdInter):
        logger.critical(
            f"AdminCommandsCog, send_announcement command used by {inter.author.id} - {inter.author.name}"
        )
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        embeds = {}
        languages = Guilds.get_used_languages()
        for lang in languages:
            embeds[lang] = AnnouncementEmbed()
        update_start = datetime.now()
        channels = self.bot.get_cog("AnnouncementsCog").channels
        chunked_channels = [channels[i : i + 50] for i in range(0, len(channels), 50)]
        for chunk in chunked_channels:
            for channel in chunk:
                self.bot.loop.create_task(
                    self.bot.get_cog("AnnouncementsCog").send_embed(
                        channel, embeds, "Announcement"
                    )
                )
            await sleep(1.025)
        await inter.send(
            f"Attempted to send out an announcement to {len(self.bot.get_cog('AnnouncementsCog').channels)} channels in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
            delete_after=5,
        )


def setup(bot: commands.Bot):
    bot.add_cog(AdminCommandsCog(bot))
