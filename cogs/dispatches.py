from datetime import datetime
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    HTTPException,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.containers import DispatchContainer
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds, WarInfo
from utils.interactables import DispatchStringSelect


class DispatchesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.current_war_info = None

    def cog_load(self) -> None:
        if not self.current_war_info:
            self.current_war_info = WarInfo()
        if not self.dispatch_check.is_running():
            self.dispatch_check.start()
            self.bot.loops.append(self.dispatch_check)

    def cog_unload(self) -> None:
        if self.dispatch_check.is_running():
            self.dispatch_check.stop()
            if self.dispatch_check in self.bot.loops:
                self.bot.loops.remove(self.dispatch_check)

    @tasks.loop(minutes=1)
    async def dispatch_check(self) -> None:
        dispatch_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or dispatch_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        if not self.current_war_info.dispatch_id:
            await self.bot.channels.moderator_channel.send(
                "# No dispatch ID found in the database. Please check the war info table."
            )
            return
        for index, dispatch in enumerate(self.bot.data.dispatches["en"]):
            if self.current_war_info.dispatch_id < dispatch.id:
                if len(dispatch.full_message) < 5 or "#planet" in dispatch.full_message:
                    self.current_war_info.dispatch_id = dispatch.id
                    self.current_war_info.save_changes()
                    continue
                unique_langs = GWWGuilds.unique_languages()
                containers = {
                    lang: [
                        DispatchContainer(
                            dispatch_json=self.bot.json_dict["languages"][lang][
                                "containers"
                            ]["DispatchContainer"],
                            dispatch=self.bot.data.dispatches[lang][index],
                        )
                    ]
                    for lang in unique_langs
                }
                await self.bot.interface_handler.send_feature(
                    feature_type="war_announcements",
                    content=containers,
                    announcement_type="dispatch",
                )
                self.current_war_info.dispatch_id = dispatch.id
                self.current_war_info.save_changes()
                self.bot.logger.info(
                    f"Sent dispatch out to {len(self.bot.interface_handler.war_announcements)} channels in {(datetime.now() - dispatch_start).total_seconds():.2f}s"
                )
                return

    @dispatch_check.before_loop
    async def before_dispatch_check(self) -> None:
        await self.bot.wait_until_ready()

    async def dispatch_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.data.loaded:
            return []
        dispatch_list = sorted(
            [f"{i.id}-{i.title}"[:90] for i in inter.bot.data.dispatches["en"]],
            reverse=True,
        )
        return [d for d in dispatch_list if str(user_input).lower() in str(d).lower()][
            :25
        ]

    @wait_for_startup()
    @commands.slash_command(
        description="Get the 25 most recent dispatches or a specific dispatch",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the 25 latest dispatches with a dropdown to select other ones via id-title.",
            "example_usage": "**`/dispatches public:Yes`** returns an embed with the most recent patch notes, it also has a dropdown for the most recent 10 patch notes you can choose from. Other people can see this too.",
        },
    )
    async def dispatches(
        self,
        inter: AppCmdInter,
        specific: str = commands.Param(
            autocomplete=dispatch_autocomp,
            default=None,
            description="Get a specific dispatch by ID",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ) -> None:
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except HTTPException:
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{specific = }> <{public = }>"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        dispatch = None
        if specific:
            try:
                disp_id = int(specific.split("-")[0])
            except ValueError:
                await inter.send(
                    f"The ID you supplied (`{specific}`) is in the incorrect format. Please choose a dispatch from the list."
                )
                return
            specific_dispatch_list = [
                d for d in self.bot.data.dispatches[guild.language] if d.id == disp_id
            ]
            if specific_dispatch_list != []:
                dispatch = specific_dispatch_list[0]
        else:
            dispatch = self.bot.data.dispatches[guild.language][-1]
        if not dispatch:
            await inter.send("I couldn't find that dispatch, sorry.", ephemeral=True)
            return
        await inter.send(
            components=[
                DispatchContainer(
                    dispatch_json=self.bot.json_dict["languages"][guild.language][
                        "containers"
                    ]["DispatchContainer"],
                    dispatch=dispatch,
                    with_time=True,
                ),
                DispatchStringSelect(self.bot.data.dispatches[guild.language]),
            ],
            ephemeral=public != "Yes",
        )

    @commands.Cog.listener("on_dropdown")
    async def dispatches_listener(self, inter: MessageInteraction) -> None:
        if (
            inter.component.custom_id != "dispatch"
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        dispatch = [
            d
            for d in self.bot.data.dispatches[guild.language]
            if d.id == int(inter.values[0].split("-")[0])
        ][0]
        container = DispatchContainer(
            dispatch_json=self.bot.json_dict["languages"][guild.language]["containers"][
                "DispatchContainer"
            ],
            dispatch=dispatch,
            with_time=True,
        )
        await inter.response.edit_message(
            components=[
                container,
                DispatchStringSelect(self.bot.data.dispatches[guild.language]),
            ]
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(DispatchesCog(bot))
