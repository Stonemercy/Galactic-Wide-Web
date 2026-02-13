from disnake.ext import commands


class NotWhitelisted(commands.CheckFailure):
    def __init__(self):
        super().__init__("User tried to use a whitelisted command.")


class NotReadyYet(commands.CheckFailure):
    def __init__(self):
        super().__init__("The bot isn't ready yet.")
