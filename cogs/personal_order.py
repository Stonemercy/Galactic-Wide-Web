from datetime import datetime, time
from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuilds
from utils.embeds.personal_order_embed import PersonalOrderCommandEmbed


class PersonalOrderCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.last_po_update: None | datetime = None

    def cog_load(self) -> None:
        if not self.personal_order_updates.is_running():
            self.personal_order_updates.start()
            self.bot.loops.append(self.personal_order_updates)

    def cog_unload(self) -> None:
        if self.personal_order_updates.is_running():
            self.personal_order_updates.stop()
        if self.personal_order_updates in self.bot.loops:
            self.bot.loops.remove(self.personal_order_updates)

    @tasks.loop(time=[time(hour=9, minute=30)])
    async def personal_order_updates(self):
        po_updates_start = datetime.now()
        self.bot.logger.info(f"PO loop starting at {po_updates_start}")
        if (
            self.last_po_update
            and (po_updates_start - self.last_po_update).total_seconds() < 600
        ):
            self.bot.logger.info(f"Skipping duplicate PO loop execution")
            return
        self.last_po_update = po_updates_start
        if (
            not self.bot.interface_handler.loaded
            or po_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.data.formatted_data.personal_order
        ):
            return
        unique_langs = GWWGuilds.unique_languages()
        embeds = {
            lang: [
                PersonalOrderCommandEmbed(
                    personal_order=self.bot.data.formatted_data.personal_order,
                    json_dict=self.bot.json_dict,
                )
            ]
            for lang in unique_langs
        }
        await self.bot.interface_handler.send_feature(
            feature_type="personal_order_updates",
            content=embeds,
            announcement_type="PO",
        )
        self.bot.logger.info(
            f"Sent PO announcements out to {len(self.bot.interface_handler.personal_order_updates)} channels in {(datetime.now() - po_updates_start).total_seconds():.2f}s"
        )

    @personal_order_updates.before_loop
    async def before_po_updates(self) -> None:
        await self.bot.wait_until_ready()

    @personal_order_updates.error
    async def personal_order_updates_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "personal_order_updates loop")

    @wait_for_startup()
    @commands.slash_command(
        description="Get the current Personal Order",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the current Personal Order, if available.",
            "example_usage": "**`/personal_order public:Yes`** returns an embed with the current Personal Order. Other people can see this too.",
        },
    )
    async def personal_order(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        if not self.bot.data.formatted_data.personal_order:
            await inter.send(
                "Personal order unavailable. Apologies for the inconvenience",
                ephemeral=public != "Yes",
            )
        else:
            await inter.send(
                embed=PersonalOrderCommandEmbed(
                    personal_order=self.bot.data.formatted_data.personal_order,
                    json_dict=self.bot.json_dict,
                ),
                ephemeral=public != "Yes",
            )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(PersonalOrderCog(bot))
