from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    File,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, Param, slash_command
from os import listdir
from utils.api_wrapper.models import Superstore
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import SuperstoreContainer


class SuperstoreCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.usable_images = (
            listdir(path="resources/warbonds")
            + listdir(path="resources/emotes")
            + listdir(path="resources/player_cards")
        )

    @wait_for_startup()
    @slash_command(
        description="Returns active Superstore pages, if available.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the active Superstore pages, if available.",
            "example_usage": "**`/superstore public:Yes`** returns a container with Superstore contents and a dropdown to select the page. It can also be seen by others in discord.",
        },
    )
    async def superstore(
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
                content="A **Fatal Error** has occurred\nApologies for the inconvenience."
            )
            return
        if self.bot.data.formatted_data.superstore is None:
            await inter.send(
                content="Superstore unavailable.\nApologies for the inconvenience."
            )
            return
        container = SuperstoreContainer(
            superstore=self.bot.data.formatted_data.superstore,
            usable_images=self.usable_images,
        )
        files = self.get_files_for_page(page=container.page)
        if files != []:
            await inter.send(files=files, components=container)
        else:
            await inter.send(components=container)

    @Cog.listener("on_dropdown")
    async def superstore_dropdown_listener(self, inter: MessageInteraction) -> None:
        if (
            not self.bot.ready
            or inter.component.custom_id != "superstore_page"
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        await inter.response.defer()
        container = SuperstoreContainer(
            self.bot.data.formatted_data.superstore,
            self.usable_images,
            page_id=int(inter.values[0]),
        )
        files = self.get_files_for_page(page=container.page)
        if files != []:
            await inter.edit_original_response(files=files, components=container)
        else:
            await inter.edit_original_response(components=container)

    def get_files_for_page(self, page: Superstore.Page) -> list[File]:
        files = []
        for i in [j for j in page.items if j.type == "Emote"]:
            if f"{i.id}.png" in self.usable_images:
                files.append(File(f"resources/emotes/{i.id}.png"))
        for i in [j for j in page.items if j.type == "Player Card"]:
            if f"{i.id}.png" in self.usable_images:
                files.append(File(f"resources/player_cards/{i.id}.png"))
        if f"{page.banner_image_id}.png" in self.usable_images:
            files.append(File(f"resources/warbonds/{page.banner_image_id}.png"))
        return files


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(SuperstoreCog(bot))
