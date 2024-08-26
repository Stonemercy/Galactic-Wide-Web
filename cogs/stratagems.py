from json import load
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import StratagemEmbed
from main import GalacticWideWebBot


class StratagemsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.stratagems: dict = load(open("data/json/stratagems.json"))

    async def stratagem_autocomp(inter: AppCmdInter, user_input: str):
        stratagems: dict = load(open("data/json/stratagems.json"))
        return [name for name in stratagems if user_input in name.lower()][:25]

    @commands.slash_command(description="Returns information on a stratagem.")
    async def stratagem(
        self,
        inter: AppCmdInter,
        stratagem: str = commands.Param(
            autocomplete=stratagem_autocomp,
            description="The stratagem you want to lookup",
        ),
    ):
        self.bot.logger.info(
            f"StratagemsCog, stratagem stratagem:{stratagem} command used"
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
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(StratagemsCog(bot))
