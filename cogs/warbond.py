from disnake import (
    AppCmdInter,
    ButtonStyle,
    MessageInteraction,
    InteractionContextTypes,
    ApplicationInstallTypes,
)
from disnake.ext import commands
from disnake.ui import Button, ActionRow
from main import GalacticWideWebBot
from re import findall
from utils.checks import wait_for_startup
from utils.embeds.command_embeds import WarbondCommandEmbed
from utils.interactables import HDCButton, WikiButton


class WarbondCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.warbond_index = {
            warbond["name"]: warbond
            for warbond in self.bot.json_dict["warbonds"]["index"].values()
        }
        self.boosters = [
            booster["name"]
            for booster in self.bot.json_dict["items"]["boosters"].values()
        ]

    async def warbond_autocomp(inter: AppCmdInter, user_input: str):
        warbond_names = [
            warbond["name"]
            for warbond in inter.bot.json_dict["warbonds"]["index"].values()
        ]
        return [warbond for warbond in warbond_names if user_input in warbond.lower()][
            :25
        ]

    @wait_for_startup()
    @commands.slash_command(
        description="Returns a basic summary of the items in a specific warbond.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def warbond(
        self,
        inter: AppCmdInter,
        warbond: str = commands.Param(
            autocomplete=warbond_autocomp, description="The warbond you want to lookup"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{warbond = }>"
        )
        if warbond not in self.warbond_index:
            return await inter.send(
                (
                    "That warbond isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=public != "Yes",
            )
        chosen_warbond_json = {
            "name": warbond,
            "json": self.bot.json_dict["warbonds"][self.warbond_index[warbond]["id"]],
        }
        embed = WarbondCommandEmbed(
            warbond_json=chosen_warbond_json, json_dict=self.bot.json_dict, page=1
        )
        components = [
            Button(
                style=ButtonStyle.success,
                custom_id=f"{warbond}_prev_page",
                label="Previous Page",
                disabled=True,
            ),
            Button(
                style=ButtonStyle.success,
                custom_id=f"{warbond}_next_page",
                label="Next Page",
            ),
            WikiButton(link=f"https://helldivers.wiki.gg/wiki/Warbonds"),
            HDCButton(
                link=f"https://helldiverscompanion.com/#hellpad/warbonds/{warbond.lower().replace(' ', '_')}"
            ),
        ]
        return await inter.send(
            embed=embed,
            ephemeral=public != "Yes",
            components=components,
        )

    @commands.Cog.listener("on_button_click")
    async def page_button_listener(self, inter: MessageInteraction):
        button_id = inter.component.custom_id
        if button_id[:-10] not in self.warbond_index:
            return
        action_row = ActionRow.rows_from_message(inter.message)[0]
        warbond_index = self.warbond_index[button_id[:-10]]
        warbond_json = {
            "name": warbond_index["name"],
            "json": self.bot.json_dict["warbonds"][warbond_index["id"]],
        }
        page_count = [int(i) for i in warbond_json["json"]]
        current_page = int(findall(r"\d+", inter.message.embeds[0].description)[0])
        new_page = (
            current_page + 1
            if button_id == f"{warbond_index['name']}_next_page"
            else current_page - 1
        )
        if new_page == page_count[0]:
            action_row.children[0].disabled = True
        elif new_page == page_count[-1]:
            action_row.children[1].disabled = True
        else:
            action_row.children[0].disabled = False
            action_row.children[1].disabled = False
        embed = WarbondCommandEmbed(
            warbond_json=warbond_json, json_dict=self.bot.json_dict, page=new_page
        )
        await inter.response.edit_message(
            embed=embed,
            components=action_row,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarbondCog(bot))
