from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from random import choice
from utils.checks import wait_for_startup
from utils.containers import RandomiserContainer
from utils.dataclasses import RandomiserData
from utils.dbv2 import GWWGuild, GWWGuilds


STRATAGEMS_TO_IGNORE = [
    "SOS Beacon",
    "Hellbomb",
    "Resupply",
    "Reinforce",
    "SSSD Delivery",
    "Seismic Probe",
    "Upload Data",
    "Eagle Rearm",
    "SEAF Artillery",
    "Super Earth Flag",
    "Orbital Illumination Flare",
    "SoS Beacon",
    "Prospecting Drill",
]

SUPPORT_WEAPONS = [
    "AC-8 Autocannon",
    "APW-1 Anti-Materiel Rifle",
    "Arc-3 Arc Thrower",
    "CQC-1 One True Flag",
    "EAT-17 Expendable Anti-Tank",
    "EAT-700 Expendable Napalm",
    "Entrenchment Tool",
    "FAF-14 Spear",
    "FLAM-40 Flamethrower",
    "GL-21 Grenade Launcher",
    "GL-52 De-Escalator",
    "GR-8 Recoilless Rifle",
    "LAS-98 Laser Cannon",
    "LAS-99 Quasar Cannon",
    "M-105 Stalwart",
    "MG-206 Heavy Machine Gun",
    "MG-43 Machine Gun",
    "MLS-4X Commando",
    "MS-11 Solo Silo",
    "PLAS-45 Epoch",
    "RL-77 Airburst Rocket Launcher",
    "RS-422 Railgun",
    "S-11 Speargun",
    "SG-88 Break-Action Shotgun",
    "StA-X3 W.A.S.P. Launcher",
    "TX-41 Sterelizer",
]

BACKPACKS = [
    "AC-8 Autocannon",
    'AX/AR-23 "Guard Dog"',
    'AX/ARC-3 "Guard Dog" K-9',
    'AX/LAS-5 "Guard Dog" Rover',
    'AX/TX-13 "Guard Dog" Dog Breath',
    "B-1 Supply Pack",
    "B-100 Portable Hellbomb",
    "GR-8 Recoilless Rifle",
    "LIFT-182 Warp Pack",
    "Lift-850 Jump Pack",
    "Lift-860 Hover Pack",
    "SH-20 Ballistic Shield Backpack",
    "SH-32 Shield Generator Pack",
    "SH-51 Directional Shield",
    "StA-X3 W.A.S.P. Launcher",
]


class RandomiserCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Get a random loadout to use in-game",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Gets a completely random loadout to use in-game including Stratagems, Weapons, Booster, Armour and where to spawn",
            "example_usage": "**`/randomiser`** returns something",
        },
    )
    async def randomiser(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        stratagems_list = []
        backpack_strat = False
        support_weapon_strat = False
        for _ in range(4):
            stratagem: list[str, dict] = choice(
                [
                    [name, data]
                    for category in self.bot.json_dict["stratagems"].values()
                    for name, data in category.items()
                ]
            )
            while (
                (stratagem[0] in STRATAGEMS_TO_IGNORE)
                or (stratagem in stratagems_list)
                or (stratagem[0] in BACKPACKS and backpack_strat)
                or (stratagem[0] in SUPPORT_WEAPONS and support_weapon_strat)
            ):
                stratagem = choice(
                    [
                        [strat, data]
                        for category in self.bot.json_dict["stratagems"].values()
                        for strat, data in category.items()
                    ]
                )
            if stratagem[0] in BACKPACKS:
                print(stratagem[0], "is a backpack")
                backpack_strat = True
            if stratagem[0] in SUPPORT_WEAPONS:
                print(stratagem[0], "is a support weapon")
                support_weapon_strat = True
            stratagems_list.append(stratagem)
        primary_weapon = choice(
            list(self.bot.json_dict["items"]["primary_weapons"].values())
        )
        secondary_weapon = choice(
            list(self.bot.json_dict["items"]["secondary_weapons"].values())
        )
        grenade = choice(list(self.bot.json_dict["items"]["grenades"].values()))
        booster = choice(list(self.bot.json_dict["items"]["boosters"].values()))
        armor = choice(list(self.bot.json_dict["items"]["armor"].values()))
        where_to_spawn = choice(
            [
                "North",
                "North-East",
                "East",
                "South-East",
                "South",
                "South-West",
                "West",
                "North-West",
            ]
        )

        randomiser_data = RandomiserData(
            stratagems=stratagems_list,
            primary_weapon=primary_weapon,
            secondary_weapon=secondary_weapon,
            grenade=grenade,
            booster=booster,
            armor=armor,
            where_to_spawn=where_to_spawn,
            json_dict=self.bot.json_dict,
        )
        component = RandomiserContainer(randomiser_data=randomiser_data)
        await inter.send(
            components=component,
            ephemeral=public != "Yes",
        )
        """
        TODO:
         - Stratagems x 4
         - Primary Weapon
         - Secondary Weapon
         - Grenade
         - Booster
         - Armour (exc helmet)
         - Where to spawn
           - GET SPAWN CHOICE ICON FROM GAME FILES
           - make choice within the circle and probably away from the edge a bit?
         - Button to randomise the loadout
        """

    @commands.Cog.listener("on_button_click")
    async def re_roll_listener(self, inter: MessageInteraction):
        if inter.component.custom_id != "re_roll_randomiser":
            return
        try:
            await inter.response.defer()
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with this interaction, please try again.",
                delete_after=5,
            )
            return
        stratagems_list = []
        backpack_strat = False
        support_weapon_strat = False
        for _ in range(4):
            stratagem: list[str, dict] = choice(
                [
                    [strat, data]
                    for category in self.bot.json_dict["stratagems"].values()
                    for strat, data in category.items()
                ]
            )
            while (
                (stratagem[0] in STRATAGEMS_TO_IGNORE)
                or (stratagem in stratagems_list)
                or (stratagem[0] in BACKPACKS and backpack_strat)
                or (stratagem[0] in SUPPORT_WEAPONS and support_weapon_strat)
            ):
                stratagem = choice(
                    [
                        [strat, data]
                        for category in self.bot.json_dict["stratagems"].values()
                        for strat, data in category.items()
                    ]
                )
            if stratagem[0] in BACKPACKS:
                print(stratagem[0], "is a backpack")
                backpack_strat = True
            if stratagem[0] in SUPPORT_WEAPONS:
                print(stratagem[0], "is a support weapon")
                support_weapon_strat = True
            stratagems_list.append(stratagem)
        primary_weapon = choice(
            list(self.bot.json_dict["items"]["primary_weapons"].values())
        )
        secondary_weapon = choice(
            list(self.bot.json_dict["items"]["secondary_weapons"].values())
        )
        grenade = choice(list(self.bot.json_dict["items"]["grenades"].values()))
        booster = choice(list(self.bot.json_dict["items"]["boosters"].values()))
        armor = choice(list(self.bot.json_dict["items"]["armor"].values()))
        where_to_spawn = choice(
            [
                "North",
                "North-East",
                "East",
                "South-East",
                "South",
                "South-West",
                "West",
                "North-West",
            ]
        )

        randomiser_data = RandomiserData(
            stratagems=stratagems_list,
            primary_weapon=primary_weapon,
            secondary_weapon=secondary_weapon,
            grenade=grenade,
            booster=booster,
            armor=armor,
            where_to_spawn=where_to_spawn,
            json_dict=self.bot.json_dict,
        )
        component = RandomiserContainer(randomiser_data=randomiser_data)
        await inter.edit_original_response(
            components=component,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(RandomiserCog(bot))
