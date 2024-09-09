from asyncio import sleep
from cogs.stats import DashboardStats
from datetime import datetime, time
from disnake import (
    Forbidden,
    NotFound,
    PartialMessage,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds import Dashboard
from utils.db import GuildRecord, GuildsDB
from utils.api import API, Data


class DashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.liberation_changes = {}
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

    times = []
    for i in range(24):
        for j in range(0, 60, 15):
            times.append(time(hour=i, minute=j, second=0))

    @wait_for_startup()
    @tasks.loop(time=times)
    async def dashboard(self, force: bool = False):
        if self.bot.dashboard_messages == []:
            return
        update_start = datetime.now()
        api = API()
        await api.pull_from_api(
            get_campaigns=True,
            get_assignments=True,
            get_planet_events=True,
            get_planets=True,
        )
        if api.error:
            return await self.bot.moderator_channel.send(
                f"<@164862382185644032>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        data = Data(data_from_api=api)
        for campaign in data.campaigns:
            liberation = (
                1 - (campaign.planet.health / campaign.planet.max_health)
                if not campaign.planet.event
                else 1
                - (campaign.planet.event.health / campaign.planet.event.max_health)
            )
            if campaign.planet.name not in self.liberation_changes:
                self.liberation_changes[campaign.planet.name] = {
                    "liberation": liberation,
                    "liberation_change": [],
                }
            else:
                if (
                    len(
                        self.liberation_changes[campaign.planet.name][
                            "liberation_change"
                        ]
                    )
                    == 4
                ):
                    self.liberation_changes[campaign.planet.name][
                        "liberation_change"
                    ].pop(0)
                while (
                    len(
                        self.liberation_changes[campaign.planet.name][
                            "liberation_change"
                        ]
                    )
                    < 4
                ):
                    self.liberation_changes[campaign.planet.name][
                        "liberation_change"
                    ].append(
                        liberation
                        - self.liberation_changes[campaign.planet.name]["liberation"]
                    )
            self.liberation_changes[campaign.planet.name]["liberation"] = liberation
        languages = GuildsDB.get_used_languages()
        dashboard_dict = {
            lang: Dashboard(data, lang, self.liberation_changes) for lang in languages
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
            await sleep(1.05)
        if not force:
            self.bot.logger.info(
                f"Updated {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
            )
        dashboard_stats: DashboardStats = self.bot.get_cog("StatsCog").dashboard_stats
        dashboard_stats.new_count(dashboards_updated)
        dashboard_stats.new_time((datetime.now() - update_start).total_seconds())
        return dashboards_updated

    @dashboard.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DashboardCog(bot))
