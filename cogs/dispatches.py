from datetime import datetime, timedelta, timezone
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, Param, slash_command
from disnake.ext.tasks import loop
from utils.bot import GalacticWideWebBot
from utils.containers import DispatchContainer
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuilds
from utils.interactables import DispatchStringSelect


class DispatchesCog(Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    def cog_load(self) -> None:
        if not self.dispatch_check.is_running():
            self.dispatch_check.start()
            self.bot.loops.append(self.dispatch_check)

    def cog_unload(self) -> None:
        if self.dispatch_check.is_running():
            self.dispatch_check.cancel()
        if self.dispatch_check in self.bot.loops:
            self.bot.loops.remove(self.dispatch_check)

    @loop(minutes=1)
    async def dispatch_check(self) -> None:
        dispatch_start = datetime.now(tz=timezone.utc)
        if not self.bot.ready:
            self.bot.logger.warning(
                "dispatch_check loop returning - the bot isn't ready"
            )
            return
        if self.bot.interface_handler.busy:
            self.bot.logger.warning(
                "dispatch_check loop returning - the interface_handler is busy"
            )
            return
        if not self.bot.data.formatted_data:
            self.bot.logger.error("dispatch_check loop returning - NO FORMATTED DATA")
            return
        if english_dispatches := self.bot.data.formatted_data.dispatches.get("en"):
            fifteen_minutes_ago = datetime.now(tz=timezone.utc) - timedelta(minutes=15)
            for index, dispatch in enumerate(english_dispatches):
                if self.bot.databases.war_info.dispatch_id < dispatch.id:
                    faulty_dispatch = False
                    if len(dispatch.full_message) < 5:
                        self.bot.logger.warning(
                            f"dispatch_check loop - dispatch {dispatch.id} full message length is {len(dispatch.full_message)}"
                        )
                        if dispatch.published_at < fifteen_minutes_ago:
                            faulty_dispatch = True
                        else:
                            return
                    elif "#planet" in dispatch.full_message:
                        self.bot.logger.warning(
                            f"dispatch_check loop - dispatch {dispatch.id} has #planet in message"
                        )
                        if dispatch.published_at < fifteen_minutes_ago:
                            faulty_dispatch = True
                        else:
                            return
                    if faulty_dispatch:
                        self.bot.logger.error(
                            f"dispatch_check loop - dispatch {dispatch.id} has been faulty for 15 minutes, skipping"
                        )
                        self.bot.databases.war_info.dispatch_id = dispatch.id
                        self.bot.databases.war_info.save_changes()
                        continue
                    unique_langs = GWWGuilds.unique_languages()
                    containers = {
                        lang: [
                            DispatchContainer(
                                dispatch_json=self.bot.json_dict["languages"][lang][
                                    "containers"
                                ]["DispatchContainer"],
                                dispatch=self.bot.data.formatted_data.dispatches.get(
                                    lang,
                                    self.bot.data.formatted_data.dispatches.get(
                                        "en", []
                                    ),
                                )[index],
                            )
                        ]
                        for lang in unique_langs
                    }
                    await self.bot.interface_handler.send_feature(
                        feature_type="war_announcements",
                        content=containers,
                        announcement_type="dispatch",
                    )
                    self.bot.databases.war_info.dispatch_id = dispatch.id
                    self.bot.databases.war_info.save_changes()
                    self.bot.logger.info(
                        f"dispatch_check loop - sent dispatch #{dispatch.id} out to {len(self.bot.interface_handler.war_announcements)} channels in {(datetime.now(tz=timezone.utc) - dispatch_start).total_seconds():.2f} seconds"
                    )
                    return

    @dispatch_check.before_loop
    async def before_dispatch_check(self) -> None:
        await self.bot.wait_until_ready()

    @dispatch_check.error
    async def dispatch_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "dispatch_check loop")

    async def dispatch_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.ready:
            return []
        return [
            d
            for d in sorted(
                [
                    f"{i.id}-{i.title}"[:90]
                    for i in inter.bot.data.formatted_data.dispatches.get("en", [])
                ],
                reverse=True,
            )
            if str(user_input).lower() in str(d).lower()
        ][:25]

    @wait_for_startup()
    @slash_command(
        description="Get the most recent dispatch, or search for a specific one",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows the most recent in-game dispatch by default. Use the `specific` option with autocomplete to look up a particular dispatch by ID and title. Includes a dropdown to switch between the 25 most recent dispatches.",
            "example_usage": "**`/dispatches public:Yes`** returns the latest dispatch visible to everyone.\n- **`/dispatches specific:1234-Title public:No`** returns that specific dispatch just for you.",
        },
    )
    async def dispatches(
        self,
        inter: AppCmdInter,
        specific: str = Param(
            autocomplete=dispatch_autocomp,
            default=None,
            description="Get a specific dispatch by ID",
        ),
        public: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        guild = self.bot.get_guild_from_inter(inter=inter)
        dispatch = None
        if specific is not None:
            try:
                disp_id = int(specific.split("-")[0])
            except ValueError:
                await inter.send(
                    f"The ID you supplied (`{specific}`) is in the incorrect format. Please choose a dispatch from the list."
                )
                return
            dispatch = next(
                (
                    d
                    for d in self.bot.data.formatted_data.dispatches.get(
                        guild.language,
                        self.bot.data.formatted_data.dispatches.get("en", []),
                    )
                    if d.id == disp_id
                ),
                None,
            )
        else:
            dispatch = self.bot.data.formatted_data.dispatches.get(
                guild.language, self.bot.data.formatted_data.dispatches.get("en", [])
            )[-1]
        if dispatch is None:
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
                DispatchStringSelect(
                    self.bot.data.formatted_data.dispatches.get(
                        guild.language,
                        self.bot.data.formatted_data.dispatches.get("en", []),
                    )
                ),
            ],
            ephemeral=public != "Yes",
        )

    @Cog.listener("on_dropdown")
    async def dispatches_listener(self, inter: MessageInteraction) -> None:
        if (
            not self.bot.ready
            or inter.component.custom_id != "dispatch"
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        guild = self.bot.get_guild_from_inter(inter=inter)
        dispatch = [
            d
            for d in self.bot.data.formatted_data.dispatches.get(
                guild.language, self.bot.data.formatted_data.dispatches.get("en", [])
            )
            if d.id == int(inter.values[0])
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
                DispatchStringSelect(
                    self.bot.data.formatted_data.dispatches.get(
                        guild.language,
                        self.bot.data.formatted_data.dispatches.get("en", []),
                    )
                ),
            ]
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(DispatchesCog(bot))
