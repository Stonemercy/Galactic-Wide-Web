from datetime import datetime, time
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.dbv2 import GWWGuilds
from utils.embeds import Dashboard


class DashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        if not self.dashboard_poster.is_running():
            self.dashboard_poster.start()
            self.bot.loops.append(self.dashboard_poster)

    def cog_unload(self) -> None:
        if self.dashboard_poster.is_running():
            self.dashboard_poster.cancel()
        if self.dashboard_poster in self.bot.loops:
            self.bot.loops.remove(self.dashboard_poster)

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(0, 60, 15)
        ]
    )
    async def dashboard_poster(self) -> None:
        dashboards_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or dashboards_start < self.bot.ready_time
        ):
            return
        unique_langs = GWWGuilds.unique_languages()
        dashboards = {
            lang: Dashboard(
                data=self.bot.data.formatted_data,
                language_code=lang,
                json_dict=self.bot.json_dict,
            )
            for lang in unique_langs
        }
        for lang, dashboard in dashboards.copy().items():
            compact_level = 0
            while dashboard.character_count() > 6000 and compact_level < 2:
                compact_level += 1
                dashboards[lang] = Dashboard(
                    data=self.bot.data.formatted_data,
                    language_code=lang,
                    json_dict=self.bot.json_dict,
                    compact_level=compact_level,
                )
                dashboard = dashboards[lang]
        await self.bot.interface_handler.send_feature("dashboards", dashboards)
        self.bot.logger.info(
            f"Updated {len(self.bot.interface_handler.dashboards)} dashboards in {(datetime.now()-dashboards_start).total_seconds():.2f} seconds"
        )

    @dashboard_poster.before_loop
    async def before_dashboard_poster(self) -> None:
        await self.bot.wait_until_ready()

    @dashboard_poster.error
    async def dashboard_poster_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "dashboard_poster loop")


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(DashboardCog(bot))
