from logging import getLogger
from disnake import AppCmdInter, File
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Planet
from data.lists import planets
from helpers.functions import planet_map, pull_from_api
from json import load

logger = getLogger("disnake")


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
        logger.info(f"PlanetCog, planet planet:{planet} public:{public} command used")
        planets_list = planets
        public = public != "Yes"
        if planet not in planets_list:
            return await inter.send(
                "Please select a planet from the list.",
                ephemeral=public,
            )
        await inter.response.defer(ephemeral=public)
        guild = Guilds.get_info(inter.guild_id)
        language = guild[5]
        data = await pull_from_api(
            get_planets=True, get_thumbnail=True, get_campaigns=True
        )
        for data_key, data_value in data.items():
            if data_value == None:
                logger.error(
                    f"PlanetCog, planet command, {data_key} returned {data_value}"
                )
                return await inter.send(
                    "There was an issue getting the data. Please try again later",
                    ephemeral=public,
                )
        planets_data: list = data["planets"]
        planet_data = None
        planet_thumbnail = None
        for thumbnail in data["thumbnails"]:
            if planet == thumbnail["planet"]["name"]:
                thumbnail_url = thumbnail["planet"]["image"].replace(" ", "%20")
                planet_thumbnail = f"https://helldivers.news{thumbnail_url}"
                break
        for i in planets_data:
            if i["name"] != planet.upper():
                continue
            else:
                planet_data = i
                break
        if planet_data == None:
            return await inter.send("Information on that planet is unavailable.")
        embed = Planet(planet_data, planet_thumbnail, language)
        try:
            embed.set_image(
                file=File(
                    f"resources/biomes/{planet_data['biome']['name'].lower()}.png"
                )
            )
        except:
            logger.error(
                f"PlanetCog, planet command, {planet_data['biome']['name'].lower()} biome image unavailable"
            )
            pass
        map_embed = planet_map(data, planet_data, language)
        embeds = [embed, map_embed]
        await inter.send(embeds=embeds, ephemeral=public)


def setup(bot: commands.Bot):
    bot.add_cog(PlanetCog(bot))
