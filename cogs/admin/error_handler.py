from datetime import timedelta
from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from sys import exc_info
from traceback import format_exception


class ErrorHandlerCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_slash_command_error(
        self, inter: AppCmdInter, error: commands.CommandError
    ):
        if hasattr(inter.application_command, "on_error"):
            return
        elif isinstance(error, commands.NotOwner):
            await inter.send(
                content=f"You are not allowed to use this command.",
                ephemeral=True,
            )
            return
        elif isinstance(error, commands.CheckFailure):
            if (
                inter.created_at.replace(tzinfo=None) + timedelta(hours=1)
                < self.bot.ready_time
            ):
                await inter.send(
                    content=(
                        f"Please wait {self.bot.time_until_ready} seconds to use this.\n"
                        f"Ready <t:{int(self.bot.ready_time.timestamp())}:R>"
                    ),
                    ephemeral=True,
                    delete_after=self.bot.time_until_ready,
                )
                return
            else:
                await inter.send(error, ephemeral=True)
        else:
            try:
                await inter.send(
                    content="There was an unexpected error. Please try again.",
                    ephemeral=True,
                )
                await self.bot.moderator_channel.send(
                    content=f"{self.bot.owner.mention}```py\n{''.join(format_exception(type(error), value=error, tb=error.__traceback__))[-1900:]}\n```"
                )
            except Exception as e:
                await self.bot.moderator_channel.send(
                    content=f"{self.bot.owner.mention}\n```\n{error}```\n```\n{e}```"
                )
                raise error

    @commands.Cog.listener()
    async def on_error(self, event_method: str, *args, **kwargs):
        exc_type, exc_value, exc_traceback = exc_info()
        await self.bot.moderator_channel.send(
            content=f"{self.bot.owner.mention}\nUnhandled Event Error\n```py\n{''.join(format_exception(exc_type, exc_value, exc_traceback))}```",
            event=event_method,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=ErrorHandlerCog(bot))
