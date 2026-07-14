from aiohttp import ServerDisconnectedError
from disnake import AppCmdInter, ChannelType, Color, Embed, MessageInteraction, NotFound
from disnake.ext.commands import (
    BadArgument,
    BotMissingPermissions,
    CheckFailure,
    Cog,
    MissingPermissions,
    MissingRequiredArgument,
    NoPrivateMessage,
    PrivateMessageOnly,
)
from traceback import format_exception
from utils.bot import GalacticWideWebBot
from utils.errors import NotReadyYet, NotWhitelisted


class ErrorHandlerCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_slash_command_error(self, inter: AppCmdInter, error):
        error = getattr(error, "original", error)
        embed = Embed(title="Error", color=Color.red())
        log_error = True

        if isinstance(error, NotReadyYet):
            embed.description = f"The bot isn't ready yet, try again <t:{int(self.bot.ready_time.timestamp())}:R>"
            log_error = False
        elif isinstance(error, NotWhitelisted):
            embed.description = (
                f"This command isn't for public use. Apologies for the inconvenience."
            )
            log_error = False
        elif isinstance(error, MissingPermissions):
            embed.description = f"You don't have permission to use this command.\nRequired: {', '.join(error.missing_permissions)}"
        elif isinstance(error, BotMissingPermissions):
            embed.description = f"I don't have the required permissions.\nMissing: {', '.join(error.missing_permissions)}"
        elif isinstance(error, MissingRequiredArgument):
            embed.description = f"Missing required argument: `{error.param.name}`"
        elif isinstance(error, BadArgument):
            embed.description = f"Invalid argument provided: {str(error)}"
        elif isinstance(error, CheckFailure):
            embed.description = "You don't have permission to use this command."
        elif isinstance(error, NoPrivateMessage):
            embed.description = "This command cannot be used in DMs."
            log_error = False
        elif isinstance(error, PrivateMessageOnly):
            embed.description = "This command can only be used in DMs."
            log_error = False
        elif isinstance(error, NotFound):
            embed.description = "There was an error with Discord for this interaction. Please try again."
            log_error = False
        elif isinstance(error, ServerDisconnectedError):
            embed.description = "There was an error with Discord's server for this interaction. Please try again."
            log_error = False
        else:
            embed.description = (
                "An unexpected error occurred. The developers have been notified."
            )

        if log_error:
            await self.log_error(inter, error, "Slash Command")

        try:
            if inter.response.is_done():
                await inter.followup.send(embed=embed, ephemeral=True)
            else:
                await inter.response.send_message(embed=embed, ephemeral=True)
        except:
            pass

        self.bot.logger.error(
            f"{inter.author.name} | /{inter.application_command.qualified_name} | {error}"
        )

    async def log_error(
        self,
        inter: MessageInteraction | AppCmdInter | None,
        error: Exception,
        error_type="Unknown",
    ):
        embed = Embed(title=f"{error_type} error", color=Color.dark_red())
        if inter and inter.application_command:
            embed.title += f" - /{inter.application_command.name}"
        if hasattr(inter, "guild") and inter.guild:
            embed.add_field(
                name="Guild",
                value=f"-# {inter.guild.name} - {inter.guild.approximate_member_count}\n-# {inter.guild.id}",
            )
        if hasattr(inter, "author"):
            embed.add_field(
                name="User",
                value=f"-# {inter.author}\n-# {inter.author.id}\n-# {inter.author.mention}",
            )
        elif hasattr(inter, "user"):
            embed.add_field(
                name="User",
                value=f"-# {inter.user}\n-# {inter.user.id}\n-# {inter.user.mention}",
            )
        if hasattr(inter, "channel"):
            channel_name = (
                "DMs"
                if inter.channel.type == ChannelType.private
                else inter.channel.name
            )
            embed.add_field(
                name="Channel",
                value=f"-# {channel_name}\n-# {inter.channel.mention if hasattr(inter.channel, 'mention') else 'DM'}",
                inline=False,
            )

        error_text = "".join(format_exception(type(error), error, error.__traceback__))

        if len(error_text) > 1024:
            embed.add_field(
                name="Error",
                value=f"```py\n{error_text[-1010:]}\n```",
                inline=False,
            )
        else:
            embed.add_field(
                name="Error", value=f"```py\n{error_text}\n```", inline=False
            )

        await self.bot.channels.moderator_channel.send(
            content=self.bot.owner.mention, embed=embed
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(ErrorHandlerCog(bot))
