from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Planet
from data.lists import planets
from helpers.functions import pull_from_api
from json import load


class PlanetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.planets_json = load(
            open("data/json/planets/planets.json", encoding="UTF-8")
        )
        self.biomes = load(open("data/json/planets/biomes.json", encoding="UTF-8"))
        self.environmentals = load(
            open("data/json/planets/environmentals.json", encoding="UTF-8")
        )
        print("Planet cog has finished loading")

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        return [command for command in planets if user_input in command.lower()][:25]

    @commands.slash_command(description="Get details on a specific planet")
    async def planet(
        self,
        inter: AppCmdInter,
        planet: str = commands.Param(autocomplete=planet_autocomp),
    ):
        planets_list = planets
        if planet not in planets_list:
            return await inter.send(
                "Please select a planet from the list.",
                ephemeral=True,
            )
        await inter.response.defer()
        data = await pull_from_api(get_planets=True, get_thumbnail=True)
        planets_data = data["planets"]
        planet_data = None
        planet_thumbnail = None
        for thumbnail in data["thumbnails"]:
            if planet == thumbnail["planet"]["name"]:
                thumbnail_url = thumbnail["planet"]["image"].replace(" ", "%20")
                planet_thumbnail = f"https://helldivers.news{thumbnail_url}"
                break
        for i in planets_data:
            if i["name"] != planet:
                continue
            else:
                planet_data = i
                break
        if planet_data == None:
            return await inter.send("Information on that planet is unavailable.")
        planet_json = self.planets_json[str(planet_data["index"])]
        planet_biome = self.biomes[planet_json["biome"]]
        planet_enviros = []
        for i in planet_json["environmentals"]:
            planet_enviros.append(self.environmentals[i])
        embed = Planet(planet_data, planet_thumbnail, planet_biome, planet_enviros)
        await inter.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(PlanetCog(bot))
