from datetime import datetime, time, timezone
from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext.commands import Cog, Param, slash_command
from disnake.ext.tasks import loop
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import MOUnavailableContainer
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import Dashboard
from utils.interactables import WikiButton


class MajorOrderCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.last_mo_update: None | datetime = None
        self.mo_briefing_check_dict = {}
        self.loops = (self.major_order_check, self.major_order_updates)

    def cog_load(self) -> None:
        for loop in self.loops:
            if not loop.is_running():
                loop.start()
                self.bot.loops.append(loop)

    def cog_unload(self) -> None:
        for loop in self.loops:
            if loop.is_running():
                loop.cancel()
            if loop in self.bot.loops:
                self.bot.loops.remove(loop)

    @loop(minutes=1)
    async def major_order_check(self) -> None:
        mo_check_start = datetime.now(tz=timezone.utc)
        if not self.bot.ready:
            self.bot.logger.warning(
                "major_order_check loop returning - the bot isn't ready"
            )
            return
        if self.bot.interface_handler.busy:
            self.bot.logger.warning(
                "major_order_check loop returning - the interface_handler is busy"
            )
            return
        if not self.bot.data.formatted_data:
            self.bot.logger.error(
                "major_order_check loop returning - NO FORMATTED DATA"
            )
            return
        if self.bot.data.formatted_data.assignments.get("en") == None:
            self.bot.logger.warning(
                "major_order_check loop returning - english assignments are missing"
            )
            return
        unique_langs = GWWGuilds.unique_languages()
        for index, major_order in enumerate(
            self.bot.data.formatted_data.assignments.get("en")
        ):
            if major_order.id not in self.bot.databases.war_info.major_order_ids:
                mo_briefing_dict = {
                    lang.short_code: ge
                    for lang in [
                        l for l in Languages.all if l.short_code in unique_langs
                    ]
                    for ge in self.bot.data.formatted_data.global_events[
                        lang.short_code
                    ]
                    if ge.assignment_id == major_order.id
                    and "" not in (ge.title, ge.message)
                }
                if not mo_briefing_dict:
                    if major_order.id in self.mo_briefing_check_dict:
                        self.mo_briefing_check_dict[major_order.id] += 1
                    else:
                        self.mo_briefing_check_dict[major_order.id] = 1
                    if self.mo_briefing_check_dict[major_order.id] < 5:
                        self.bot.logger.warning(
                            f"major_order_check loop - briefing not available for assignment {major_order.id} - Check #{self.mo_briefing_check_dict[major_order.id]}"
                        )
                        return
                self.mo_briefing_check_dict.pop(major_order.id, None)
                unique_langs = GWWGuilds.unique_languages()
                embeds = {
                    lang: [
                        Dashboard.MajorOrderEmbed(
                            assignment=self.bot.data.formatted_data.assignments.get(
                                lang,
                                self.bot.data.formatted_data.assignments.get("en"),
                            )[index],
                            planets=self.bot.data.formatted_data.planets,
                            gambit_planets=self.bot.data.formatted_data.gambit_planets,
                            language_json=self.bot.json_dict["languages"][lang],
                            json_dict=self.bot.json_dict,
                        )
                    ]
                    for lang in unique_langs
                }
                for lang, embed_list in embeds.items():
                    briefing = mo_briefing_dict.get(lang, None)
                    if briefing:
                        for embed in embed_list:
                            embed._add_briefing(briefing=briefing)
                self.bot.databases.war_info.major_order_ids.append(major_order.id)
                self.bot.databases.war_info.save_changes()
                await self.bot.interface_handler.send_feature(
                    feature_type="war_announcements",
                    content=embeds,
                    announcement_type="MO",
                )
                self.bot.logger.info(
                    f"major_order_check loop - sent MO {major_order.id} initial announcement out to {len(self.bot.interface_handler.major_order_updates)} channels in {(datetime.now(tz=timezone.utc) - mo_check_start).total_seconds():.2f} seconds"
                )

        # check for old MO IDs that are no longer active
        current_mo_ids = [
            mo.id for mo in self.bot.data.formatted_data.assignments.get("en", [])
        ]
        for active_id in self.bot.databases.war_info.major_order_ids.copy():
            if active_id not in current_mo_ids:
                self.bot.databases.war_info.major_order_ids.remove(active_id)
                self.bot.databases.war_info.save_changes()
                self.bot.logger.info(
                    f"major_order_check - MO {active_id} no longer active, removed from DB"
                )

    @major_order_check.before_loop
    async def before_mo_check(self) -> None:
        await self.bot.wait_until_ready()

    @major_order_check.error
    async def major_order_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "major_order_check loop")

    @loop(
        time=[time(hour=6, minute=20, second=30), time(hour=18, minute=20, second=30)]
    )
    async def major_order_updates(self):
        mo_updates_start = datetime.now(tz=timezone.utc)
        if (
            self.last_mo_update
            and (mo_updates_start - self.last_mo_update).total_seconds() < 600
        ):
            self.bot.logger.warning(
                f"major_order_updates loop - skipping duplicate loop execution"
            )
            return
        self.last_mo_update = mo_updates_start
        if not self.bot.ready:
            self.bot.logger.warning(
                "major_order_updates returning - the bot isn't ready"
            )
            return
        if self.bot.data.formatted_data.assignments.get("en") == None:
            self.bot.logger.warning(
                "major_order_updates returning - english assignments are missing"
            )
            return
        unique_langs = GWWGuilds.unique_languages()
        embeds = {
            lang: [
                Dashboard.MajorOrderEmbed(
                    assignment=major_order,
                    planets=self.bot.data.formatted_data.planets,
                    gambit_planets=self.bot.data.formatted_data.gambit_planets,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                )
                for major_order in self.bot.data.formatted_data.assignments.get(
                    lang, self.bot.data.formatted_data.assignments.get("en", [])
                )
            ]
            for lang in unique_langs
        }
        await self.bot.interface_handler.send_feature(
            feature_type="major_order_updates",
            content=embeds,
            announcement_type="MO",
        )
        self.bot.logger.info(
            f"major_order_updates loop - sent MO update announcement out to {len(self.bot.interface_handler.major_order_updates)} channels in {(datetime.now(tz=timezone.utc) - mo_updates_start).total_seconds():.2f} seconds"
        )

    @major_order_updates.before_loop
    async def before_major_order_updates(self) -> None:
        await self.bot.wait_until_ready()

    @major_order_updates.error
    async def major_order_updates_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "major_order_updates loop")

    @wait_for_startup()
    @slash_command(
        description="Show the current Major Order(s), if any are active",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows all currently active Major Orders from High Command. Use `with_announcement:Yes` to also attach the MO's briefing text. Includes a link to the wiki.",
            "example_usage": "**`/major_order public:Yes`** returns the current Major Order visible to everyone.\n- **`/major_order with_announcement:Yes`** includes the High Command briefing text alongside the order.",
        },
    )
    async def major_order(
        self,
        inter: AppCmdInter,
        with_announcement: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the large briefing to be attached.",
        ),
        public: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild.id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild.id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild.id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        if (
            assignments := self.bot.data.formatted_data.assignments.get(
                guild.language, self.bot.data.formatted_data.assignments.get("en", [])
            )
        ) != []:
            embeds = []
            for assignment in assignments:
                embed = Dashboard.MajorOrderEmbed(
                    assignment=assignment,
                    planets=self.bot.data.formatted_data.planets,
                    gambit_planets=self.bot.data.formatted_data.gambit_planets,
                    language_json=guild_language,
                    json_dict=self.bot.json_dict,
                )
                if with_announcement == "Yes":
                    briefings_list = [
                        ge
                        for ge in self.bot.data.formatted_data.global_events[
                            guild.language
                        ]
                        if ge.assignment_id == assignment.id
                        and ge.title != ""
                        and ge.message != ""
                    ]
                    if briefings_list != []:
                        briefing = briefings_list[0]
                        embed._add_briefing(briefing)
                embeds.append(embed)

            await inter.send(
                embeds=embeds,
                components=[
                    WikiButton(
                        link=f"https://helldivers.wiki.gg/wiki/Major_Orders#Recent"
                    )
                ],
                ephemeral=public != "Yes",
            )
        else:
            await inter.send(
                components=[MOUnavailableContainer()],
                ephemeral=public != "Yes",
            )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(MajorOrderCog(bot))
