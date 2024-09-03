from datetime import datetime
from disnake import AppCmdInter
from disnake.ext import commands


def owner_only():
    def predicate(inter: AppCmdInter):
        return inter.author.id == inter.bot.owner_id

    return commands.check(predicate)


def wait_for_startup():
    def predicate(inter: AppCmdInter):
        return datetime.now() > inter.bot.ready_time

    return commands.check(predicate)
