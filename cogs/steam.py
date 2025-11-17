from datetime import datetime
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    HTTPException,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds, WarInfo
from utils.embeds import SteamEmbed
from utils.interactables import SteamStringSelect


class SteamCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.current_war_info = None

    def cog_load(self) -> None:
        if not self.current_war_info:
            self.current_war_info = WarInfo()
        if not self.steam_check.is_running():
            self.steam_check.start()
            self.bot.loops.append(self.steam_check)

    def cog_unload(self) -> None:
        if self.steam_check.is_running():
            self.steam_check.stop()
            if self.steam_check in self.bot.loops:
                self.bot.loops.remove(self.steam_check)

    @tasks.loop(minutes=1)
    async def steam_check(self) -> None:
        patch_notes_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or patch_notes_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        if self.current_war_info.patch_notes_id != self.bot.data.steam[0].id:
            unique_langs = GWWGuilds.unique_languages()
            embeds = {
                lang: [
                    SteamEmbed(
                        self.bot.data.steam[0], self.bot.json_dict["languages"][lang]
                    )
                ]
                for lang in unique_langs
            }
            await self.bot.interface_handler.send_feature("patch_notes", embeds)
            self.current_war_info.patch_notes_id = self.bot.data.steam[0].id
            self.current_war_info.save_changes()
            self.bot.logger.info(
                f"Sent patch announcements out to {len(self.bot.interface_handler.patch_notes)} channels in {(datetime.now() - patch_notes_start).total_seconds():.2f}s"
            )

    @steam_check.before_loop
    async def before_steam_check(self) -> None:
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="Get the 25 most recent Steam posts",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the 25 latest patch notes with a dropdown to select other ones via title.",
            "example_usage": "**`/steam public:Yes`** returns an embed with the most recent patch notes, it also has a dropdown for the most recent 10 patch notes you can choose from. Other people can see this too.",
        },
    )
    async def steam(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
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
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
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
        await inter.send(
            embed=SteamEmbed(
                steam=self.bot.data.steam[0],
                language_json=self.bot.json_dict["languages"][guild.language],
            ),
            components=[SteamStringSelect(self.bot.data.steam)],
            ephemeral=public != "Yes",
        )

    @commands.Cog.listener("on_dropdown")
    async def steam_notes_listener(self, inter: MessageInteraction):
        if (
            inter.component.custom_id != "steam"
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        steam_data = [
            steam for steam in self.bot.data.steam if steam.title == inter.values[0]
        ][0]
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        embed = SteamEmbed(
            steam=steam_data,
            language_json=self.bot.json_dict["languages"][guild.language],
        )
        await inter.response.edit_message(embed=embed)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(SteamCog(bot))
