from logging import getLogger
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Items
from json import load

logger = getLogger("disnake")


class WeaponsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.types = load(open("data/json/items/weapons/types.json"))
        self.fire_modes = load(open("data/json/items/weapons/fire_modes.json"))
        self.traits = load(open("data/json/items/weapons/traits.json"))
        self.primaries = load(open("data/json/items/weapons/primary.json"))
        self.primaries["item_list"] = {}
        for i, j in self.primaries.items():
            if i == "item_list":
                continue
            self.primaries["item_list"][j["name"]] = j
        self.primaries = self.primaries["item_list"]

        self.secondaries = load(open("data/json/items/weapons/secondary.json"))
        self.secondaries["item_list"] = {}
        for i, j in self.secondaries.items():
            if i == "item_list":
                continue
            self.secondaries["item_list"][j["name"]] = j
        self.secondaries = self.secondaries["item_list"]

        self.grenades = load(open("data/json/items/weapons/grenades.json"))
        self.grenades["item_list"] = {}
        for i, j in self.grenades.items():
            if i == "item_list":
                continue
            self.grenades["item_list"][j["name"]] = j
        self.grenades = self.grenades["item_list"]

    async def primary_autocomp(inter: AppCmdInter, user_input: str):
        primaries_json = load(open("data/json/items/weapons/primary.json"))
        primaries = []
        for i in primaries_json.values():
            primaries.append(i["name"])
        return [primary for primary in primaries if user_input in primary.lower()]

    async def secondary_autocomp(inter: AppCmdInter, user_input: str):
        secondaries_json = load(open("data/json/items/weapons/secondary.json"))
        secondaries = []
        for i in secondaries_json.values():
            secondaries.append(i["name"])
        return [
            secondary for secondary in secondaries if user_input in secondary.lower()
        ]

    async def grenade_autocomp(inter: AppCmdInter, user_input: str):
        grenades_json = load(open("data/json/items/weapons/grenades.json"))
        grenades = []
        for i in grenades_json.values():
            grenades.append(i["name"])
        return [grenade for grenade in grenades if user_input in grenade.lower()]

    @commands.slash_command(description="Returns information on a specific weapon.")
    async def weapons(
        self,
        inter: AppCmdInter,
    ):
        pass

    @weapons.sub_command(description="Use this for primary weapons")
    async def primary(
        self,
        inter: AppCmdInter,
        primary: str = commands.Param(autocomplete=primary_autocomp),
    ):
        logger.info("weapons_primary command used")
        guild_in_db = Guilds.get_info(inter.guild_id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if primary not in self.primaries:
            return await inter.send(
                guild_language["weapons.missing"],
                ephemeral=True,
            )
        chosen_primary = self.primaries[primary]
        embed = Items.Weapons.Primary(
            chosen_primary, self.types, self.fire_modes, self.traits, guild_language
        )
        return await inter.send(embed=embed, ephemeral=True)

    @weapons.sub_command(description="Use this for secondary weapons")
    async def secondary(
        self,
        inter: AppCmdInter,
        secondary: str = commands.Param(autocomplete=secondary_autocomp),
    ):
        logger.info("weapons_secondary command used")
        guild_in_db = Guilds.get_info(inter.guild_id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if secondary not in self.secondaries:
            return await inter.send(
                guild_language["weapons.missing"],
                ephemeral=True,
                delete_after=10,
            )
        chosen_secondary = self.secondaries[secondary]
        embed = Items.Weapons.Secondary(
            chosen_secondary, self.fire_modes, self.traits, guild_language
        )
        return await inter.send(embed=embed, ephemeral=True)

    @weapons.sub_command(description="Use this for grenades")
    async def grenade(
        self,
        inter: AppCmdInter,
        grenade: str = commands.Param(autocomplete=grenade_autocomp),
    ):
        logger.info("weapons_grenade command used")
        guild_in_db = Guilds.get_info(inter.guild_id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if grenade not in self.grenades:
            return await inter.send(
                guild_language["weapons.missing"],
                ephemeral=True,
                delete_after=10,
            )
        chosen_grenade = self.grenades[grenade]
        embed = Items.Weapons.Grenade(chosen_grenade, guild_language)
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(WeaponsCog(bot))
