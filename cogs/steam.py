from datetime import datetime, timezone
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, Param, slash_command
from disnake.ext.tasks import loop
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import SteamEmbed
from utils.interactables import SteamStringSelect


class SteamCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        if not self.steam_check.is_running():
            self.steam_check.start()
            self.bot.loops.append(self.steam_check)

    def cog_unload(self) -> None:
        if self.steam_check.is_running():
            self.steam_check.cancel()
        if self.steam_check in self.bot.loops:
            self.bot.loops.remove(self.steam_check)

    @loop(minutes=1)
    async def steam_check(self) -> None:
        patch_notes_start = datetime.now(tz=timezone.utc)
        if not self.bot.ready:
            self.bot.logger.warning("steam_check loop returning - the bot isn't ready")
            return
        if self.bot.interface_handler.busy:
            self.bot.logger.warning(
                "steam_check loop returning - the interface_handler is busy"
            )
            return
        if not self.bot.data.formatted_data.steam_news:
            self.bot.logger.warning(
                "steam_check loop returning - steam posts are missing"
            )
            return
        if not self.bot.data.formatted_data:
            self.bot.logger.error("steam_check loop returning - NO FORMATTED DATA")
            return

        for steam_news in self.bot.data.formatted_data.steam_news[::-1]:
            if steam_news.id > self.bot.databases.war_info.patch_notes_id:
                unique_langs = GWWGuilds.unique_languages()
                embeds = {
                    lang: [
                        SteamEmbed(steam_news, self.bot.json_dict["languages"][lang])
                    ]
                    for lang in unique_langs
                }
                await self.bot.interface_handler.send_feature("patch_notes", embeds)
                self.bot.databases.war_info.patch_notes_id = steam_news.id
                self.bot.databases.war_info.save_changes()
                self.bot.logger.info(
                    f"steam_check loop - sent steam announcement {steam_news.id} out to {len(self.bot.interface_handler.patch_notes)} channels in {(datetime.now(tz=timezone.utc) - patch_notes_start).total_seconds():.2f} seconds"
                )
                return

    @steam_check.before_loop
    async def before_steam_check(self) -> None:
        await self.bot.wait_until_ready()

    @steam_check.error
    async def steam_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "steam_check loop")

    @wait_for_startup()
    @slash_command(
        description="Get the most recent Helldivers 2 Steam posts",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows the most recent Helldivers 2 Steam post. Includes a dropdown to browse and switch between the 25 most recent posts by title.",
            "example_usage": "**`/steam public:Yes`** returns the latest Steam post visible to everyone, with a dropdown to browse recent posts.",
        },
    )
    async def steam(
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
        await inter.send(
            embed=SteamEmbed(
                steam=self.bot.data.formatted_data.steam_news[0],
                language_json=self.bot.json_dict["languages"][guild.language],
            ),
            components=[SteamStringSelect(self.bot.data.formatted_data.steam_news)],
            ephemeral=public != "Yes",
        )

    @Cog.listener("on_dropdown")
    async def steam_notes_listener(self, inter: MessageInteraction):
        if (
            not self.bot.ready
            or inter.component.custom_id != "steam"
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        steam_data = [
            steam
            for steam in self.bot.data.formatted_data.steam_news
            if steam.title == inter.values[0]
        ][0]
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild.id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild.id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild.id, "en", [])
        else:
            guild = GWWGuild.default()
        embed = SteamEmbed(
            steam=steam_data,
            language_json=self.bot.json_dict["languages"][guild.language],
        )
        await inter.response.edit_message(embed=embed)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(SteamCog(bot))
