from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Colour,
    Embed,
    InteractionContextTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.data import SiegeFleet
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds.command_embeds import SiegeFleetCommandEmbed


class SiegeFleetsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def fleet_autocomp(inter: AppCmdInter, user_input: str):
        return [
            gr.name
            for gr in inter.bot.data.global_resources
            if isinstance(gr, SiegeFleet)
            if user_input.lower() in gr.name.lower()
        ]

    @wait_for_startup()
    @commands.slash_command(
        description="Check status of fleets currently sieging our territory",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns information on fleets currently sieging our territory",
            "example_usage": "**`/siege_fleets public:Yes`** would return information on The Great Host that other members in the server can see.",
        },
    )
    async def siege_fleets(
        self,
        inter: AppCmdInter,
        fleet: str = commands.Param(
            autocomplete=fleet_autocomp, description="The fleet you want to lookup"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ):
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{public = }> <{fleet = }>"
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
        guild_language = self.bot.json_dict["languages"][guild.language]
        try:
            fleet_chosen = [
                gr
                for gr in self.bot.data.global_resources
                if isinstance(gr, SiegeFleet) and gr.name == fleet
            ][0]
            embed = SiegeFleetCommandEmbed(
                siege_fleet=fleet_chosen,
                siege_changes=self.bot.data.siege_fleet_changes.get_entry(
                    fleet_chosen.id
                ),
                language_json=guild_language,
            )
        except IndexError:
            embed = Embed(
                title="Fleet not found, please select from the list",
                colour=Colour.dark_embed(),
            )
        finally:
            await inter.send(
                embed=embed,
                ephemeral=public != "Yes",
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SiegeFleetsCog(bot))
