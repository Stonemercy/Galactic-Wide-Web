from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.interactables import WikiButton
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import MajorOrderEmbed


class MajorOrderCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on an Automaton or variation.",
        dm_permission=False,
    )
    async def major_order(
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
        guild_language = self.bot.json_dict["languages"][guild_in_db.language]
        if self.bot.data.assignment in (None, []):
            return await inter.send(
                guild_language["major_order"]["no_order"], ephemeral=ephemeral
            )
        embed = MajorOrderEmbed(
            data=self.bot.data,
            language=guild_language,
            planet_names=self.bot.json_dict["planets"],
            reward_types=self.bot.json_dict["items"]["reward_types"],
            with_health_bars=True,
        )
        components = [WikiButton(link=f"https://helldivers.wiki.gg/wiki/Major_Orders")]
        await inter.send(embed=embed, components=components)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MajorOrderCog(bot))
