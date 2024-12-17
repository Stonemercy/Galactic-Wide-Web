from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.interactables import WikiButton
from utils.checks import wait_for_startup
from utils.embeds import StratagemEmbed


class StratagemsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.stratagems: dict = self.bot.json_dict["stratagems"]

    async def stratagem_autocomp(inter: AppCmdInter, user_input: str):
        stratagems: dict = inter.bot.json_dict["stratagems"]
        return [name for name in stratagems if user_input in name.lower()][:25]

    @wait_for_startup()
    @commands.slash_command(description="Returns information on a stratagem.")
    async def stratagem(
        self,
        inter: AppCmdInter,
        stratagem: str = commands.Param(
            autocomplete=stratagem_autocomp,
            description="The stratagem you want to lookup",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{stratagem = }>"
        )
        if stratagem not in self.stratagems:
            return await inter.send(
                (
                    "That stratagem isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        stratagem_stats = self.stratagems[stratagem]
        embed = StratagemEmbed(stratagem, stratagem_stats)
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **stratagem __{stratagem}__** <@{self.bot.owner_id}> :warning:"
            )
        components = [
            WikiButton(
                link=f"https://helldivers.wiki.gg/wiki/{stratagem.replace(' ', '_')}"
            )
        ]
        return await inter.send(
            embed=embed, ephemeral=public != "Yes", components=components
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(StratagemsCog(bot))
