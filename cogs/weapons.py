from collections import OrderedDict
from enum import auto
from operator import getitem
from os import getenv
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

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
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
        weapon_info = weapons[weapon]
        embed = Weapons.Single(weapon, weapon_info)
        return await inter.send(embed=embed)

    # SORT BY #####################################################################
    @weapons.sub_command_group()
    async def by(self, inter: AppCmdInter):
        pass

    @by.sub_command(description="Test for weapons")
    async def dps(self, inter: AppCmdInter):
        sorted_by_dps = sorted(
            weapons.items(), key=lambda x: x[1]["dps"], reverse=True
        )[0:5]
        embed = Weapons.All(sorted_by_dps)
        return await inter.send(embed=embed)

    @by.sub_command()
    async def damage(self, inter: AppCmdInter):
        return inter.send("Weapon Damage blah blah")

    # ALL #########################################################################
    @weapons.sub_command()
    async def all(self, inter: AppCmdInter):
        return inter.send("All weapon info")


def setup(bot: commands.Bot):
    bot.add_cog(WeaponsCog(bot))
