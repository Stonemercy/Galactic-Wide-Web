from asyncio import sleep
from datetime import datetime, time
from disnake import (
    Forbidden,
    NotFound,
    PartialMessage,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.embeds import Dashboard
from utils.db import GuildRecord, GuildsDB


class DashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.dashboard.start()

    def cog_unload(self):
        self.dashboard.stop()

    async def update_message(self, message: PartialMessage, dashboard_dict: dict):
        guild: GuildRecord = GuildsDB.get_info(message.guild.id)
        if not guild:
            self.bot.dashboard_messages.remove(message)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {guild = } | {message.guild.id = }"
            )
        try:
            await message.edit(embeds=dashboard_dict[guild.language].embeds)
        except (NotFound, Forbidden) as e:
            self.bot.dashboard_messages.remove(message)
            GuildsDB.update_dashboard(message.guild.id, 0, 0)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {e} | removed from self.bot.dashboard_messages | {message.channel.id = }"
            )
        except Exception as e:
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {e} | {message.channel.id = }"
            )

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(0, 60, 15)
        ]
    )
    async def dashboard(self):
        if (
            self.bot.dashboard_messages == []
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        update_start = datetime.now()
        languages = GuildsDB.get_used_languages()
        dashboard_dict = {
            lang: Dashboard(
                data=self.bot.data,
                language=self.bot.json_dict["languages"][lang],
                json_dict=self.bot.json_dict,
            )
            for lang in languages
        }
        chunked_messages = [
            self.bot.dashboard_messages[i : i + 50]
            for i in range(0, len(self.bot.dashboard_messages), 50)
        ]
        dashboards_updated = 0
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(self.update_message(message, dashboard_dict))
                dashboards_updated += 1
            await sleep(1.1)
        self.bot.logger.info(
            f"Updated {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )
        return dashboards_updated

    @dashboard.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DashboardCog(bot))
