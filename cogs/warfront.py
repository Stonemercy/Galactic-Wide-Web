from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Embed,
    HTTPException,
    InteractionContextTypes,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import WarfrontAllPlanetsEmbed, Dashboard


class WarfrontCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
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
    ) -> None:
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except HTTPException:
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{faction = }> <{public = }>"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        defence_embed = Dashboard.DefenceEmbed(
            planet_events=[
                planet
                for planet in self.bot.data.formatted_data.planet_events
                if planet.event.faction.full_name == faction
            ],
            language_json=guild_language,
            total_players=self.bot.data.formatted_data.total_players,
            eagle_storm=self.bot.data.formatted_data.dss.get_ta_by_name("EAGLE STORM"),
            gambit_planets=self.bot.data.formatted_data.gambit_planets,
        )
        attack_embed = Dashboard.AttackEmbed(
            campaigns=[
                campaign
                for campaign in self.bot.data.formatted_data.campaigns
                if campaign.faction.full_name == faction and not campaign.planet.event
            ],
            language_json=guild_language,
            faction=faction,
            total_players=self.bot.data.formatted_data.total_players,
            planets=self.bot.data.formatted_data.planets,
            gambit_planets=self.bot.data.formatted_data.gambit_planets,
        )
        all_planets_embed = WarfrontAllPlanetsEmbed(
            planets=self.bot.data.formatted_data.planets, faction=faction
        )
        embeds: list[Embed] = [defence_embed, attack_embed, all_planets_embed]
        for embed in embeds.copy():
            if len(embed.fields) == 0:
                embeds.remove(embed)
                continue
            embed.set_image("https://i.imgur.com/cThNy4f.png")
        await inter.send(embeds=embeds)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(WarfrontCog(bot))
