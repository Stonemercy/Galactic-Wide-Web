from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Embed,
    InteractionContextTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.dashboard import Dashboard


class SiegeFleetsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def fleet_autocomp(inter: AppCmdInter, user_input: str):
        return [
            p.event.siege_fleet.name
            for p in [
                p
                for p in inter.bot.data.planets.values()
                if p.event and p.event.siege_fleet
            ]
            if user_input.lower() in p.event.siege_fleet.name.lower()
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
            guild = GWWGuild.get_by_id(inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuild.new(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        embed = {
            "THE GREAT HOST": Dashboard.TheGreatHostEmbed(
                the_great_host_resource=self.bot.data.global_resources.the_great_host,
                the_great_host_changes=self.bot.data.the_great_host_changes,
                language_json=guild_language,
            ),
        }.get(fleet, Embed(title="Fleet not found"))
        await inter.send(
            embed=embed,
            ephemeral=public != "Yes",
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SiegeFleetsCog(bot))
