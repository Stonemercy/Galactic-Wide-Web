from disnake import (
    AppCmdInter,
    Embed,
    InteractionContextTypes,
    ApplicationInstallTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.dashboard import Dashboard


class WarfrontCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on a specific War front",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns information on each campaign for a specific faction",
            "example_usage": "**`/warfront faction:Illuminate public:Yes`** would return information on the Illuminate warfront that other members in the server can see.",
        },
    )
    async def warfront(
        self,
        inter: AppCmdInter,
        faction=commands.Param(
            choices=["Automaton", "Terminids", "Illuminate"],
            description="The faction to focus on",
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
            f"{self.qualified_name} | /{inter.application_command.name} <{faction = }> <{public = }>"
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
        gambit_planets = {}
        for campaign in self.bot.data.campaigns:
            if (
                campaign.planet.current_owner == "Humans"
                or len(campaign.planet.defending_from) == 0
                or 1190 in campaign.planet.active_effects
            ):
                continue
            else:
                for defending_index in campaign.planet.attack_targets:
                    defending_planet = self.bot.data.planets[defending_index]
                    if (
                        len(defending_planet.defending_from) < 2
                        and defending_planet.event
                    ):
                        gambit_planets[defending_index] = campaign.planet
        defence_embed = Dashboard.DefenceEmbed(
            planet_events=[
                planet
                for planet in self.bot.data.planet_events
                if planet.event.faction == faction
            ],
            liberation_changes=self.bot.data.liberation_changes,
            language_json=guild_language,
            planet_names=self.bot.json_dict["planets"],
            total_players=self.bot.data.total_players,
            eagle_storm=self.bot.data.dss.get_ta_by_name("EAGLE STORM"),
            with_health_bars=True,
            gambit_planets=gambit_planets,
        )
        attack_embed = Dashboard.AttackEmbed(
            campaigns=[
                campaign
                for campaign in self.bot.data.campaigns
                if campaign.faction == faction and not campaign.planet.event
            ],
            liberation_changes=self.bot.data.liberation_changes,
            language_json=guild_language,
            planet_names=self.bot.json_dict["planets"],
            faction=faction,
            total_players=self.bot.data.total_players,
            with_health_bars=True,
            gambit_planets=gambit_planets,
        )
        embeds: list[Embed] = [defence_embed, attack_embed]
        for embed in embeds.copy():
            if len(embed.fields) == 0:
                embeds.remove(embed)
                continue
            embed.set_image("https://i.imgur.com/cThNy4f.png")
        await inter.send(embeds=embeds)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarfrontCog(bot))
