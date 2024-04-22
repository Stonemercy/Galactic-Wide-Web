from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Items
from json import load


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
        print("Weapons cog has finished loading")

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

    @commands.slash_command(
        description="Get info on one of the weapons used in the fight for democracy"
    )
    async def weapons(
        self,
        inter: AppCmdInter,
    ):
        pass

    @weapons.sub_command(description="Get a specific primary weapon's stats")
    async def primary(
        self,
        inter: AppCmdInter,
        primary: str = commands.Param(autocomplete=primary_autocomp),
    ):
        if primary not in self.primaries:
            return await inter.send(
                (
                    "That weapon isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
                delete_after=10,
            )
        chosen_primary = self.primaries[primary]
        embed = Items.Weapons.Primary(
            chosen_primary, self.types, self.fire_modes, self.traits
        )
        return await inter.send(embed=embed, ephemeral=True)

    @weapons.sub_command(description="Get a specific secondary weapon's stats")
    async def secondary(
        self,
        inter: AppCmdInter,
        secondary: str = commands.Param(autocomplete=secondary_autocomp),
    ):
        if secondary not in self.secondaries:
            return await inter.send(
                (
                    "That weapon isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
                delete_after=10,
            )
        chosen_secondary = self.secondaries[secondary]
        embed = Items.Weapons.Secondary(chosen_secondary, self.fire_modes, self.traits)
        return await inter.send(embed=embed, ephemeral=True)

    @weapons.sub_command(description="Get a specific secondary weapon's stats")
    async def grenade(
        self,
        inter: AppCmdInter,
        grenade: str = commands.Param(autocomplete=grenade_autocomp),
    ):
        if grenade not in self.grenades:
            return await inter.send(
                (
                    "That grenade isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
                delete_after=10,
            )
        chosen_grenade = self.grenades[grenade]
        embed = Items.Weapons.Grenade(chosen_grenade)
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(WeaponsCog(bot))
