from datetime import datetime, time, timezone
from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext.commands import Cog, Param, slash_command
from disnake.ext.tasks import loop
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuilds
from utils.embeds import PersonalOrderCommandEmbed


class PersonalOrderCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.last_po_update: None | datetime = None

    def cog_load(self) -> None:
        if not self.personal_order_updates.is_running():
            self.personal_order_updates.start()
            self.bot.loops.append(self.personal_order_updates)

    def cog_unload(self) -> None:
        if self.personal_order_updates.is_running():
            self.personal_order_updates.cancel()
        if self.personal_order_updates in self.bot.loops:
            self.bot.loops.remove(self.personal_order_updates)

    @loop(time=[time(hour=9, minute=35)])
    async def personal_order_updates(self):
        po_updates_start = datetime.now(tz=timezone.utc)
        if (
            self.last_po_update
            and (po_updates_start - self.last_po_update).total_seconds() < 600
        ):
            self.bot.logger.info(
                f"personal_order_updates loop - skipping duplicate loop execution"
            )
            return
        self.last_po_update = po_updates_start
        if not self.bot.ready:
            self.bot.logger.warning(
                "personal_order_updates loop returning - the bot isn't ready"
            )
            return
        if not self.bot.data.formatted_data.personal_order:
            self.bot.logger.warning(
                "personal_order_updates loop returning - personal order is missing"
            )
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
            f"personal_order_updates - sent PO {self.bot.data.formatted_data.personal_order.id} announcement out to {len(self.bot.interface_handler.personal_order_updates)} channels in {(datetime.now(tz=timezone.utc) - po_updates_start).total_seconds():.2f} seconds"
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
    @slash_command(
        description="Get the current Personal Order (if available)",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows the current Personal Order if one is active (and the data is available).",
            "example_usage": "**`/personal_order public:Yes`** returns the current Personal Order, visible to everyone in the channel.",
        },
    )
    async def personal_order(
        self,
        inter: AppCmdInter,
        public: str = Param(
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
