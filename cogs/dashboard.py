from asyncio import sleep
from cogs.stats import DashboardStats
from datetime import datetime, time, timedelta
from disnake import (
    Forbidden,
    NotFound,
    PartialMessage,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.embeds import Dashboard
from utils.db import GuildRecord, GuildsDB
from utils.data import Campaign, Data


class DashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.liberation_changes = {}
        self.dashboard.start()

    def cog_unload(self):
        self.dashboard.stop()

    def get_needed_players(self, campaign: Campaign):
        if campaign.planet.event:
            liberation_changes = self.liberation_changes[campaign.planet.name]
            if (
                len(liberation_changes["liberation_changes"]) == 0
                or sum(liberation_changes["liberation_changes"]) == 0
            ):
                return
            progress_needed = 100 - liberation_changes["liberation"]
            now = datetime.now()
            seconds_to_complete = int(
                (progress_needed / sum(liberation_changes["liberation_changes"])) * 3600
            )
            winning = (
                now + timedelta(seconds=seconds_to_complete)
                < campaign.planet.event.end_time_datetime
            )
            if not winning:
                hours_left = (
                    campaign.planet.event.end_time_datetime - now
                ).total_seconds() / 3600
                progress_needed_per_hour = progress_needed / hours_left
                amount_ratio = progress_needed_per_hour / sum(
                    liberation_changes["liberation_changes"]
                )
                required_players = campaign.planet.stats["playerCount"] * amount_ratio
                return required_players

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
    async def dashboard(self, force: bool = False):
        if self.bot.dashboard_messages == [] or None in self.bot.data_dict.values():
            return
        update_start = datetime.now()
        data = Data(data_from_api=self.bot.data_dict)
        planets_with_player_reqs = {}
        for campaign in data.campaigns:
            if campaign.planet.name not in self.liberation_changes:
                self.liberation_changes[campaign.planet.name] = {
                    "liberation": campaign.progress,
                    "liberation_changes": [],
                }
            else:
                changes = self.liberation_changes[campaign.planet.name]
                if len(changes["liberation_changes"]) == 4:
                    changes["liberation_changes"].pop(0)
                while len(changes["liberation_changes"]) < 4:
                    changes["liberation_changes"].append(
                        campaign.progress - changes["liberation"]
                    )
                changes["liberation"] = campaign.progress
            required = self.get_needed_players(campaign)
            if required:
                planets_with_player_reqs[campaign.planet.index] = required
        languages = GuildsDB.get_used_languages()
        dashboard_dict = {
            lang: Dashboard(
                data=data,
                language=self.bot.json_dict["languages"][lang],
                liberation_changes=self.liberation_changes,
                json_dict=self.bot.json_dict,
                planet_reqs=planets_with_player_reqs,
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
