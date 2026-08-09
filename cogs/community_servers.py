from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Guild,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, slash_command
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds import CommunityServersEmbed
from utils.interactables.community_servers import NextPageButton, PreviousPageButton

ALLOWED_BUTTONS = ["CommunityServerPreviousPageButton", "CommunityServerNextPageButton"]


class CommunityServersCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    # should really localize
    @wait_for_startup()
    @slash_command(
        description="Get a list of community servers with invite links",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows a paged list of servers the bot is in that are marked as Discord Community servers and have a vanity invite URL, sorted by member count. Use the Previous/Next buttons to browse through pages of 10 servers at a time.",
            "example_usage": "**`/community_servers`** returns a paged list of community servers the bot is in, sorted by member count.",
        },
    )
    async def community_servers(self, inter: AppCmdInter) -> None:
        await inter.response.defer(ephemeral=True)

        embed = CommunityServersEmbed(
            guilds=self.communities_with_links,
            page_number=1,
        )
        components = [
            PreviousPageButton(disabled=True),
            NextPageButton(disabled=len(self.communities_with_links) < 10),
        ]
        await inter.send(
            embed=embed,
            components=components,
            ephemeral=True,
        )

    @property
    def communities_with_links(self) -> list[Guild]:
        if not self.bot.ready:
            return []
        return sorted(
            [
                guild
                for guild in self.bot.guilds
                if "COMMUNITY" in guild.features and guild.vanity_url_code is not None
            ],
            key=lambda guild: guild.member_count,
            reverse=True,
        )

    @Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction) -> None:
        if (
            not self.bot.ready
            or inter.component.custom_id not in ALLOWED_BUTTONS
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        await inter.response.defer()

        embed = inter.message.embeds[0]
        current_page = 1
        if (
            embed.footer is not None
            and embed.footer.text is not None
            and "Page" in embed.footer.text
        ):
            current_page = int(embed.footer.text.split(" ")[1])

        match inter.component.custom_id:
            case "CommunityServerPreviousPageButton":
                new_page = max(1, current_page - 1)
                embed = CommunityServersEmbed(
                    guilds=self.communities_with_links,
                    page_number=new_page,
                )
                components = [
                    PreviousPageButton(disabled=new_page == 1),
                    NextPageButton(disabled=len(self.communities_with_links) < 10),
                ]
                await inter.edit_original_response(embed=embed, components=components)
                return
            case "CommunityServerNextPageButton":
                new_page = min(
                    int(len(self.communities_with_links) / 10) + 1, current_page + 1
                )
                embed = CommunityServersEmbed(
                    guilds=self.communities_with_links, page_number=new_page
                )
                components = [
                    PreviousPageButton(disabled=len(self.communities_with_links) < 10),
                    NextPageButton(
                        disabled=new_page >= len(self.communities_with_links) / 10
                    ),
                ]
                await inter.edit_original_response(embed=embed, components=components)
                return


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(CommunityServersCog(bot))
