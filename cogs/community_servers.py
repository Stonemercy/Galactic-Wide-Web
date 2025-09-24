from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Guild,
    InteractionContextTypes,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
)
from disnake.ext import commands
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import CommunityServersEmbed
from utils.interactables import NextPageButton, PreviousPageButton


class CommunityServersCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    # need to localize
    @wait_for_startup()
    @commands.slash_command(
        description="Get all community servers and their invite links",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns a list of as many servers the bot can send in one message. These servers are listed as Communities and have a vanity link.",
            "example_usage": '**`/community_servers`** returns a list of every server the bot is on that is listed as "Community" and has a custom invite URL.',
        },
    )
    async def community_servers(self, inter: AppCmdInter):
        try:
            await inter.response.defer(ephemeral=True)
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            msg=f"{self.qualified_name} | /{inter.application_command.name}"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        embed = CommunityServersEmbed(
            guilds=self.communities_with_links,
            new_index=16,
        )
        components = [
            PreviousPageButton(disabled=True),
            NextPageButton(),
        ]
        await inter.send(embed=embed, components=components, ephemeral=True)

    @property
    def communities_with_links(self) -> list[Guild]:
        return sorted(
            [
                guild
                for guild in self.bot.guilds
                if "COMMUNITY" in guild.features and guild.vanity_url_code
            ],
            key=lambda guild: guild.member_count,
            reverse=True,
        )

    @commands.Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction):
        if inter.component.custom_id not in (
            "CommunityServerPreviousPageButton",
            "CommunityServerNextPageButton",
        ):
            return
        await inter.response.defer()
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        # guild_language = self.bot.json_dict["languages"][guild.language]
        match inter.component.custom_id:
            case "CommunityServerPreviousPageButton":
                index = int(inter.message.embeds[0].footer.text.split("/")[0])
                new_index = max(16, index - 16)
                embed = CommunityServersEmbed(
                    guilds=self.communities_with_links,
                    new_index=new_index,
                )
                components = [
                    PreviousPageButton(disabled=new_index <= 16),
                    NextPageButton(),
                ]
                try:
                    await inter.edit_original_response(
                        embed=embed, components=components
                    )
                    return
                except NotFound:
                    await inter.send(
                        "There was an issue editing the setup message. Your settings have been saved so just use the command again!\nApologies for the inconvenience",
                        ephemeral=True,
                    )
                    return
            case "CommunityServerNextPageButton":
                index = int(inter.message.embeds[0].footer.text.split("/")[0])
                new_index = min(len(self.communities_with_links), index + 16)
                embed = CommunityServersEmbed(
                    guilds=self.communities_with_links,
                    new_index=new_index,
                )
                components = [
                    PreviousPageButton(),
                    NextPageButton(
                        disabled=new_index >= len(self.communities_with_links)
                    ),
                ]
                try:
                    await inter.edit_original_response(
                        embed=embed, components=components
                    )
                    return
                except NotFound:
                    await inter.send(
                        "There was an issue editing the setup message. Your settings have been saved so just use the command again!\nApologies for the inconvenience",
                        ephemeral=True,
                    )
                    return


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=CommunityServersCog(bot))
