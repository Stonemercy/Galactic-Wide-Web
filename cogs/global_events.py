from datetime import datetime
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Embed,
    HTTPException,
    InteractionContextTypes,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import GlobalEventCommandContainer, GlobalEventsContainer
from utils.dbv2 import GWWGuild, GWWGuilds


class GlobalEventsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        if not self.global_event_check.is_running():
            self.global_event_check.start()
            self.bot.loops.append(self.global_event_check)

    def cog_unload(self) -> None:
        if self.global_event_check.is_running():
            self.global_event_check.stop()
        if self.global_event_check in self.bot.loops:
            self.bot.loops.remove(self.global_event_check)

    @tasks.loop(minutes=1)
    async def global_event_check(self) -> None:
        ge_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or ge_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.formatted_data.global_events["en"]
        ):
            return
        for index, global_event in enumerate(
            self.bot.data.formatted_data.global_events["en"]
        ):
            if global_event.id > self.bot.databases.war_info.global_event_id:
                if (
                    global_event.assignment_id != 0
                    or all(
                        [
                            not global_event.title,
                            not global_event.message,
                            not global_event.effects,
                        ]
                    )
                    or "BRIEFING" in global_event.title.upper()
                ):
                    self.bot.databases.war_info.global_event_id = global_event.id
                    self.bot.databases.war_info.save_changes()
                    continue
                unique_langs = GWWGuilds.unique_languages()
                containers = {
                    lang: [
                        GlobalEventsContainer(
                            long_lang_code=self.bot.json_dict["languages"][lang][
                                "code_long"
                            ],
                            container_json=self.bot.json_dict["languages"][lang][
                                "containers"
                            ]["GlobalEventsContainer"],
                            global_event=self.bot.data.formatted_data.global_events[
                                lang
                            ][index],
                            planets=self.bot.data.formatted_data.planets,
                        )
                    ]
                    for lang in unique_langs
                }
                await self.bot.interface_handler.send_feature(
                    feature_type="detailed_dispatches", content=containers
                )
                self.bot.databases.war_info.global_event_id = global_event.id
                self.bot.databases.war_info.save_changes()
                self.bot.logger.info(
                    f"Sent Global Event out to {len(self.bot.interface_handler.detailed_dispatches)} channels in {(datetime.now() - ge_start).total_seconds():.2f}s"
                )
                break

    @global_event_check.before_loop
    async def before_ge_check(self) -> None:
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="[WIP] Returns information on the current global event(s) - if available.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "[WIP] Returns information on the current Global Event(s) if any are active",
            "example_usage": "**`/global_events public:Yes`** would return information on the current Global Events that other members in the server can see.",
        },
    )
    async def global_events(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
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
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
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
        # guild_language = self.bot.json_dict["languages"][guild.language] TODO
        containers = []
        for global_event in sorted(
            self.bot.data.formatted_data.global_events[guild.language],
            key=lambda x: x.expire_time,
        ):
            if global_event.assignment_id:
                continue
            container = GlobalEventCommandContainer(
                global_event=global_event, planets=self.bot.data.formatted_data.planets
            )
            containers.append(container)
        if not containers:
            await inter.send("No global events active")
            return
        await inter.send(
            components=containers,
            ephemeral=public != "Yes",
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(GlobalEventsCog(bot))
