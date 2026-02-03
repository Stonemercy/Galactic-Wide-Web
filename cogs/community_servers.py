from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Guild,
    InteractionContextTypes,
    MessageInteraction,
    NotFound,
)
from disnake.ext import commands
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds import CommunityServersEmbed
from utils.interactables import NextPageButton, PreviousPageButton


class CommunityServersCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    # should really localize
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
    async def community_servers(self, inter: AppCmdInter) -> None:
        await inter.response.defer(ephemeral=True)
        embed = CommunityServersEmbed(
            guilds=self.communities_with_links,
            new_index=min(16, len(self.communities_with_links)),
        )
        components = [
            PreviousPageButton(disabled=True),
            NextPageButton(disabled=len(self.communities_with_links) < 16),
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
    async def on_button_clicks(self, inter: MessageInteraction) -> None:
        if inter.component.custom_id not in (
            "CommunityServerPreviousPageButton",
            "CommunityServerNextPageButton",
        ):
            return
        await inter.response.defer()
        try:
            embed = inter.message.embeds[0]
            footer_text = (
                embed.footer.text if embed.footer and embed.footer.text else None
            )
            index = (
                int(footer_text.split("/")[0])
                if footer_text and "/" in footer_text
                else 16
            )
        except (IndexError, AttributeError, ValueError):
            index = 16
        match inter.component.custom_id:
            case "CommunityServerPreviousPageButton":
                new_index = max(16, index - 16)
                embed = CommunityServersEmbed(
                    guilds=self.communities_with_links,
                    new_index=new_index,
                )
                components = [
                    PreviousPageButton(disabled=new_index <= 16),
                    NextPageButton(disabled=len(self.communities_with_links) < 16),
                ]
                try:
                    await inter.edit_original_response(
                        embed=embed, components=components
                    )
                    return
                except NotFound:
                    await inter.send(
                        "-# There was an issue changing page.\n-# Please try again.",
                        ephemeral=True,
                    )
                    return
            case "CommunityServerNextPageButton":
                new_index = min(len(self.communities_with_links), index + 16)
                embed = CommunityServersEmbed(
                    guilds=self.communities_with_links,
                    new_index=new_index,
                )
                components = [
                    PreviousPageButton(disabled=len(self.communities_with_links) < 16),
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
                        "-# There was an issue changing page.\n-# Please try again.",
                        ephemeral=True,
                    )
                    return


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(CommunityServersCog(bot))
