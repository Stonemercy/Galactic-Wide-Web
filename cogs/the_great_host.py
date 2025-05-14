from disnake import AppCmdInter, InteractionTimedOut, NotFound
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.dashboard import Dashboard


class TheGreatHostCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Check status of The Great Host",
    )
    async def the_great_host(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ):
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuild.new(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        await inter.send(
            embed=Dashboard.TheGreatHostEmbed(
                the_great_host_resource=self.bot.data.global_resources.the_great_host,
                the_great_host_changes=self.bot.data.the_great_host_changes,
                language_json=guild_language,
            ),
            ephemeral=public != "Yes",
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(TheGreatHostCog(bot))
