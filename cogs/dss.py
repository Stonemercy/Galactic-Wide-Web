from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    HTTPException,
    InteractionContextTypes,
)
from disnake.ext import commands
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import DSSEmbed


class DSSCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Show info on the Democracy Space Station",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Directly opens the DSS tab of the Wiki, instead of using the menu.",
            "example_usage": "**`/dss`** opens the Wiki to the DSS tab.",
        },
    )
    async def dss(self, inter: AppCmdInter) -> None:
        try:
            await inter.response.defer(ephemeral=True)
        except HTTPException:
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        embed = DSSEmbed(
            language_json=guild_language,
            dss_data=self.bot.data.formatted_data.dss,
            next_vote_campaigns=self.bot.data.formatted_data.campaigns[:8],
        )
        await inter.send(embed=embed)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(DSSCog(bot))
