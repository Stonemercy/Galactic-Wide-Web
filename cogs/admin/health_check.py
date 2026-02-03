from datetime import datetime, timedelta
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.dataclasses import Config
from utils.dbv2 import Feature, GWWGuild, GWWGuilds


class HealthCheckCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        if not self.health_check.is_running():
            self.health_check.start()
            self.bot.loops.append(self.health_check)

    def cog_unload(self) -> None:
        if self.health_check.is_running():
            self.health_check.cancel()
        if self.health_check in self.bot.loops:
            self.bot.loops.remove(self.health_check)

    @tasks.loop(minutes=1)
    async def health_check(self) -> None:
        now = datetime.now()
        guild: GWWGuild | None = GWWGuilds.get_specific_guild(
            id=Config.SUPPORT_SERVER_ID
        )
        if guild:
            try:
                dashboard_list: list[Feature] = [
                    f for f in guild.features if f.name == "dashboards"
                ]
                if dashboard_list == []:
                    self.bot.logger.warning(
                        f"{self.qualified_name} | dashboard_checking | No dashboard feature found for {guild.guild_id} (support server)"
                    )
                    return
                else:
                    dashboard: Feature = dashboard_list[0]
                    channel = self.bot.get_channel(
                        dashboard.channel_id
                    ) or await self.bot.fetch_channel(dashboard.channel_id)
                    message = await channel.fetch_message(dashboard.message_id)
                    cutoff = now - timedelta(minutes=17)
                    if (
                        message.edited_at.replace(tzinfo=None) < cutoff
                        and self.bot.startup_time < cutoff
                    ):
                        await self.bot.channels.moderator_channel.send(
                            content=f"<@{self.bot.owner.id}> {message.jump_url} was last edited <t:{int(message.edited_at.timestamp())}:R> :warning:"
                        )
            except Exception as e:
                self.bot.logger.error(
                    f"{self.qualified_name} | dashboard_checking | {e}"
                )
        if self.bot.data.formatted_data:
            if self.bot.data.formatted_data.formatted_at < now - timedelta(minutes=5):
                await self.bot.channels.moderator_channel.send(
                    content=f"<@{self.bot.owner.id}> Data was last formatted <t:{int(self.bot.data.formatted_data.formatted_at.timestamp())}:R> :warning:"
                )
        else:
            if self.bot.ready_time < now:
                await self.bot.channels.moderator_channel.send(
                    content=f"<@{self.bot.owner.id}> Data has **not** been formatted yet :warning:"
                )

    @health_check.before_loop
    async def before_dashboard_check(self) -> None:
        await self.bot.wait_until_ready()

    @health_check.error
    async def health_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "health_check loop")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(HealthCheckCog(bot))
