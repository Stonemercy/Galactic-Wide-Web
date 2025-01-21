from data.lists import json_dict
from datetime import datetime, timedelta
from disnake import Activity, ActivityType, Intents
from disnake.ext import commands
from json import load
from logging import INFO, FileHandler, Formatter, getLogger
from os import getenv, listdir
from utils.interface_handler import InterfaceHandler
from utils.data import Data

MODERATOR_CHANNEL_ID = int(getenv("MODERATION_CHANNEL"))
FEEDBACK_CHANNEL_ID = int(getenv("FEEDBACK_CHANNEL"))
WASTE_BIN_CHANNEL_ID = int(getenv("WASTE_BIN_CHANNEL"))


class GalacticWideWebBot(commands.AutoShardedInteractionBot):
    def __init__(self):
        super().__init__(
            intents=Intents.default(),
            activity=Activity(name="for dissidents", type=ActivityType.watching),
        )
        self.logger = getLogger("disnake")
        self.logger.setLevel(INFO)
        handler = FileHandler(filename="disnake.log", encoding="utf-8", mode="w")
        handler.setFormatter(
            Formatter("%(asctime)s: %(levelname)s: %(name)s: %(message)s")
        )
        self.logger.addHandler(handler)
        self.startup_time = datetime.now()
        self.ready_time = self.startup_time + timedelta(seconds=30)
        self.interface_handler = InterfaceHandler(bot=self)
        self.json_dict = json_dict.copy()
        self.load_json()
        self.data = Data()
        self.command_usage = {}
        self.moderator_channel = None
        self.feedback_channel = None
        self.waste_bin_channel = None

    async def on_ready(self):
        await self.get_channels()
        self.logger.info(
            f"Loaded {len(self.cogs)}/{len([f for f in listdir('cogs') if f.endswith('.py')]) + len([f for f in listdir('cogs/admin') if f.endswith('.py')])} cogs successfully"
        )
        self.owner = [owner for owner in self.owners][0]
        self.owner_id = self.owner.id

    def load_json(self):
        for key, values in self.json_dict.copy().items():
            if "path" not in values:
                for second_key, second_values in values.items():
                    if "path" in second_values:
                        with open(second_values["path"], encoding="UTF-8") as json_file:
                            self.json_dict[key][second_key] = load(json_file)
                            continue
                continue
            else:
                with open(values["path"], encoding="UTF-8") as json_file:
                    self.json_dict[key] = load(json_file)

    async def get_channels(self):
        channel_dict = {
            "moderator_channel": MODERATOR_CHANNEL_ID,
            "feedback_channel": FEEDBACK_CHANNEL_ID,
            "waste_bin_channel": WASTE_BIN_CHANNEL_ID,
        }
        for attr, channel_id in channel_dict.items():
            while not getattr(self, attr):
                setattr(
                    self,
                    attr,
                    self.get_channel(channel_id)
                    or await self.fetch_channel(channel_id),
                )
