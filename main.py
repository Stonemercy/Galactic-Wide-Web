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

intents = Intents.default()

load_dotenv("data/.env")
OWNER = int(getenv("OWNER"))

activity = Activity(name="for Socialism", type=ActivityType.watching)

bot = commands.InteractionBot(
    owner_id=OWNER,
    intents=intents,
    activity=activity,
)

bot.load_extensions("cogs")
bot.load_extensions("cogs/admin")

print(
    f"Loaded {len(bot.cogs)}/{len([f for f in listdir('cogs') if f.endswith('.py')]) + len([f for f in listdir('cogs/admin') if f.endswith('.py')])} cogs successfully"
)

if __name__ == "__main__":
    bot.run(getenv("TOKEN"))
