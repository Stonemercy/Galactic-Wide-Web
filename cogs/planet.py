from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Planet
from data.lists import planets
from helpers.functions import pull_from_api


class PlanetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
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
                "Please select a planet from the list or capitalize appropriately.",
                ephemeral=True,
            )
        await inter.response.defer()
        data = await pull_from_api(get_planets=True)
        planets_data = data["planets"]
        for i in planets_data:
            if i["name"] != planet:
                continue
            else:
                planet_data = i
        if not planet_data:
            return await inter.send(
                "I couldn't get info on that planet, please try again", ephemeral=True
            )
        embed = Planet(planet_data)
        await inter.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(PlanetCog(bot))
