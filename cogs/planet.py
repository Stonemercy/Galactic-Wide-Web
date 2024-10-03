from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import PlanetEmbed
from utils.functions import planet_map
from utils.api import Data, API


class PlanetCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        return [
            planet["name"]
            for planet in inter.bot.json_dict["planets"].values()
            if user_input in planet["name"].lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(description="Returns the war details on a specific planet.")
    async def planet(
        self,
        inter: AppCmdInter,
        planet: str = commands.Param(
            autocomplete=planet_autocomp, description="The planet you want to lookup"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        ephemeral = public != "Yes"
        await inter.response.defer(ephemeral=ephemeral)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{planet = }> <{public = }>"
        )
        if planet not in [
            planet["name"] for planet in self.bot.json_dict["planets"].values()
        ]:
            return await inter.send(
                "Please select a planet from the list.",
                ephemeral=ephemeral,
            )
        guild: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild:
            guild = GuildsDB.insert_new_guild(inter.guild.id)
        api = API()
        await api.pull_from_api(
            get_planets=True, get_thumbnail=True, get_campaigns=True
        )
        if api.error:
            await self.bot.moderator_channel.send(
                f"<@{self.bot.owner_id}>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
            return await inter.send(
                "There was an issue getting the data. Please try again later",
                ephemeral=ephemeral,
            )
        data = Data(data_from_api=api)
        planet_names = [
            planet_names
            for planet_names in self.bot.json_dict["planets"].values()
            if planet_names["name"] == planet
        ][0]
        embed = PlanetEmbed(
            planet_names=planet_names,
            data=data,
            language=self.bot.json_dict["languages"][guild.language],
        )
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for biome of **planet __{planet}__** <@{self.bot.owner_id}> :warning:"
            )
        map_embed = planet_map(data, embed.planet.index, guild.language)
        await inter.send(embeds=[embed, map_embed], ephemeral=ephemeral)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(PlanetCog(bot))
