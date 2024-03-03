from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Planet


class PlanetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Planet cog has finished loading")

    @commands.slash_command(
        description="Get details on a specific planet (only active planets available)"
    )
    async def planet(self, inter: AppCmdInter, planet: str):
        await inter.response.defer()
        embed = Planet(planet)
        await embed.get_data()
        if embed.data:
            embed.set_data()
            await inter.send(embed=embed)
        else:
            await inter.send(
                "That planet wasn't found, please try again", delete_after=5.0
            )


def setup(bot: commands.Bot):
    bot.add_cog(PlanetCog(bot))
