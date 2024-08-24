from datetime import datetime
from disnake.ext import commands
from dotenv import load_dotenv
from os import getenv, listdir
from disnake import ActivityType, Intents, Activity
import logging

logger = logging.getLogger("disnake")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="disnake.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s: %(levelname)s: %(name)s: %(message)s")
)
logger.addHandler(handler)

load_dotenv("data/.env")
OWNER = int(getenv("OWNER"))

intents = Intents.default()
activity = Activity(name="for Socialism", type=ActivityType.watching)


class GalacticWideWebBot(commands.InteractionBot):
    def __init__(self):
        super().__init__(owner_id=OWNER, intents=intents, activity=activity)
        self.logger = logger
        self.startup_time = datetime.now()
        self.dashboard_messages = []
        self.dashboard_channels = []
        self.announcement_channels = []
        self.patch_channels = []
        self.map_messages = []
        self.map_channels = []

    async def on_ready(self):
        self.moderator_channel = self.get_channel(int(getenv("MODERATION_CHANNEL")))
        self.feedback_channel = self.get_channel(int(getenv("FEEDBACK_CHANNEL")))
        self.waste_bin_channel = self.get_channel(int(getenv("WASTE_BIN_CHANNEL")))
        self.logger.info(
            f"Loaded {len(bot.cogs)}/{len([f for f in listdir('cogs') if f.endswith('.py')]) + len([f for f in listdir('cogs/admin') if f.endswith('.py')])} cogs successfully"
        )


bot = GalacticWideWebBot()

bot.load_extensions("cogs")
bot.load_extensions("cogs/admin")

if __name__ == "__main__":
    bot.run(getenv("TOKEN"))
