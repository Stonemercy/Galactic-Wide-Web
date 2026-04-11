from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import SuperstoreContainer
from utils.dbv2 import GWWGuild, GWWGuilds


class SuperstoreCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns the current Superstore rotational page, if available",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the current Superstore rotational page, if available. These items are not mapped automatically so some might not show if they are new.",
            "example_usage": "**`/superstore public:Yes`** returns a container with Superstore rotation, including prices and rotation time. It can also be seen by others in discord.",
        },
    )
    async def superstore(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()

        if not self.bot.data.formatted_data.superstore:
            await inter.send(
                "Superstore unavailable.\nApologies for the inconvenience."
            )
            return

        await inter.send(
            components=[SuperstoreContainer(self.bot.data.formatted_data.superstore)]
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(SuperstoreCog(bot))
