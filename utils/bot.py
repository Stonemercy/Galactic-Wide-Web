from datetime import datetime, timedelta
from json import load
from logging import INFO, FileHandler, Formatter, getLogger
from os import getenv, listdir
from disnake import Activity, ActivityType, Intents
from disnake.ext import commands
from utils.data import Data
from data.lists import json_dict


class GalacticWideWebBot(commands.InteractionBot):
    def __init__(self):
        super().__init__(
            intents=Intents.default(),
            activity=Activity(name="for Socialism", type=ActivityType.watching),
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
        self.dashboard_messages = []
        self.announcement_channels = []
        self.patch_channels = []
        self.map_messages = []
        self.major_order_channels = []
        self.c_n_m_loaded = False
        self.json_dict = json_dict.copy()
        self.load_json()
        self.data = Data()
        self.command_usage = {}

    async def on_ready(self):
        self.moderator_channel = self.get_channel(int(getenv("MODERATION_CHANNEL")))
        self.feedback_channel = self.get_channel(int(getenv("FEEDBACK_CHANNEL")))
        self.waste_bin_channel = self.get_channel(int(getenv("WASTE_BIN_CHANNEL")))
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
