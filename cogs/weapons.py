from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Weapons
from data.lists import weapons


class WeaponsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Weapons cog has finished loading")

    async def weapon_autocomp(inter: AppCmdInter, user_input: str):
        return [command for command in weapons if user_input in command.lower()]

    @commands.slash_command(
        description="Get info on one of the weapons used in the fight for democracy"
    )
    async def weapons(
        self,
        inter: AppCmdInter,
    ):
        pass

    @weapons.sub_command(description="Get a specific weapon's stats")
    async def specific(
        self,
        inter: AppCmdInter,
        weapon: str = commands.Param(autocomplete=weapon_autocomp),
    ):
        if weapon not in weapons:
            return await inter.send(
                (
                    "That weapon isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        weapon_info = weapons[weapon]
        embed = Weapons.Single(weapon, weapon_info)
        return await inter.send(embed=embed)

    # SORT BY #####################################################################
    @weapons.sub_command(description="Returns 6 weapons")
    async def by(
        self,
        inter: AppCmdInter,
        stat: str = commands.Param(
            default=None,
            choices=["DPS", "Damage", "Fire Rate"],
            description="The stat you want the weapons sorted by",
        ),
        weapon_type: str = commands.Param(
            name="type",
            default=None,
            choices=[
                "Pistol",
                "Shotgun",
                "Energy-Based",
                "Explosive",
                "Submachine Gun",
                "Marksman Rifle",
                "Assault Rifle",
            ],
            description="The weapon type you want to get",
        ),
    ):
        if stat is not None and weapon_type is not None:
            return await inter.send(
                "Please only use one filter/sort at a time", ephemeral=True
            )
        elif stat is not None:
            stat = stat.lower()
            sorted_by_stat = sorted(
                weapons.items(), key=lambda x: x[1][stat], reverse=True
            )[0:6]
            embed = Weapons.All(sorted_by_stat)
            return await inter.send(embed=embed)
        elif weapon_type is not None:
            sorted_by_type = []
            for i, j in weapons.items():
                if weapon_type == j["type"]:
                    sorted_by_type.append((i, j))
            embed = Weapons.All(sorted_by_type)
            return await inter.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(WeaponsCog(bot))
