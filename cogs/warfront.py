from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds import Dashboard


class WarfrontCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on a specific War front",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
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
        ephemeral = public != "Yes"
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{faction = }> <{public = }>"
        )
        await inter.response.defer(ephemeral=ephemeral)
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        defence_embed = Dashboard.DefenceEmbed(
            [
                planet
                for planet in self.bot.data.planet_events
                if planet.event.faction == faction
            ],
            self.bot.data.dss,
            self.bot.data.liberation_changes,
            self.bot.data.planets_with_player_reqs,
            guild_language,
            self.bot.json_dict["planets"],
            self.bot.data.total_players,
        )
        attack_embed = Dashboard.AttackEmbed(
            [
                campaign
                for campaign in self.bot.data.campaigns
                if campaign.faction == faction and not campaign.planet.event
            ],
            self.bot.data.liberation_changes,
            guild_language,
            self.bot.json_dict["planets"],
            faction,
            self.bot.data.total_players,
        )
        for embed in [defence_embed, attack_embed]:
            embed.set_image("https://i.imgur.com/cThNy4f.png")
        await inter.send(embeds=[defence_embed, attack_embed])


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarfrontCog(bot))
