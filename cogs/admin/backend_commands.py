from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import is_whitelisted, wait_for_startup
from utils.containers import GlobalEventsContainer, GWEContainer


class BackendCommandsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    async def id_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.data.loaded:
            return []
        id_list = sorted(
            [
                f"{i.id}-{i.effect_description['name']}"
                for i in inter.bot.data.formatted_data.war_effects.values()
            ],
            key=lambda x: int(x.split("-")[0]),
            reverse=True,
        )
        return [gwe for gwe in id_list if str(user_input).lower() in str(gwe).lower()][
            :25
        ]

    async def planet_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.data.loaded:
            return []
        return [
            f"{p.index}-{p.names.get('en-GB', str(p.index))}"
            for p in sorted(
                inter.bot.data.formatted_data.planets.values(),
                key=lambda x: len(x.active_effects),
                reverse=True,
            )
            if user_input.lower()
            in f"{p.index}-{p.names.get('en-GB', str(p.index))}".lower()
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
            default="0",
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
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        gwe_list = []
        if id != "0":
            try:
                id = int(id.split("-")[0])
            except ValueError:
                await inter.send(
                    f"The id you supplied (`{id}`) is in the incorrect format. Please choose an ID from the list or type in the ID on its own."
                )
                return
            gwe_list = [
                g
                for g in self.bot.data.formatted_data.war_effects.values()
                if g.id == id
            ]
        elif on_planet != "":
            try:
                planet_index = int(on_planet.split("-")[0])
            except ValueError:
                await inter.send(
                    f"The planet you supplied (`{on_planet}`) is in the incorrect format. Please choose a planet from the list or type in the planet on its own."
                )
                return
            planet = self.bot.data.formatted_data.planets.get(planet_index)
            if not planet:
                await inter.send(
                    f"`{planet_index}` isn't a valid planet index :thinking:"
                )
                return
            if not planet.active_effects:
                await inter.send(
                    f"No effects found on `{planet.names.get('en-GB', planet.index)}`, sorry :pensive:"
                )
                return
            gwe_list = list(planet.active_effects)

        if gwe_list != []:
            components = []
            for gwe in gwe_list:
                global_events_list = [
                    i
                    for i in self.bot.data.formatted_data.global_events["en"]
                    if gwe.id in (j.id for j in i.effects)
                ]
                if (
                    global_events_list != []
                    and global_events_list[0].planet_indices == []
                ):
                    planets_with_gwe = "ALL"
                else:
                    planets_with_gwe = [
                        p
                        for p in self.bot.data.formatted_data.planets.values()
                        if gwe in p.active_effects
                    ]
                container = GWEContainer(
                    gwe=gwe,
                    planets_with_gwe=planets_with_gwe,
                    with_pretty_print=len(gwe_list) <= 4,
                )
                components.append(container)
            await inter.send(components=components, ephemeral=public != "Yes")
        else:
            await inter.send(
                "Couldn't find that effect, sorry :pensive:", ephemeral=public != "Yes"
            )

    async def title_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if inter.bot.data.loaded:
            return [
                ge
                for ge in [
                    f"{i.id}-{i.title}{[j.id for j in i.effects]}"
                    for i in inter.bot.data.formatted_data.global_events["en"]
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
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        try:
            ge_id = int(title.split("-")[0])
        except ValueError:
            await inter.send(
                f"The title you submitted (`{title}`) is not in the correct format. Please choose one from the list provided."
            )
            return
        ge_list = [
            ge
            for ge in self.bot.data.formatted_data.global_events["en"]
            if ge.id == ge_id
        ]
        if ge_list != []:
            components = []
            for ge in ge_list:
                container = GlobalEventsContainer(
                    container_json=self.bot.json_dict["languages"]["en"]["containers"][
                        "GlobalEventsContainer"
                    ],
                    global_event=ge,
                    planets=self.bot.data.formatted_data.planets,
                    with_expiry_time=True,
                )
                components.append(container)
            await inter.send(components=components, ephemeral=public != "Yes")
        else:
            await inter.send(
                "Couldn't find that effect, sorry :pensive:", ephemeral=public != "Yes"
            )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(BackendCommandsCog(bot))
