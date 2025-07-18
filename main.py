from os import getenv
from utils.bot import GalacticWideWebBot

bot = GalacticWideWebBot()
bot.load_extensions("cogs/admin")
bot.load_extensions("cogs")

if __name__ == "__main__":
    bot.run(getenv("TOKEN"))
