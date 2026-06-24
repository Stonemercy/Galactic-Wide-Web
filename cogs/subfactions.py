from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.containers import SubfactionsContainer
from utils.dataclasses import Subfactions
from utils.dataclasses.factions import Factions
from utils.dbv2 import GWWGuild, GWWGuilds


class SubfactionCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Get information on enemy subfactions and their controlled planets",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Shows the subfaction with the most controlled planets by default, along with a list of the planets they currently occupy. Use the dropdown to switch between subfactions.",
            "example_usage": "**`/subfaction public:Yes`** returns the most widespread subfaction and their planets, visible to everyone. Use the dropdown to view other subfactions.",
        },
    )
    async def subfaction(
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

        sf_planetcount_tuples = [
            (
                sf,
                len(
                    [
                        p
                        for p in self.bot.data.formatted_data.planets.values()
                        if sf in p.subfactions
                        and (p.faction != Factions.humans or p.active_campaign)
                    ]
                ),
            )
            for sf in Subfactions._all
        ]
        subfaction_to_use = max(sf_planetcount_tuples, key=lambda x: x[1])[0]
        container = SubfactionsContainer(
            subfaction=subfaction_to_use, planets=self.bot.data.formatted_data.planets
        )
        await inter.send(components=container)

    @commands.Cog.listener("on_dropdown")
    async def subfactions_listener(self, inter: MessageInteraction):
        if (
            not self.bot.ready
            or inter.component.custom_id != "subfactions"
            or inter.author != inter.message.interaction_metadata.user
        ):
            return
        subfaction = next(
            (
                sf
                for sf in Subfactions._all
                if sf.eng_name.title() == inter.values[0].split(" - ")[0]
            ),
            None,
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
        container = SubfactionsContainer(
            subfaction=subfaction, planets=self.bot.data.formatted_data.planets
        )
        await inter.response.edit_message(components=container)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(SubfactionCog(bot))
