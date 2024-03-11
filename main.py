from disnake.ext import commands
from dotenv import load_dotenv
from os import getenv
from disnake import ActivityType, Intents, Activity

intents = Intents.default()

load_dotenv("data/.env")
OWNER = int(getenv("OWNER"))

activity = Activity(name="for Socialism", type=ActivityType.watching)

bot = commands.InteractionBot(
    owner_id=OWNER, intents=intents, activity=activity, reload=True
)

bot.load_extensions("cogs")


if __name__ == "__main__":
    bot.run(getenv("TOKEN"))
