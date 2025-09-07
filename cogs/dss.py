from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.wiki import Wiki


class DSSCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Go directly to the DSS tab of the wiki",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Goes directly to the DSS tab of the wiki, instead of using the menu.",
            "example_usage": "**`/dss`** returns the wiki open to the DSS tab.",
        },
    )
    async def dss(self, inter: AppCmdInter):
        try:
            await inter.response.defer(ephemeral=True)
        except (NotFound, InteractionTimedOut):
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
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        embed = Wiki.Embeds.DSSEmbed(
            dss_data=self.bot.data.dss,
            language_json=guild_language,
            localized_planet_names=self.bot.data.json_dict["planets"],
        )
        components = Wiki.Buttons.dss_action_rows(language_json=guild_language)
        await inter.send(embed=embed, components=components)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DSSCog(bot))
