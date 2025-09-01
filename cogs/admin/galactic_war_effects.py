from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import is_whitelisted, wait_for_startup
from utils.embeds import GalacticWarEffectEmbed


class GWECog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def id_autocomp(inter: AppCmdInter, user_input: str):
        id_list = sorted(
            [i.id for i in inter.bot.data.galactic_war_effects], reverse=True
        )
        return [gwe for gwe in id_list if str(user_input).lower() in str(gwe).lower()][
            :25
        ]

    async def type_autocomp(inter: AppCmdInter, user_input: str):
        type_list = set(
            sorted([i.effect_type for i in inter.bot.data.galactic_war_effects])
        )
        return [
            gwe for gwe in type_list if str(user_input).lower() in str(gwe).lower()
        ][:25]

    @wait_for_startup()
    @is_whitelisted()
    @commands.slash_command(
        description="Check a galactic effect",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def gwe(
        self,
        inter: AppCmdInter,
        id: int = commands.Param(
            autocomplete=id_autocomp,
            description="The ID you want to lookup",
            default=0,
        ),
        type: int = commands.Param(
            autocomplete=type_autocomp,
            description="The type you want to lookup",
            default=0,
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{id = }> <{type = }> <{public = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        gwe_list = None
        if id != 0:
            gwe_list = [g for g in self.bot.data.galactic_war_effects if g.id == id]
        elif type != 0:
            gwe_list = [
                g for g in self.bot.data.galactic_war_effects if g.effect_type == type
            ]
        if gwe_list:
            embeds = []
            for gwe in gwe_list:
                planets_with_gwe = [
                    p
                    for p in self.bot.data.planets.values()
                    if gwe.id in [effect.id for effect in p.active_effects]
                ]
                global_events_list = [
                    i for i in self.bot.data.global_events if gwe.id in i.effect_ids
                ]
                if (
                    global_events_list != []
                    and global_events_list[0].planet_indices == []
                ):
                    planets_with_gwe = "ALL"
                embed = GalacticWarEffectEmbed(
                    gwe=gwe,
                    planets_with_gwe=planets_with_gwe,
                    json_dict=self.bot.json_dict,
                )
                embeds.append(embed)
            await inter.send(embeds=embeds[:5], ephemeral=public != "Yes")
        else:
            await inter.send(
                "Couldn't find that effect, sorry", ephemeral=public != "Yes"
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=GWECog(bot))
