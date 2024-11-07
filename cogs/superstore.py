from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import SuperstoreEmbed


class SuperstoreCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Get the current Superstore rotation",
    )
    async def superstore(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        ephemeral = public != "Yes"
        await inter.response.defer(ephemeral=ephemeral)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        guild: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild:
            GuildsDB.insert_new_guild(inter.guild.id)
        embed = SuperstoreEmbed(self.bot.data.superstore)
        await inter.send(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SuperstoreCog(bot))
