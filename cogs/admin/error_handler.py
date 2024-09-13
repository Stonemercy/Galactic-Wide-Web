from datetime import datetime
from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot


class ErrorHandlerCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: AppCmdInter, error):
        if hasattr(inter.application_command, "on_error"):
            return
        if isinstance(error, commands.CheckFailure):
            now = datetime.now()
            if now < self.bot.ready_time:
                return await inter.send(
                    (
                        f"Please wait {int((self.bot.ready_time - now).total_seconds())} seconds to use this.\n"
                        f"Ready <t:{int(self.bot.ready_time.timestamp())}:R>"
                    ),
                    ephemeral=True,
                    delete_after=int((self.bot.ready_time - now).total_seconds()),
                )
            else:
                return await inter.send(
                    f"You need to be the owner of {inter.guild.me.mention} to use this command.",
                    ephemeral=True,
                )
        else:
            await self.bot.moderator_channel.send(error)
            raise error


def setup(bot: GalacticWideWebBot):
    bot.add_cog(ErrorHandlerCog(bot))
