from disnake import (
    AppCmdInter,
    MessageInteraction,
    InteractionContextTypes,
    ApplicationInstallTypes,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.command_embeds import SteamCommandEmbed
from utils.interactables import SteamStringSelect


class SteamCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Get previous Steam posts",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def steam(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        await inter.send(
            embed=SteamCommandEmbed(
                steam=self.bot.data.steam[0],
                language_json=self.bot.json_dict["languages"][guild.language],
            ),
            components=[SteamStringSelect(self.bot.data)],
            ephemeral=public != "Yes",
        )

    @commands.Cog.listener("on_dropdown")
    async def steam_notes_listener(self, inter: MessageInteraction):
        if inter.component.custom_id != "steam":
            return
        steam_data = [
            steam for steam in self.bot.data.steam if steam.title == inter.values[0]
        ][0]
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        embed = SteamCommandEmbed(
            steam_data,
            self.bot.json_dict["languages"][guild.language],
        )
        await inter.response.edit_message(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SteamCog(bot))
