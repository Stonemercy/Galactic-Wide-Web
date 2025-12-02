from datetime import datetime, time
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    HTTPException,
    InteractionContextTypes,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from typing import TYPE_CHECKING
from utils.checks import wait_for_startup
from utils.containers import MOUnavailableContainer
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import Dashboard
from utils.interactables import WikiButton

if TYPE_CHECKING:
    from utils.data import GlobalEvent


class MajorOrderCog(commands.Cog):
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
                loop.stop()
                if loop in self.bot.loops:
                    self.bot.loops.remove(loop)

    @tasks.loop(minutes=1)
    async def major_order_check(self) -> None:
        mo_check_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or mo_check_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.assignments["en"]
        ):
            return
        if self.bot.databases.war_info.major_order_ids == None:
            await self.bot.channels.moderator_channel.send(
                "# Major Order entry has not been initialized with an empty array. Please check the war info table."
            )
            return
        unique_langs = GWWGuilds.unique_languages()
        for index, major_order in enumerate(self.bot.data.assignments["en"]):
            if major_order.id not in self.bot.databases.war_info.major_order_ids:
                mo_briefing_dict = {
                    lang.short_code: ge
                    for lang in [
                        l for l in Languages.all if l.short_code in unique_langs
                    ]
                    for ge in self.bot.data.global_events[lang.short_code]
                    if ge.assignment_id == major_order.id
                    and "" not in (ge.title, ge.message)
                }
                if not mo_briefing_dict:
                    if major_order.id in self.mo_briefing_check_dict:
                        self.mo_briefing_check_dict[major_order.id] += 1
                    else:
                        self.mo_briefing_check_dict[major_order.id] = 1
                    if self.mo_briefing_check_dict[major_order.id] < 5:
                        self.bot.logger.info(
                            f"MO briefing not available for assignment #{major_order.id} - Check #{self.mo_briefing_check_dict[major_order.id]}"
                        )
                        return
                self.mo_briefing_check_dict.pop(major_order.id, None)
                unique_langs = GWWGuilds.unique_languages()
                embeds = {
                    lang: [
                        Dashboard.MajorOrderEmbed(
                            assignment=self.bot.data.assignments[lang][index],
                            planets=self.bot.data.planets,
                            gambit_planets=self.bot.data.gambit_planets,
                            language_json=self.bot.json_dict["languages"][lang],
                            json_dict=self.bot.json_dict,
                        )
                    ]
                    for lang in unique_langs
                }
                for lang, embed_list in embeds.items():
                    briefing: GlobalEvent = mo_briefing_dict.get(lang, None)
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
                    f"Sent MO announcements out to {len(self.bot.interface_handler.major_order_updates)} channels in {(datetime.now() - mo_check_start).total_seconds():.2f}s"
                )

        # check for old MO IDs that are no longer active
        current_mo_ids = [mo.id for mo in self.bot.data.assignments["en"]]
        for active_id in self.bot.databases.war_info.major_order_ids.copy():
            if active_id not in current_mo_ids:
                self.bot.databases.war_info.major_order_ids.remove(active_id)
                self.bot.databases.war_info.save_changes()

    @major_order_check.before_loop
    async def before_mo_check(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=6, minute=20, second=30), time(hour=18, minute=20, second=30)]
    )
    async def major_order_updates(self):
        mo_updates_start = datetime.now()
        self.bot.logger.info(f"MO loop starting at {mo_updates_start}")
        if (
            self.last_mo_update
            and (mo_updates_start - self.last_mo_update).total_seconds() < 600
        ):
            self.bot.logger.info(f"Skipping duplicate MO loop execution")
            return
        self.last_mo_update = mo_updates_start
        if (
            not self.bot.interface_handler.loaded
            or mo_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.data.assignments["en"]
        ):
            return
        unique_langs = GWWGuilds.unique_languages()
        embeds = {
            lang: [
                Dashboard.MajorOrderEmbed(
                    assignment=major_order,
                    planets=self.bot.data.planets,
                    gambit_planets=self.bot.data.gambit_planets,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                )
                for major_order in self.bot.data.assignments[lang]
            ]
            for lang in unique_langs
        }
        await self.bot.interface_handler.send_feature(
            feature_type="major_order_updates",
            content=embeds,
            announcement_type="MO",
        )
        self.bot.logger.info(
            f"Sent MO announcements out to {len(self.bot.interface_handler.major_order_updates)} channels in {(datetime.now() - mo_updates_start).total_seconds():.2f}s"
        )

    @major_order_updates.before_loop
    async def before_major_order_updates(self) -> None:
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on the current major order(s) - if available.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns information on the current Major Order(s) and other assignments from High Command",
            "example_usage": "**`/major_order public:Yes`** would return information on the current Major Order that other members in the server can see.",
        },
    )
    async def major_order(
        self,
        inter: AppCmdInter,
        with_announcement: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the large briefing to be attached.",
        ),
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
            f"{self.qualified_name} | /{inter.application_command.name} <{with_announcement = }> <{public = }>"
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
        guild_language = self.bot.json_dict["languages"][guild.language]
        if self.bot.data.assignments["en"]:
            embeds = []
            for assignment in self.bot.data.assignments[guild.language]:
                embed = Dashboard.MajorOrderEmbed(
                    assignment=assignment,
                    planets=self.bot.data.planets,
                    gambit_planets=self.bot.data.gambit_planets,
                    language_json=guild_language,
                    json_dict=self.bot.json_dict,
                )
                if with_announcement == "Yes":
                    briefings_list: list[GlobalEvent] = [
                        ge
                        for ge in self.bot.data.global_events[guild.language]
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
