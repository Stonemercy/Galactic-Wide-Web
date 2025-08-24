from disnake.ext import commands


class NotWhitelisted(commands.CheckFailure):
    def __init__(self):
        super().__init__("You are not on the whitelist.")
