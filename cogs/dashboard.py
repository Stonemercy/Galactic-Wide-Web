from datetime import datetime, time
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.db import GWWGuild
from utils.embeds.dashboard import Dashboard


class DashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.dashboard_poster.start()

    def cog_unload(self):
        self.dashboard_poster.stop()

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(0, 60, 15)
        ]
    )
    async def dashboard_poster(self):
        dashboards_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or dashboards_start < self.bot.ready_time
        ):
            return
        dashboards = {
            lang: Dashboard(
                data=self.bot.data,
                language_code=lang,
                json_dict=self.bot.json_dict,
            )
            for lang in list({guild.language for guild in GWWGuild.get_all()})
        }
        for lang, dashboard in dashboards.items():
            if dashboard.character_count() > 6000:
                dashboard = Dashboard(
                    data=self.bot.data,
                    language_code=lang,
                    json_dict=self.bot.json_dict,
                    with_health_bars=False,
                )
        await self.bot.interface_handler.edit_dashboards(dashboards)
        self.bot.logger.info(
            f"Updated {len(self.bot.interface_handler.dashboards)} dashboards in {(datetime.now()-dashboards_start).total_seconds():.2f} seconds"
        )

    @dashboard_poster.before_loop
    async def before_dashboard_poster(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DashboardCog(bot))
