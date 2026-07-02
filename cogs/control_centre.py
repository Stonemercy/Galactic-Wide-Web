from os import listdir
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    File,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, Param, slash_command
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import ControlCentreContainer
from utils.dataclasses.enums import ControlCentrePage
from utils.dbv2 import GWWGuild, GWWGuilds

MAIN_BUTTONS = [
    "overview_button",
    "active_campaign_button",
    "past_campaigns_button",
]


class ControlCentreCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.usable_images = listdir("resources/news_images")

    @wait_for_startup()
    @slash_command(
        description="Check the status of the in-game Control Centre",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows the in-game Control Centre. You can use the buttons and dropdowns to navigate.",
            "example_usage": "**`/control_centre public:Yes`** returns the current Control Centre, visible to everyone.",
        },
    )
    async def control_centre(
        self,
        inter: AppCmdInter,
        public: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
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
        if not self.bot.data.formatted_data.control_centre.get(guild.language):
            await inter.send("Control Centre unavailable")
            return

        cc = self.bot.data.formatted_data.control_centre.get(guild.language)
        images_required = [
            f"{i}.png"
            for i in cc.images_required(episode_id=cc.episodes[-1].id, phase_id=0)
            if f"{i}.png" in self.usable_images
        ]
        print(len(images_required))
        container = ControlCentreContainer(
            control_centre=cc,
            required_images=images_required,
            dispatches=self.bot.data.formatted_data.dispatches.get(guild.language, []),
            page=ControlCentrePage.Overview,
        )
        await inter.send(
            components=container,
            files=[
                File(f"resources/news_images/{i}")
                for i in images_required
                if i in self.usable_images
            ],
        )

    @Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction) -> None:
        if (
            not self.bot.ready
            or inter.author != inter.message.interaction_metadata.user
            or inter.component.custom_id not in MAIN_BUTTONS
            and "control_centre" not in inter.component.custom_id
        ):
            return
        await inter.response.defer()
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild.id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild.id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild.id, "en", [])
        else:
            guild = GWWGuild.default()

        if inter.component.custom_id in MAIN_BUTTONS:
            page = ControlCentrePage[
                "".join(
                    inter.component.custom_id.replace("_", " ").title().split(" ")[:-1]
                )
            ]
            cc = self.bot.data.formatted_data.control_centre.get(guild.language)
            episode_id = None
            phase_id = None
            need_episode = True
            match page:
                case ControlCentrePage.Overview:
                    episode_id = cc.episodes[-1].id
                    phase_id = 0
                case ControlCentrePage.ActiveCampaign:
                    episode_id = cc.episodes[-1].id
                    need_episode = False
                    phase_id = cc.episodes[-1].phases[-1].id
                case ControlCentrePage.PastCampaigns:
                    phase_id = 0
            images_required = [
                f"{i}.png"
                for i in cc.images_required(
                    episode_id=episode_id,
                    need_episode=need_episode,
                    phase_id=phase_id,
                )
                if f"{i}.png" in self.usable_images
            ]
            if page == ControlCentrePage.PastCampaigns:
                try:
                    images_required.remove(f"{cc.episodes[-1].image_id}.png")
                except:
                    pass
            container = ControlCentreContainer(
                control_centre=cc,
                required_images=images_required,
                dispatches=self.bot.data.formatted_data.dispatches.get(
                    guild.language, []
                ),
                page=page,
            )
            await inter.edit_original_response(
                components=container,
                files=[
                    File(f"resources/news_images/{i}")
                    for i in images_required
                    if i in self.usable_images
                ],
            )
        else:
            episode_id = int(inter.component.custom_id.split("_")[-1])
            cc = self.bot.data.formatted_data.control_centre.get(guild.language)
            phase_id = (
                next((e for e in cc.episodes if e.id == episode_id)).phases[-1].id
            )
            images_required = [
                f"{i}.png"
                for i in cc.images_required(
                    episode_id=episode_id, need_episode=False, phase_id=phase_id
                )
                if f"{i}.png" in self.usable_images
            ]
            container = ControlCentreContainer(
                control_centre=cc,
                required_images=images_required,
                dispatches=self.bot.data.formatted_data.dispatches.get(
                    guild.language, []
                ),
                page=ControlCentrePage.ActiveCampaign,
                episode_id=episode_id,
            )
            await inter.edit_original_response(
                components=container,
                files=[
                    File(f"resources/news_images/{i}")
                    for i in images_required
                    if i in self.usable_images
                ],
            )

    @Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction) -> None:
        if (
            not self.bot.ready
            or inter.author != inter.message.interaction_metadata.user
            or "cc_active_campaigns_dropdown" not in inter.component.custom_id
        ):
            return
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild.id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild.id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild.id, "en", [])
        else:
            guild = GWWGuild.default()

        episode_id = int(inter.component.custom_id.split("_")[-1])
        phase_id = int(inter.values[0])
        cc = self.bot.data.formatted_data.control_centre.get(guild.language)
        images_required = [
            f"{i}.png"
            for i in cc.images_required(
                episode_id=episode_id, need_episode=False, phase_id=phase_id
            )
            if f"{i}.png" in self.usable_images
        ]
        container = ControlCentreContainer(
            control_centre=cc,
            required_images=images_required,
            dispatches=self.bot.data.formatted_data.dispatches.get(guild.language, []),
            page=ControlCentrePage.ActiveCampaign,
            phase_id=phase_id,
            episode_id=episode_id,
        )
        await inter.response.edit_message(
            components=container,
            files=[
                File(f"resources/news_images/{i}")
                for i in images_required
                if i in self.usable_images
            ],
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(ControlCentreCog(bot))
