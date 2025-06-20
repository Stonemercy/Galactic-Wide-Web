# from datetime import datetime, time
from os import getenv

# from disnake import (
#     AppCmdInter,
#     Permissions,
#     InteractionContextTypes,
#     ApplicationInstallTypes,
# )
from disnake.ext import commands  # , tasks
from main import GalacticWideWebBot

# from utils.checks import wait_for_startup
# from utils.embeds.command_embeds import PersonalOrderCommandEmbed
# from utils.embeds.loop_embeds import PersonalOrderLoopEmbed
# from utils.interactables import WikiButton

SUPPORT_SERVER_ID = [int(getenv("SUPPORT_SERVER"))]


class PersonalOrderCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        ###### DISABLED UNTIL SOURCE IS UPDATED ######
        # self.personal_order_update.start()

    # def cog_unload(self):
    #     self.personal_order_update.stop()

    # @wait_for_startup()
    # @commands.slash_command(
    #     description="Returns information on todays personal order.",
    #     install_types=ApplicationInstallTypes.all(),
    #     contexts=InteractionContextTypes.all(),
    #     extras={
    #         "long_description": "Returns the current Personal Order",
    #         "example_usage": "**`/personal_order public:Yes`** returns an embed with todays personal order details. It can also be seen by others in discord.",
    #     },
    # )
    # async def personal_order(
    #     self,
    #     inter: AppCmdInter,
    #     public: str = commands.Param(
    #         choices=["Yes", "No"],
    #         default="No",
    #         description="If you want the response to be seen by others in the server.",
    #     ),
    # ):
    #     await inter.response.defer(ephemeral=public != "Yes")
    #     self.bot.logger.info(
    #         f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
    #     )
    #     if inter.guild:
    #         guild = GWWGuild.get_by_id(inter.guild_id)
    #     else:
    #         guild = GWWGuild.default()
    #     if not self.bot.data.personal_order:
    #         await inter.send(
    #             "Personal order data is unavailable. Please try again later.",
    #             ephemeral=public != "Yes",
    #         )
    #         return
    #     await inter.send(
    #         embed=PersonalOrderCommandEmbed(
    #             personal_order=self.bot.data.personal_order,
    #             language_json=self.bot.json_dict["languages"][guild.language],
    #             reward_types=self.bot.json_dict["items"]["reward_types"],
    #             item_names_json=self.bot.json_dict["items"]["item_names"],
    #             enemy_ids_json=self.bot.json_dict["enemies"]["enemy_ids"],
    #         ),
    #         components=[
    #             WikiButton(link=f"https://helldivers.wiki.gg/wiki/Personal_Orders")
    #         ],
    #         ephemeral=public != "Yes",
    #     )

    # @tasks.loop(
    #     time=[time(hour=9, minute=10, second=0), time(hour=21, minute=10, second=0)]
    # )
    # async def personal_order_update(self):
    #     po_updates_start = datetime.now()
    #     if (
    #         not self.bot.interface_handler.loaded
    #         or po_updates_start < self.bot.ready_time
    #         or not self.bot.data.loaded
    #         or not self.bot.data.personal_order
    #     ):
    #         return
    #     embeds = {
    #         lang: PersonalOrderLoopEmbed(
    #             personal_order=self.bot.data.personal_order,
    #             language_json=self.bot.json_dict["languages"][lang],
    #             reward_types=self.bot.json_dict["items"]["reward_types"],
    #             item_names_json=self.bot.json_dict["items"]["item_names"],
    #             enemy_ids_json=self.bot.json_dict["enemies"]["enemy_ids"],
    #         )
    #         for lang in list(set([guild.language for guild in GWWGuild.get_all()]))
    #     }
    #     await self.bot.interface_handler.send_news("PO", embeds)
    #     self.bot.logger.info(
    #         f"Sent Personal Order announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['PO'])} channels"
    #     )

    # @personal_order_update.before_loop
    # async def before_personal_order_update(self):
    #     await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(PersonalOrderCog(bot))
