from datetime import datetime
from disnake import AppCmdInter
from disnake.ext import commands


def wait_for_startup():
    """Waits for the bot to be ready before allowing the interaction"""

    def predicate(inter: AppCmdInter):
        return datetime.now() > inter.bot.ready_time

    return commands.check(predicate)
