from disnake import AppCmdInter, File
from disnake.ext import commands
from helpers.api import API
from helpers.db import Guilds
from helpers.embeds import PlanetEmbed
from data.lists import planets
from helpers.functions import planet_map
from helpers.api import Data, API
from json import load


class PlanetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.planets_json = load(
            open("data/json/planets/planets.json", encoding="UTF-8")
        )

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        return [command for command in planets if user_input in command.lower()][:25]

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
        public = public != "Yes"
        await inter.response.defer(ephemeral=public)
        self.bot.logger.info(
            f"PlanetCog, planet planet:{planet} public:{public} command used"
        )
        planets_list = planets
        if planet not in planets_list:
            return await inter.send(
                "Please select a planet from the list.",
                ephemeral=public,
            )
        guild = Guilds.get_info(inter.guild_id)
        if not guild:
            guild = Guilds.insert_new_guild(inter.guild.id)
        language = guild[5]
        api = API()
        await api.pull_from_api(
            get_planets=True, get_thumbnail=True, get_campaigns=True
        )
        if api.error:
            error_channel = self.bot.get_channel(
                1212735927223590974
            ) or await self.bot.fetch_channel(1212735927223590974)
            await error_channel.send(
                f"<@164862382185644032>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
            return await inter.send(
                "There was an issue getting the data. Please try again later",
                ephemeral=public,
            )
        data = Data(data_from_api=api)
        planet_thumbnail = [
            f"https://helldivers.news{thumbnail['planet']['image'].replace(' ', '%20')}"
            for thumbnail in data.thumbnails
            if thumbnail["planet"]["name"] == planet
        ]
        planet_thumbnail = planet_thumbnail[0] if planet_thumbnail != [] else None
        planet_data = [i for i in data.planets.values() if i.name == planet.upper()]
        if planet_data == []:
            return await inter.send("Information on that planet is unavailable.")
        else:
            planet_data = planet_data[0]
        embed = PlanetEmbed(planet_data, planet_thumbnail, language)
        try:
            embed.set_image(
                file=File(f"resources/biomes/{planet_data.biome['name'].lower()}.png")
            )
        except:
            self.bot.logger.error(
                f"PlanetCog, planet command, {planet_data.biome['name'].lower()} biome image unavailable"
            )
        map_embed = planet_map(data, planet_data.index, language)
        await inter.send(embeds=[embed, map_embed], ephemeral=public)


def setup(bot: commands.Bot):
    bot.add_cog(PlanetCog(bot))
