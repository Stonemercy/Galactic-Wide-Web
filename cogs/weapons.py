from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds import Items
from utils.interactables import WikiButton


class WeaponsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.primaries = {
            item["name"]: item
            for item in self.bot.json_dict["items"]["primary_weapons"].values()
        }
        self.secondaries = {
            item["name"]: item
            for item in self.bot.json_dict["items"]["secondary_weapons"].values()
        }
        self.grenades = {
            item["name"]: item
            for item in self.bot.json_dict["items"]["grenades"].values()
        }

    async def primary_autocomp(inter: AppCmdInter, user_input: str):
        primaries = [
            i["name"] for i in inter.bot.json_dict["items"]["primary_weapons"].values()
        ]
        return [primary for primary in primaries if user_input in primary.lower()][:25]

    async def secondary_autocomp(inter: AppCmdInter, user_input: str):
        secondaries = [
            i["name"]
            for i in inter.bot.json_dict["items"]["secondary_weapons"].values()
        ]
        return [
            secondary for secondary in secondaries if user_input in secondary.lower()
        ][:25]

    async def grenade_autocomp(inter: AppCmdInter, user_input: str):
        grenades = [
            i["name"] for i in inter.bot.json_dict["items"]["grenades"].values()
        ]
        return [grenade for grenade in grenades if user_input in grenade.lower()][:25]

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on a specific weapon.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
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
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{primary = }>"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        if primary not in self.primaries:
            return await inter.send(
                guild_language["weapons"]["missing"],
                ephemeral=public != "Yes",
            )
        primary_json = self.primaries[primary]
        embed = Items.Weapons.Primary(
            weapon_json=primary_json,
            json_dict=self.bot.json_dict,
            language=guild_language,
        )
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **weapon primary __{primary}__** <@{self.bot.owner_id}> :warning:"
            )
        components = [
            WikiButton(
                link=f"https://helldivers.wiki.gg/wiki/{primary.replace(' ', '_')}"
            )
        ]
        return await inter.send(
            embed=embed, ephemeral=public != "Yes", components=components
        )

    @weapons.sub_command(description="Use this for secondary weapons")
    async def secondary(
        self,
        inter: AppCmdInter,
        secondary: str = commands.Param(
            autocomplete=secondary_autocomp,
            description="The Secondary weapon you want to lookup",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{secondary = }>"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        if secondary not in self.secondaries:
            return await inter.send(
                guild_language["weapons"]["missing"],
                ephemeral=public != "Yes",
            )
        secondary_json = self.secondaries[secondary]
        embed = Items.Weapons.Secondary(
            weapon_json=secondary_json,
            json_dict=self.bot.json_dict,
            language=guild_language,
        )
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **weapon secondary __{secondary}__** <@{self.bot.owner_id}> :warning:"
            )
        components = [
            WikiButton(
                link=f"https://helldivers.wiki.gg/wiki/{secondary.replace(' ', '_')}"
            )
        ]
        return await inter.send(
            embed=embed, ephemeral=public != "Yes", components=components
        )

    @weapons.sub_command(description="Use this for grenades")
    async def grenade(
        self,
        inter: AppCmdInter,
        grenade: str = commands.Param(
            autocomplete=grenade_autocomp, description="The Grenade you want to lookup"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{grenade = }>"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        if grenade not in self.grenades:
            return await inter.send(
                guild_language["weapons"]["missing"],
                ephemeral=public != "Yes",
            )
        grenade_json = self.grenades[grenade]
        embed = Items.Weapons.Grenade(
            grenade_json=grenade_json, language=guild_language
        )
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **weapon grenade __{grenade}__** <@{self.bot.owner_id}> :warning:"
            )
        components = [
            WikiButton(
                link=f"https://helldivers.wiki.gg/wiki/{grenade.replace(' ', '_')}"
            )
        ]
        return await inter.send(
            embed=embed, ephemeral=public != "Yes", components=components
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WeaponsCog(bot))
