from datetime import datetime, time
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.dbv2 import WarInfo, GWWGuilds
from utils.embeds.dashboard import Dashboard
from utils.embeds.loop_embeds import (
    DispatchesLoopEmbed,
    GlobalEventsLoopEmbed,
    SteamLoopEmbed,
)


class AnnouncementsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.loops = (
            self.major_order_check,
            self.global_event_check,
            self.dispatch_check,
            self.steam_check,
            self.major_order_updates,
        )
        for loop in self.loops:
            if not loop.is_running():
                loop.start()
                self.bot.loops.append(loop)

    def cog_unload(self):
        for loop in self.loops:
            if loop.is_running():
                loop.stop()

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        announcement_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or announcement_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.assignments
        ):
            return
        current_war_info = WarInfo()
        if current_war_info.major_order_ids == None:
            await self.bot.moderator_channel.send(
                "# No major order IDs found in the database. Please check the war info table."
            )
            return
        for major_order in self.bot.data.assignments:
            if major_order.id not in current_war_info.major_order_ids:
                unique_langs = GWWGuilds().unique_languages
                embeds = {
                    lang: [
                        Dashboard.MajorOrderEmbed(
                            assignment=major_order,
                            planets=self.bot.data.planets,
                            liberation_changes_tracker=self.bot.data.liberation_changes,
                            mo_task_tracker=self.bot.data.major_order_changes,
                            language_json=self.bot.json_dict["languages"][lang],
                            json_dict=self.bot.json_dict,
                            with_health_bars=True,
                        )
                    ]
                    for lang in unique_langs
                }
                mo_briefing = [
                    ge
                    for ge in self.bot.data.global_events
                    if ge.assignment_id == major_order.id
                    and ge.title != ""
                    and ge.message != ""
                ]
                if mo_briefing:
                    mo_briefing = mo_briefing[0]
                    for embed_list in embeds.values():
                        for embed in embed_list:
                            embed.insert_field_at(
                                0,
                                mo_briefing.title,
                                mo_briefing.split_message[0],
                                inline=False,
                            )
                            for index, chunk in enumerate(
                                mo_briefing.split_message[1:], 1
                            ):
                                embed.insert_field_at(index, "", chunk, inline=False)
                else:
                    self.bot.logger.info(
                        f"MO briefing not available for assignment {major_order.id}"
                    )
                current_war_info.major_order_ids.append(major_order.id)
                current_war_info.save_changes()
                await self.bot.interface_handler.send_feature(
                    "war_announcements", embeds, "MO"
                )
                self.bot.logger.info(
                    f"Sent MO announcements out to {len(self.bot.interface_handler.major_order_updates)} channels"
                )
        current_mo_ids = [mo.id for mo in self.bot.data.assignments]
        for active_id in current_war_info.major_order_ids.copy():
            if active_id not in current_mo_ids:
                current_war_info.major_order_ids.remove(active_id)
                current_war_info.save_changes()

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        dispatch_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or dispatch_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        current_war_info = WarInfo()
        if not current_war_info.dispatch_id:
            await self.bot.moderator_channel.send(
                "# No dispatch ID found in the database. Please check the war info table."
            )
            return
        for dispatch in self.bot.data.dispatches:
            if current_war_info.dispatch_id < dispatch.id:
                if len(dispatch.message) < 5:
                    continue
                unique_langs = GWWGuilds().unique_languages
                embeds = {
                    lang: [
                        DispatchesLoopEmbed(
                            self.bot.json_dict["languages"][lang], dispatch
                        )
                    ]
                    for lang in unique_langs
                }
                await self.bot.interface_handler.send_feature(
                    "war_announcements", embeds
                )
                current_war_info.dispatch_id = dispatch.id
                current_war_info.save_changes()
                self.bot.logger.info(
                    f"Sent dispatch out to {len(self.bot.interface_handler.war_announcements)} channels"
                )
                return

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        patch_notes_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or patch_notes_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        current_war_info = WarInfo()
        if current_war_info.patch_notes_id != self.bot.data.steam[0].id:
            unique_langs = GWWGuilds().unique_languages
            embeds = {
                lang: [
                    SteamLoopEmbed(
                        self.bot.data.steam[0], self.bot.json_dict["languages"][lang]
                    )
                ]
                for lang in unique_langs
            }
            await self.bot.interface_handler.send_feature("patch_notes", embeds)
            current_war_info.patch_notes_id = self.bot.data.steam[0].id
            current_war_info.save_changes()
            self.bot.logger.info(
                f"Sent patch announcements out to {len(self.bot.interface_handler.patch_notes)} channels"
            )

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=5, minute=20, second=0), time(hour=17, minute=20, second=0)]
    )
    async def major_order_updates(self):
        mo_updates_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or mo_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.data.assignments
        ):
            return
        unique_langs = GWWGuilds().unique_languages
        embeds = {
            lang: [
                Dashboard.MajorOrderEmbed(
                    assignment=major_order,
                    planets=self.bot.data.planets,
                    liberation_changes_tracker=self.bot.data.liberation_changes,
                    mo_task_tracker=self.bot.data.major_order_changes,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                    with_health_bars=True,
                )
                for major_order in self.bot.data.assignments
            ]
            for lang in unique_langs
        }
        await self.bot.interface_handler.send_feature(
            "major_order_updates", embeds, "MO"
        )
        self.bot.logger.info(
            f"Sent MO announcements out to {len(self.bot.interface_handler.major_order_updates)} channels"
        )

    @major_order_updates.before_loop
    async def before_major_order_updates(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def global_event_check(self):
        ge_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or ge_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.global_events
        ):
            return
        current_war_info = WarInfo()
        for global_event in self.bot.data.global_events:
            if global_event.id > current_war_info.global_event_id:
                if (
                    global_event.assignment_id != 0
                    or all(
                        [
                            not global_event.title,
                            not global_event.message,
                            not global_event.effect_ids,
                        ]
                    )
                    or global_event.title.upper() == "BRIEFING"
                ):
                    current_war_info.global_event_id = global_event.id
                    current_war_info.save_changes()
                    continue
                unique_langs = GWWGuilds().unique_languages
                embeds = {
                    lang: [
                        GlobalEventsLoopEmbed(
                            self.bot.data.planets,
                            self.bot.json_dict["languages"][lang],
                            self.bot.json_dict["planet_effects"],
                            global_event,
                        )
                    ]
                    for lang in unique_langs
                }
                current_war_info.global_event_id = global_event.id
                current_war_info.save_changes()
                await self.bot.interface_handler.send_feature(
                    "detailed_dispatches", embeds
                )
                self.bot.logger.info(
                    f"Sent Global Event out to {len(self.bot.interface_handler.detailed_dispatches)} channels"
                )
                break

    @global_event_check.before_loop
    async def before_ge_check(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AnnouncementsCog(bot))
