from logging import getLogger, INFO, FileHandler, Formatter
from datetime import datetime, timedelta
from disnake import ActivityType, Intents, Activity
from disnake.ext import commands
from dotenv import load_dotenv
from os import getenv, listdir
from utils.functions import load_json

load_dotenv("data/.env")

intents = Intents.default()
activity = Activity(name="for Socialism", type=ActivityType.watching)


class GalacticWideWebBot(commands.InteractionBot):
    def __init__(self):
        super().__init__(intents=intents, activity=activity)
        self.logger = getLogger("disnake")
        self.logger.setLevel(INFO)
        handler = FileHandler(filename="disnake.log", encoding="utf-8", mode="w")
        handler.setFormatter(
            Formatter("%(asctime)s: %(levelname)s: %(name)s: %(message)s")
        )
        self.logger.addHandler(handler)
        self.startup_time = datetime.now()
        self.ready_time = self.startup_time + timedelta(seconds=15)
        self.dashboard_messages = []
        self.dashboard_channels = []
        self.announcement_channels = []
        self.patch_channels = []
        self.map_messages = []
        self.map_channels = []
        self.c_n_m_loaded = False
        self.json_dict = load_json()
        if not self.json_dict:
            self.logger.warning("JSON FAILED TO LOAD")
        self.data_dict = {
            "assignments": None,
            "campaigns": None,
            "dispatches": None,
            "planets": None,
            "steam": None,
            "thumbnails": None,
        }
        self.data_loaded = False

    async def on_ready(self):
        self.moderator_channel = self.get_channel(int(getenv("MODERATION_CHANNEL")))
        self.feedback_channel = self.get_channel(int(getenv("FEEDBACK_CHANNEL")))
        self.waste_bin_channel = self.get_channel(int(getenv("WASTE_BIN_CHANNEL")))
        self.logger.info(
            f"Loaded {len(bot.cogs)}/{len([f for f in listdir('cogs') if f.endswith('.py')]) + len([f for f in listdir('cogs/admin') if f.endswith('.py')])} cogs successfully"
        )


bot = GalacticWideWebBot()

bot.load_extensions("cogs/admin")
bot.load_extensions("cogs")

if __name__ == "__main__":
    bot.run(getenv("TOKEN"))
