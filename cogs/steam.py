from disnake import AppCmdInter, MessageInteraction
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds import SteamEmbed
from utils.interactables import SteamStringSelect


class SteamCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(description="Get previous Steam posts", dm_permission=False)
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
        await inter.send(
            embed=SteamEmbed(
                steam=self.bot.data.steam[0],
                language=self.bot.json_dict["languages"][
                    GWWGuild.get_by_id(inter.guild_id).language
                ],
            ),
            components=[SteamStringSelect(self.bot)],
            ephemeral=public != "Yes",
        )

    @commands.Cog.listener("on_dropdown")
    async def steam_notes_listener(self, inter: MessageInteraction):
        if inter.component.custom_id != "steam":
            return
        steam_data = [
            steam for steam in self.bot.data.steam if steam.title == inter.values[0]
        ][0]
        embed = SteamEmbed(
            steam_data,
            self.bot.json_dict["languages"][
                GWWGuild.get_by_id(inter.guild_id).language
            ],
        )
        await inter.response.edit_message(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SteamCog(bot))
