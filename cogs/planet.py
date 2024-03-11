from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Planet
from data.lists import planets


class PlanetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Planet cog has finished loading")

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        return [command for command in planets if user_input in command.lower()][:25]

    @commands.slash_command(
        description="Get details on a specific planet (only active planets available)"
    )
    async def planet(
        self,
        inter: AppCmdInter,
        planet: str = commands.Param(autocomplete=planet_autocomp),
    ):
        await inter.response.defer()
        embed = Planet(planet)
        try:
            await embed.get_data()
        except:
            return await inter.send(
                "Error when getting data",
                delete_after=10.0,
            )
        if embed.status == None:
            return await inter.send(
                "Data on that planet isn't available, please try an active planet",
                delete_after=10.0,
            )
        embed.set_data()
        await inter.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(PlanetCog(bot))
