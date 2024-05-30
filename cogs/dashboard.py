from asyncio import sleep
from logging import getLogger
from disnake import (
    Forbidden,
    NotFound,
    PartialMessage,
)
from disnake.ext import commands, tasks
from helpers.embeds import Dashboard
from helpers.db import Guilds
from datetime import datetime
from helpers.functions import pull_from_api

logger = getLogger("disnake")


class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.messages = []
        self.dashboard.start()

    def cog_unload(self):
        self.dashboard.stop()

    async def update_message(self, message: PartialMessage, dashboard_dict: dict):
        guild = Guilds.get_info(message.guild.id)
        if guild == None:
            self.messages.remove(message)
            return logger.error(
                f"DashboardCog, update_message, guild == None, {message.guild.id}"
            )
        try:
            await message.edit(embeds=dashboard_dict[guild[5]].embeds)
        except NotFound:
            self.messages.remove(message)
            Guilds.update_dashboard(message.guild.id, 0, 0)
            return logger.error(
                f"DashboardCog, update_message, NotFound, removing from message list, {message.channel.id}"
            )
        except Forbidden:
            self.messages.remove(message)
            Guilds.update_dashboard(message.guild.id, 0, 0)
            return logger.error(
                f"DashboardCog, update_message, Forbidden, removing from message list, {message.channel.id}"
            )
        except Exception as e:
            return logger.error(
                f"DashboardCog, update_message, {e}, {message.channel.id}"
            )

    @tasks.loop(minutes=1)
    async def dashboard(self):
        now = datetime.now()
        if now.minute not in (0, 15, 30, 45) or self.messages == []:
            return
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
                    f"DashboardCog, dashboard, {data_key} returned {data_value}"
                )
                return
        languages = Guilds.get_used_languages()
        dashboard_dict = {}
        for lang in languages:
            dashboard = Dashboard(data, lang)
            dashboard_dict[lang] = dashboard
        chunked_messages = [
            self.messages[i : i + 50] for i in range(0, len(self.messages), 50)
        ]
        update_start = datetime.now()
        dashboards_updated = 0
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(self.update_message(message, dashboard_dict))
                dashboards_updated += 1
            await sleep(1.025)
        logger.info(
            f"Updated {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )

    @dashboard.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(DashboardCog(bot))
