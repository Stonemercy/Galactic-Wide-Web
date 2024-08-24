from datetime import datetime
from disnake import AppCmdInter, Embed
from disnake.ext import commands
from main import GalacticWideWebBot


class DashboardStats:
    def __init__(self):
        self.total_updated = 0
        self.dashboards_updated_last_hour = []
        self.dashboards_update_time_last_hour = []

    def new_count(self, amount: int):
        if len(self.dashboards_updated_last_hour) == 4:
            self.dashboards_updated_last_hour.pop(0)
        self.dashboards_updated_last_hour.append(amount)
        self.total_updated += amount

    def new_time(self, time: float):
        if len(self.dashboards_update_time_last_hour) == 4:
            self.dashboards_update_time_last_hour.pop(0)
        self.dashboards_update_time_last_hour.append(time)

    def total_time(self):
        return sum(self.dashboards_update_time_last_hour)

    def total_sum(self):
        return sum(self.dashboards_updated_last_hour)

    def time_per_dash(self):
        time_to_update, total_updated = self.total_time(), self.total_sum()
        return (
            time_to_update / total_updated
            if 0 not in (time_to_update, total_updated)
            else 0
        )


class StatsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.maps_updated = 0
        self.announcements_sent = 0
        self.dashboard_stats = DashboardStats()

    @commands.slash_command(
        description="Returns information on the bot.",
    )
    async def stats(
        self,
        inter: AppCmdInter,
    ):
        self.bot.logger.info(f"StatsCog, stats command used")
        await inter.response.defer(ephemeral=True)
        embed = Embed(title="Bot stats")
        embed.add_field(
            "Uptime:",
            (
                f"Live since <t:{int(self.bot.startup_time.timestamp())}:d> at <t:{int(self.bot.startup_time.timestamp())}:t>\n"
                f"-# <t:{int(self.bot.startup_time.timestamp())}:R>"
            ),
            inline=False,
        )
        embed.add_field(
            "Dashboards:",
            (
                f"**{self.dashboard_stats.total_updated}** dashboards updated this boot\n\n"
                "In the last hour:\n"
                f"**{self.dashboard_stats.total_sum()}** dashboards updated\n"
                f"Taking **{self.dashboard_stats.total_time():.2f}** seconds\n"
                f"That's **{self.dashboard_stats.time_per_dash():.2f}s** per dashboard\n"
            ),
            inline=False,
        )
        embed.add_field("Maps updated:", f"{self.maps_updated}", inline=False)
        embed.add_field(
            "Announcements sent:", f"{self.announcements_sent}", inline=False
        )
        await inter.send(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(StatsCog(bot))
