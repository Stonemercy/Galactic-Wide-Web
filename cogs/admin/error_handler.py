from traceback import format_exception
from disnake import AppCmdInter, Color, Embed, MessageInteraction
from disnake.ext import commands
from utils.bot import GalacticWideWebBot


class ErrorHandlerCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: AppCmdInter, error):
        error = getattr(error, "original", error)
        embed = Embed(title="Error", color=Color.red())

        if isinstance(error, commands.MissingPermissions):
            embed.description = f"You don't have permission to use this command.\nRequired: {', '.join(error.missing_permissions)}"
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = f"I don't have the required permissions.\nMissing: {', '.join(error.missing_permissions)}"
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Missing required argument: `{error.param.name}`"
        elif isinstance(error, commands.BadArgument):
            embed.description = f"Invalid argument provided: {str(error)}"
        elif isinstance(error, commands.CheckFailure):
            embed.description = "You don't have permission to use this command."
        elif isinstance(error, commands.NoPrivateMessage):
            embed.description = "This command cannot be used in DMs."
        elif isinstance(error, commands.PrivateMessageOnly):
            embed.description = "This command can only be used in DMs."
        else:
            embed.description = (
                "An unexpected error occurred. The developers have been notified."
            )
            await self.log_error(inter, error, "Slash Command")

        try:
            if inter.response.is_done():
                await inter.followup.send(embed=embed, ephemeral=True)
            else:
                await inter.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

    @commands.Cog.listener()
    async def on_button_click_error(self, inter: MessageInteraction, error):
        error = getattr(error, "original", error)
        embed = Embed(title="Button Error", color=Color.red())

        if isinstance(error, commands.CheckFailure):
            embed.description = "You don't have permission to use this button."
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"This button is on cooldown. Try again in {error.retry_after:.2f} seconds."
        else:
            embed.description = "An error occurred while processing your button click."
            await self.log_error(inter, error, "Button Click")

        try:
            if inter.response.is_done():
                await inter.followup.send(embed=embed, ephemeral=True)
            else:
                await inter.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

    @commands.Cog.listener()
    async def on_dropdown_error(self, inter: MessageInteraction, error):
        error = getattr(error, "original", error)
        embed = Embed(title="Dropdown Error", color=Color.red())

        if isinstance(error, commands.CheckFailure):
            embed.description = "You don't have permission to use this dropdown."
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"This dropdown is on cooldown. Try again in {error.retry_after:.2f} seconds."
        else:
            embed.description = "An error occurred while processing your selection."
            await self.log_error(inter, error, "Dropdown")

        try:
            if inter.response.is_done():
                await inter.followup.send(embed=embed, ephemeral=True)
            else:
                await inter.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

    async def log_error(
        self,
        inter: MessageInteraction | AppCmdInter | None,
        error: Exception,
        error_type="Unknown",
    ):
        embed = Embed(title=f"{error_type} error", color=Color.dark_red())
        if hasattr(inter, "guild") and inter.guild:
            embed.add_field(
                name="Guild", value=f"{inter.guild.name} ({inter.guild.id})"
            )
        if hasattr(inter, "author"):
            embed.add_field(
                name="User",
                value=f"{inter.author} ({inter.author.id}) {inter.author.mention}",
            )
        elif hasattr(inter, "user"):
            embed.add_field(
                name="User",
                value=f"{inter.user} ({inter.user.id}) {inter.user.mention}",
            )
        if hasattr(inter, "channel"):
            embed.add_field(
                name="Channel", value=f"{inter.channel.name} {inter.channel.mention}"
            )

        error_text = "".join(format_exception(type(error), error, error.__traceback__))

        if len(error_text) > 1024:
            embed.add_field(
                name="Error",
                value="..." + error_text[-1024:],
                inline=False,
            )
        else:
            embed.add_field(
                name="Error", value=f"```py\n{error_text}\n```", inline=False
            )

        await self.bot.channels.moderator_channel.send(embed=embed)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(ErrorHandlerCog(bot))
