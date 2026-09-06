from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    File,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, Param, slash_command
from os import listdir
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import WarbondsContainer


class WarbondsCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.usable_images = listdir(path="resources/warbonds")

    @wait_for_startup()
    @slash_command(
        description="Returns active Warbonds, if available.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns active Warbonds, if available.",
            "example_usage": "**`/warbonds public:Yes`** returns a container Warbond contents, buttons to change page, and a dropdown to select a different warbond. It can also be seen by others in discord.",
        },
    )
    async def warbonds(
        self,
        inter: AppCmdInter,
        public: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        if self.bot.data.formatted_data is None:
            await inter.send(
                content="A **Fatal Error** has occurred\nApologies for the inconvenience.",
                ephemeral=True,
            )
            return
        if self.bot.data.formatted_data.warbonds is None:
            await inter.send(
                content="Warbonds unavailable.\nApologies for the inconvenience.",
                ephemeral=True,
            )
            return
        warbond_file_name = f"{next((wb for wb in list(self.bot.data.formatted_data.warbonds.values())[::-1])).id}.png"
        with_banner = False
        if warbond_file_name in self.usable_images:
            with_banner = True
        container = WarbondsContainer(
            warbonds=self.bot.data.formatted_data.warbonds,
            with_banner=with_banner,
        )
        if with_banner:
            await inter.send(
                file=File("resources/warbonds/" + warbond_file_name),
                components=container,
                ephemeral=public != "Yes",
            )
        else:
            await inter.send(components=container, ephemeral=public != "Yes")

    @Cog.listener("on_dropdown")
    async def superstore_dropdown_listener(self, inter: MessageInteraction) -> None:
        if "warbond_dropdown" not in inter.component.custom_id:
            return
        if inter.author != inter.message.interaction_metadata.user:
            await self.bot.not_interaction_author(inter)
            return
        if not self.bot.ready:
            await self.bot.bot_not_ready(inter)
            return
        await inter.response.defer()
        warbond_id = int(inter.values[0])
        warbond_file_name = f"{warbond_id}.png"
        with_banner = False
        if warbond_file_name in self.usable_images:
            with_banner = True
        container = WarbondsContainer(
            self.bot.data.formatted_data.warbonds, with_banner, warbond_id
        )
        if with_banner:
            await inter.edit_original_response(
                file=File("resources/warbonds/" + warbond_file_name),
                components=container,
            )
        else:
            await inter.edit_original_response(components=container)

    @Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction) -> None:
        if "warbonds_button" not in inter.component.custom_id:
            return
        if inter.author != inter.message.interaction_metadata.user:
            await self.bot.not_interaction_author(inter)
            return
        if not self.bot.ready:
            await self.bot.bot_not_ready(inter)
            return
        await inter.response.defer()
        warbond_id, page_index = [
            int(i) for i in inter.component.custom_id.split("_")[2:]
        ]
        warbond_file_name = f"{warbond_id}.png"
        with_banner = False
        if warbond_file_name in self.usable_images:
            with_banner = True
        container = WarbondsContainer(
            self.bot.data.formatted_data.warbonds, with_banner, warbond_id, page_index
        )
        if with_banner:
            await inter.edit_original_response(
                file=File("resources/warbonds/" + warbond_file_name),
                components=container,
            )
        else:
            await inter.edit_original_response(components=container)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(WarbondsCog(bot))
