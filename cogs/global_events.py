from datetime import datetime
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.containers import GlobalEventsContainer
from utils.dbv2 import GWWGuilds, WarInfo


class GlobalEventsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        if not self.global_event_check.is_running():
            self.global_event_check.start()
            self.bot.loops.append(self.global_event_check)

    def cog_unload(self):
        if self.global_event_check.is_running():
            self.global_event_check.stop()
            if self.global_event_check in self.bot.loops:
                self.bot.loops.remove(self.global_event_check)

    @tasks.loop(minutes=1)
    async def global_event_check(self):
        ge_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or ge_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.global_events["en"]
        ):
            return
        current_war_info = WarInfo()
        for index, global_event in enumerate(self.bot.data.global_events["en"]):
            if global_event.id > current_war_info.global_event_id:
                if (
                    global_event.assignment_id != 0
                    or all(
                        [
                            not global_event.title,
                            not global_event.message,
                            not global_event.effects,
                        ]
                    )
                    or global_event.title.upper() == "BRIEFING"
                ):
                    current_war_info.global_event_id = global_event.id
                    current_war_info.save_changes()
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
                            global_event=self.bot.data.global_events[lang][index],
                            planets=self.bot.data.planets,
                        )
                    ]
                    for lang in unique_langs
                }
                current_war_info.global_event_id = global_event.id
                current_war_info.save_changes()
                await self.bot.interface_handler.send_feature(
                    feature_type="detailed_dispatches", content=containers
                )
                self.bot.logger.info(
                    f"Sent Global Event out to {len(self.bot.interface_handler.detailed_dispatches)} channels in {(datetime.now() - ge_start).total_seconds():.2f}s"
                )
                break

    @global_event_check.before_loop
    async def before_ge_check(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(GlobalEventsCog(bot))
