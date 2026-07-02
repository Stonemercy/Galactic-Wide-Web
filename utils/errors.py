from disnake.ext.commands import CheckFailure


class NotWhitelisted(CheckFailure):
    def __init__(self):
        super().__init__("User tried to use a whitelisted command.")


class NotReadyYet(CheckFailure):
    def __init__(self):
        super().__init__("The bot isn't ready yet.")
