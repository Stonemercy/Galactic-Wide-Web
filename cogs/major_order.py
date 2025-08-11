from disnake import (
    AppCmdInter,
    InteractionContextTypes,
    ApplicationInstallTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.data import GlobalEvent
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds.dashboard import Dashboard
from utils.interactables import WikiButton


class MajorOrderCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on an Automaton or variation.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns information on the current Major Order, if there is one",
            "example_usage": "**`/major_order public:Yes`** would return information on the current Major Order that other members in the server can see.",
        },
    )
    async def major_order(
        self,
        inter: AppCmdInter,
        with_announcement: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the large briefing to be attached.",
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
            f"{self.qualified_name} | /{inter.application_command.name} <{with_announcement = }> <{public = }>"
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
        if self.bot.data.assignments:
            embeds = []
            for assignment in self.bot.data.assignments:
                embed = Dashboard.MajorOrderEmbed(
                    assignment=assignment,
                    planets=self.bot.data.planets,
                    liberation_changes_tracker=self.bot.data.liberation_changes,
                    mo_task_tracker=self.bot.data.major_order_changes,
                    language_json=guild_language,
                    json_dict=self.bot.json_dict,
                    with_health_bars=True,
                )
                if with_announcement == "Yes":
                    announcements: list[GlobalEvent] = [
                        ge
                        for ge in self.bot.data.global_events
                        if ge.assignment_id == assignment.id
                        and ge.title != ""
                        and ge.message != ""
                    ]
                    if announcement := announcements[0] if announcements else None:
                        embed.insert_field_at(
                            0,
                            announcement.title,
                            announcement.split_message[0],
                            inline=False,
                        )
                        for index, chunk in enumerate(
                            announcement.split_message[1:], 1
                        ):
                            embed.insert_field_at(index, "", chunk, inline=False)
                embeds.append(embed)
        else:
            embeds = [
                Dashboard.MajorOrderEmbed(
                    assignment=None,
                    planets=None,
                    liberation_changes_tracker=None,
                    mo_task_tracker=None,
                    language_json=guild_language,
                    json_dict=None,
                    with_health_bars=False,
                )
            ]
        await inter.send(
            embeds=embeds,
            components=[
                WikiButton(link=f"https://helldivers.wiki.gg/wiki/Major_Orders")
            ],
            ephemeral=public != "Yes",
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MajorOrderCog(bot))
