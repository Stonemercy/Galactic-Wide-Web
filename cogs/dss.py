from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.interactables import WikiButton
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import DSSEmbed


class DSSCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on the Democracy Space Station",
        dm_permission=False,
    )
    async def dss(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ):
        ephemeral = public != "Yes"
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        await inter.response.defer(ephemeral=ephemeral)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild.id)
        if self.bot.data.dss == "Error":
            return await inter.send(
                "The DSS is currently unavailable. Please try again later."
            )
        guild_language = self.bot.json_dict["languages"][guild_in_db.language]
        embed = DSSEmbed(self.bot.data.dss, guild_language)
        components = [
            WikiButton(link=f"https://helldivers.wiki.gg/wiki/Democracy_Space_Station")
        ]
        await inter.send(embed=embed, components=components)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DSSCog(bot))
