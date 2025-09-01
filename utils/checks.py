from datetime import datetime
from disnake import AppCmdInter
from disnake.ext import commands
from utils.errors import NotWhitelisted


def wait_for_startup():
    """Waits for the bot to be ready before allowing the interaction"""

    def predicate(inter: AppCmdInter):
        return datetime.now() > inter.bot.ready_time

    return commands.check(predicate)


WHITELIST_SERVERS = [1368301807872512171]
WHITELIST_USERS = [164862382185644032]


def is_whitelisted():
    """A check that allows command invocation only by whitelisted users or members of whitelisted servers"""

    def predicate(inter: AppCmdInter):
        guild_id = inter.guild.id if inter.guild else None
        if inter.author.id not in WHITELIST_USERS and (
            guild_id is None or guild_id not in WHITELIST_SERVERS
        ):
            raise NotWhitelisted()
        return True

    return commands.check(predicate)
