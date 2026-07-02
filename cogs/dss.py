from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext.commands import Cog, Param, slash_command
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import DSSEmbed


class DSSCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @slash_command(
        description="Show current info on the Democracy Space Station",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows the current status of the Democracy Space Station, including its active tactical actions and the next planets being considered for a DSS vote (if available).",
            "example_usage": "**`/dss public:Yes`** returns the DSS status embed visible to everyone in the channel.",
        },
    )
    async def dss(
        self,
        inter: AppCmdInter,
        public: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild.id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild.id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild.id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        embed = DSSEmbed(
            language_json=guild_language,
            dss_data=self.bot.data.formatted_data.dss,
            next_vote_campaigns=self.bot.data.formatted_data.campaigns[:8],
        )
        await inter.send(embed=embed, ephemeral=public != "Yes")


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(DSSCog(bot))
