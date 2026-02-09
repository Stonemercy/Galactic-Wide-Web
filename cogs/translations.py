from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Embed,
    File,
    InteractionContextTypes,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dataclasses import Languages
from utils.functions import compare_translations, split_long_string
from utils.interactables import SupportServerButton


class TranslationsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Check language JSON for missing translations",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns information on the current bot translations",
            "example_usage": "**`/check_missing_translations language_to_check:de`** would return info on how much of the bot needs translated in German",
        },
    )
    async def check_missing_translations(
        self,
        inter: AppCmdInter,
        language_to_check: str = commands.Param(
            choices=[l.short_code for l in Languages.all] + ["ALL"],
            description="The language you want to check the missing translations for.",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=True)
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
                        f"{len(diffs)} total lines are the same as English",
                        (
                            f"-# Untranslated: {untranslated_count}\n"
                            f"-# Extra: {extra_count}\n"
                            f"-# Missing: {missing_count}"
                        ),
                    )
                    if extra_count:
                        extra_text = "\n".join([s for s in diffs if "Extra" in s])
                        embed.add_field("Extra", f"{extra_text}", inline=False)
                    if missing_count:
                        missing_text = "\n".join([s for s in diffs if "Missing" in s])
                        embed.add_field("missing", f"{missing_text}", inline=False)
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
                    f"{len(diffs)} total lines are the same as English",
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
                        "Untranslated lines should be clear to see as they are the same as English",
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


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(TranslationsCog(bot))
