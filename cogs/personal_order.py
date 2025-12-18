from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    HTTPException,
    InteractionContextTypes,
)
from disnake.ext import commands
from utils.bot import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds.personal_order_embed import PersonalOrderCommandEmbed


class PersonalOrderCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Get the current Personal Order",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the current Personal Order, if available.",
            "example_usage": "**`/personal_order public:Yes`** returns an embed with the current Personal Order. Other people can see this too.",
        },
    )
    async def personal_order(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
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
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        if not self.bot.data.formatted_data.personal_order:
            await inter.send(
                "Personal order unavailable. Apologies for the inconvenience",
                ephemeral=public != "Yes",
            )
        else:
            await inter.send(
                embed=PersonalOrderCommandEmbed(
                    personal_order=self.bot.data.formatted_data.personal_order,
                    json_dict=self.bot.json_dict,
                ),
                ephemeral=public != "Yes",
            )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(PersonalOrderCog(bot))
