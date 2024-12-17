from asyncio import sleep
from datetime import datetime, time
from disnake import PartialMessage
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.embeds import Dashboard
from utils.db import GWWGuild


class DashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.dashboard.start()

    def cog_unload(self):
        self.dashboard.stop()

    async def update_message(self, message: PartialMessage, dashboard_dict: dict):
        guild = GWWGuild.get_by_id(message.guild.id)
        if not guild and message in self.bot.dashboard_messages:
            self.bot.dashboard_messages.remove(message)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {guild = } | {message.guild.id = }"
            )
        try:
            await message.edit(embeds=dashboard_dict[guild.language].embeds)
        except Exception as e:
            if message in self.bot.dashboard_messages:
                self.bot.dashboard_messages.remove(message)
            guild.dashboard_channel_id = 0
            guild.dashboard_message_id = 0
            guild.save_changes()
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {e} | removed from dashboard messages list | {message.channel.id = }"
            )

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(0, 60, 15)
        ]
    )
    async def dashboard(self):
        dashboards_start = datetime.now()
        if (
            not self.bot.dashboard_messages
            or dashboards_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        embeds = {
            lang: Dashboard(
                data=self.bot.data,
                language=self.bot.json_dict["languages"][lang],
                json_dict=self.bot.json_dict,
            )
            for lang in list({guild.language for guild in GWWGuild.get_all()})
        }
        dashboards_updated = 0
        for chunk in [
            self.bot.dashboard_messages[i : i + 50]
            for i in range(0, len(self.bot.dashboard_messages), 50)
        ]:
            for message in chunk:
                self.bot.loop.create_task(
                    self.update_message(
                        message,
                        embeds,
                    )
                )
                dashboards_updated += 1
            await sleep(1.5)
        self.bot.logger.info(
            f"Updated {dashboards_updated} dashboards in {(datetime.now() - dashboards_start).total_seconds():.2f} seconds"
        )
        return dashboards_updated

    @dashboard.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DashboardCog(bot))
