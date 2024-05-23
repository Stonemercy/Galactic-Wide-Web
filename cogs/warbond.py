from logging import getLogger
from re import findall
from disnake import AppCmdInter, ButtonStyle, MessageInteraction
from disnake.ext import commands
from disnake.ui import Button, ActionRow
from helpers.embeds import Items
from json import load

logger = getLogger("disnake")


class WarbondCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warbond_names = load(open("data/json/warbonds.json"))
        self.warbond_names["item_list"] = {}
        for i, j in self.warbond_names.items():
            if i == "item_list":
                continue
            self.warbond_names["item_list"][j["name"]] = j
        self.warbond_names = self.warbond_names["item_list"]
        self.item_names = load(open("data/json/items/item_names.json"))

    async def warbond_autocomp(inter: AppCmdInter, user_input: str):
        warbond_names = load(open("data/json/warbonds.json"))
        warbond_names["item_list"] = {}
        for i, j in warbond_names.items():
            if i == "item_list":
                continue
            warbond_names["item_list"][j["name"]] = j
        warbond_names = warbond_names["item_list"]
        return [warbond for warbond in warbond_names if user_input in warbond.lower()]

    @commands.slash_command(
        description="Returns a basic summary of the items in a specific warbond."
    )
    async def warbond(
        self,
        inter: AppCmdInter,
        warbond: str = commands.Param(autocomplete=warbond_autocomp),
    ):
        logger.info("warbond command used")
        if warbond not in self.warbond_names:
            return await inter.send(
                (
                    "That warbond isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
                delete_after=10,
            )

        chosen_warbond = load(
            open(f"data/json/warbonds/{self.warbond_names[warbond]['id']}.json")
        )

        embed = Items.Warbond(
            chosen_warbond, self.warbond_names[warbond], self.item_names, 1
        )
        components = [
            Button(
                style=ButtonStyle.success,
                custom_id=f"{self.warbond_names[warbond]['name']}_prev_page",
                label="Previous Page",
                disabled=True,
            ),
            Button(
                style=ButtonStyle.success,
                custom_id=f"{self.warbond_names[warbond]['name']}_next_page",
                label="Next Page",
            ),
        ]
        return await inter.send(
            embed=embed, ephemeral=True, components=components, delete_after=900
        )

    @commands.Cog.listener("on_button_click")
    async def page_button_listener(self, inter: MessageInteraction):
        button_id = inter.component.custom_id
        if button_id[:-10] not in self.warbond_names:
            return
        action_row = ActionRow.rows_from_message(inter.message)[0]
        warbond_json = self.warbond_names[button_id[:-10]]
        warbond = load(open(f"data/json/warbonds/{warbond_json['id']}.json"))
        page_count = [int(i) for i in warbond]
        current_page = int(findall(r"\d+", inter.message.embeds[0].description)[0])
        new_page = (
            current_page + 1
            if button_id == f"{warbond_json['name']}_next_page"
            else current_page - 1
        )
        if new_page == page_count[0]:
            action_row.children[0].disabled = True
        elif new_page == page_count[-1]:
            action_row.children[1].disabled = True
        else:
            action_row.children[0].disabled = False
            action_row.children[1].disabled = False
        embed = Items.Warbond(warbond, warbond_json, self.item_names, new_page)
        await inter.response.edit_message(
            embed=embed,
            components=action_row,
        )


def setup(bot: commands.Bot):
    bot.add_cog(WarbondCog(bot))
