from disnake.ext import commands
from dotenv import load_dotenv
from os import getenv
from helpers.db import db_startup
from disnake import ActivityType, Intents, Activity

intents = Intents.default()
intents.members = True

load_dotenv("data/.env")
OWNER = int(getenv("OWNER"))

activity = Activity(name="for Socialism", type=ActivityType.watching)

bot = commands.InteractionBot(
    owner_id=OWNER, intents=intents, activity=activity, reload=True
)

bot.load_extensions("cogs")


@bot.event
async def on_ready():
    db_startup()
    print("===============================")
    print(f"{bot.user.name} is awake and ready for action!")
    print(f"Currently serving {len(bot.users)} users in {len(bot.guilds)} servers")
    print("===============================")


if __name__ == "__main__":
    bot.run(getenv("TOKEN"))
