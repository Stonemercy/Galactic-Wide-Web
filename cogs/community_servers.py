from disnake import AppCmdInter, Permissions
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup


class CommunityServersCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        description="Get all community servers and their invite links",
        default_member_permissions=Permissions(administrator=True),
    )
    async def community_servers(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        communities_with_links = sorted(
            [
                guild
                for guild in self.bot.guilds
                if "COMMUNITY" in guild.features and guild.vanity_url_code
            ],
            key=lambda guild: guild.member_count,
        )
        guilds_text = "# Community Servers\n"
        for index, guild in enumerate(communities_with_links, start=1):
            if len(guilds_text) < 1900:
                guilds_text += f"\n-# {index}. [{guild.name}](<https://discord.com/invite/{guild.vanity_url_code}>)"
            else:
                guilds_text += (
                    f"\nThese are the top {index-1} community servers this bot is in"
                )
                break
        await inter.send(content=guilds_text, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=CommunityServersCog(bot))
