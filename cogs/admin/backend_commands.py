from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import is_whitelisted, wait_for_startup
from utils.containers import GlobalEventsContainer, GWEContainer


class BackendCommandsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def id_autocomp(inter: AppCmdInter, user_input: str):
        if not inter.bot.data.loaded:
            return []
        id_list = sorted(
            [
                f"{i.id}-{i.effect_description['name']}"
                for i in inter.bot.data.galactic_war_effects
            ],
            key=lambda x: int(x.split("-")[0]),
            reverse=True,
        )
        return [gwe for gwe in id_list if str(user_input).lower() in str(gwe).lower()][
            :25
        ]

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        if not inter.bot.data.loaded:
            return []
        return [
            f"{p.index}-{p.name}"
            for p in inter.bot.data.planets.values()
            if user_input.lower() in f"{p.index}-{p.name}".lower()
        ][:25]

    @wait_for_startup()
    @is_whitelisted()
    @commands.slash_command(
        description="Check a galactic effect",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def gwe(
        self,
        inter: AppCmdInter,
        id: str = commands.Param(
            autocomplete=id_autocomp,
            description="The ID you want to lookup",
            default=0,
        ),
        on_planet: str = commands.Param(
            autocomplete=planet_autocomp,
            description="The planet you want to lookup",
            default="",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{id = }> <{type = }> <{public = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        gwe_list = None
        if id:
            id = int(id.split("-")[0])
            if id != 0:
                gwe_list = [g for g in self.bot.data.galactic_war_effects if g.id == id]
        elif on_planet:
            gwe_list = [
                g
                for g in self.bot.data.planets[
                    int(on_planet.split("-")[0])
                ].active_effects
            ]
        if gwe_list:
            components = []
            for gwe in gwe_list:
                planets_with_gwe = [
                    p
                    for p in self.bot.data.planets.values()
                    if gwe.id in [effect.id for effect in p.active_effects]
                ]
                global_events_list = [
                    i
                    for i in self.bot.data.global_events["en"]
                    if gwe.id in [j.id for j in i.effects]
                ]
                if (
                    global_events_list != []
                    and global_events_list[0].planet_indices == []
                ):
                    planets_with_gwe = "ALL"
                container = GWEContainer(
                    gwe=gwe,
                    planets_with_gwe=planets_with_gwe,
                )
                components.append(container)
            await inter.send(components=components[:5], ephemeral=public != "Yes")
        else:
            await inter.send(
                "Couldn't find that effect, sorry", ephemeral=public != "Yes"
            )

    async def title_autocomp(inter: AppCmdInter, user_input: str):
        if inter.bot.data.loaded:
            return [
                ge
                for ge in [
                    f"{i.id}-{i.title}{[j.id for j in i.effects]}"
                    for i in inter.bot.data.global_events["en"]
                ]
                if user_input.lower() in ge.split("-")[1].lower()
            ][:25]
        else:
            return []

    @wait_for_startup()
    @is_whitelisted()
    @commands.slash_command(
        description="Check a global event",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def global_event(
        self,
        inter: AppCmdInter,
        title: str = commands.Param(
            autocomplete=title_autocomp, description="The event you want to lookup"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{title = }> <{public = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        ge_id = title.split("-")[0]
        ge_list = [
            ge for ge in self.bot.data.global_events["en"] if ge.id == int(ge_id)
        ]
        if ge_list:
            components = []
            for ge in ge_list:
                container = GlobalEventsContainer(
                    long_lang_code=self.bot.json_dict["languages"]["en"]["code_long"],
                    container_json=self.bot.json_dict["languages"]["en"]["containers"][
                        "GlobalEventsContainer"
                    ],
                    global_event=ge,
                    planets=self.bot.data.planets,
                    with_expiry_time=True,
                )
                components.append(container)
            await inter.send(components=components, ephemeral=public != "Yes")
        else:
            await inter.send(
                "Couldn't find that effect, sorry", ephemeral=public != "Yes"
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=BackendCommandsCog(bot))
