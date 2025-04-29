from disnake import AppCmdInter, Embed, File
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.functions import compare_translations, split_long_string
from utils.interactables import SupportServerButton


class TranslationsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Check language JSON for missing translations",
    )
    async def check_missing_translations(
        self,
        inter: AppCmdInter,
        language_to_check: str = commands.Param(
            choices=["de", "es", "fr", "it", "pt-br", "ru", "ALL"]
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            msg=f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        if language_to_check == "ALL":
            embeds = []
            reference = self.bot.json_dict["languages"]["en"]
            for code, language_json in self.bot.json_dict["languages"].items():
                if code == "en":
                    continue
                diffs = compare_translations(reference=reference, target=language_json)
                embed = Embed(title=f"{code.upper()} JSON diffs")
                if diffs:
                    untranslated_count = len([s for s in diffs if "Untranslated" in s])
                    extra_count = len([s for s in diffs if "Extra" in s])
                    missing_count = len([s for s in diffs if "Missing" in s])
                    embed.add_field(
                        f"{len(diffs)} total lines incorrect",
                        (
                            f"-# Untranslated: {untranslated_count}\n"
                            f"-# Extra: {extra_count}\n"
                            f"-# Missing: {missing_count}"
                        ),
                    )
                else:
                    embed.add_field("None :)", "Everything has been translated so far")
                embeds.append(embed)
            await inter.send(
                embeds=embeds,
                components=[SupportServerButton()],
            )
        else:
            diffs = compare_translations(
                reference=self.bot.json_dict["languages"]["en"],
                target=self.bot.json_dict["languages"][language_to_check],
            )
            embed = Embed(title=f"{language_to_check.upper()} JSON diffs")
            if diffs:
                untranslated_count = len([s for s in diffs if "Untranslated" in s])
                extra_count = len([s for s in diffs if "Extra" in s])
                missing_count = len([s for s in diffs if "Missing" in s])
                embed.add_field(
                    f"{len(diffs)} total lines incorrect",
                    (
                        f"-# Untranslated: {untranslated_count}\n"
                        f"-# Extra: {extra_count}\n"
                        f"-# Missing: {missing_count}"
                    ),
                )
                split_text = split_long_string(text="\n".join(diffs))
                if len(split_text) < 6:
                    for chunk in split_text:
                        embed.add_field("", chunk, inline=False)
                else:
                    embed.add_field(
                        "Incorrect lines should be clear to see as they are the same as English",
                        "",
                        inline=False,
                    )
                await inter.send(
                    embed=embed,
                    file=File(fp=f"data/languages/{language_to_check}.json"),
                    components=[SupportServerButton()],
                )
            else:
                embed.add_field(
                    "None :smiley:",
                    "Everything has been translated so far\n-# Feel free to check the current translation for any improvements",
                )
                await inter.send(
                    embed=embed,
                    file=File(fp=f"data/languages/{language_to_check}.json"),
                )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(TranslationsCog(bot))
