from disnake import AppCmdInter
from disnake.ext import commands
from json import load
from main import GalacticWideWebBot
from utils.db import Guilds
from utils.embeds import Items


class WeaponsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.types = load(open("data/json/items/weapons/types.json"))
        self.fire_modes = load(open("data/json/items/weapons/fire_modes.json"))
        self.traits = load(open("data/json/items/weapons/traits.json"))

        self.primaries_json = load(open("data/json/items/weapons/primary.json"))
        self.primaries = {item["name"]: item for item in self.primaries_json.values()}

        self.secondaries_json = load(open("data/json/items/weapons/secondary.json"))
        self.secondaries = {item["name"]: item for item in self.primaries_json.values()}

        self.grenades_json = load(open("data/json/items/weapons/grenades.json"))
        self.grenades = {item["name"]: item for item in self.primaries_json.values()}

    async def primary_autocomp(inter: AppCmdInter, user_input: str):
        primaries_json = load(open("data/json/items/weapons/primary.json"))
        primaries = [i["name"] for i in primaries_json.values()]
        return [primary for primary in primaries if user_input in primary.lower()]

    async def secondary_autocomp(inter: AppCmdInter, user_input: str):
        secondaries_json = load(open("data/json/items/weapons/secondary.json"))
        secondaries = [i["name"] for i in secondaries_json.values()]
        return [
            secondary for secondary in secondaries if user_input in secondary.lower()
        ]

    async def grenade_autocomp(inter: AppCmdInter, user_input: str):
        grenades_json = load(open("data/json/items/weapons/grenades.json"))
        grenades = [i["name"] for i in grenades_json.values()]
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
        primary: str = commands.Param(
            autocomplete=primary_autocomp,
            description="The Primary weapon you want to lookup",
        ),
    ):
        self.bot.logger.info(
            f"WeaponsCog, weapons primary primary:{primary} command used"
        )
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = Guilds.insert_new_guild(inter.guild.id)
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
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **weapon primary __{primary}__** <@{self.bot.owner_id}> :warning:"
            )
        return await inter.send(embed=embed, ephemeral=True)

    @weapons.sub_command(description="Use this for secondary weapons")
    async def secondary(
        self,
        inter: AppCmdInter,
        secondary: str = commands.Param(
            autocomplete=secondary_autocomp,
            description="The Secondary weapon you want to lookup",
        ),
    ):
        self.bot.logger.info(
            f"WeaponsCog, weapons secondary secondary:{secondary} command used"
        )
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = Guilds.insert_new_guild(inter.guild.id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if secondary not in self.secondaries:
            return await inter.send(
                guild_language["weapons.missing"],
                ephemeral=True,
            )
        chosen_secondary = self.secondaries[secondary]
        embed = Items.Weapons.Secondary(
            chosen_secondary, self.fire_modes, self.traits, guild_language
        )
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **weapon secondary __{secondary}__** <@{self.bot.owner_id}> :warning:"
            )
        return await inter.send(embed=embed, ephemeral=True)

    @weapons.sub_command(description="Use this for grenades")
    async def grenade(
        self,
        inter: AppCmdInter,
        grenade: str = commands.Param(
            autocomplete=grenade_autocomp, description="The Grenade you want to lookup"
        ),
    ):
        self.bot.logger.info(
            f"WeaponsCog, weapons grenade grenade:{grenade} command used"
        )
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = Guilds.insert_new_guild(inter.guild.id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if grenade not in self.grenades:
            return await inter.send(
                guild_language["weapons.missing"],
                ephemeral=True,
            )
        chosen_grenade = self.grenades[grenade]
        embed = Items.Weapons.Grenade(chosen_grenade, guild_language)
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **weapon grenade __{grenade}__** <@{self.bot.owner_id}> :warning:"
            )
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WeaponsCog(bot))
