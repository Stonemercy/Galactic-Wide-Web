from datetime import datetime
from disnake import Colour, OptionType, ui
from math import inf
from os import getpid
from psutil import Process, cpu_percent
from utils.bot import GalacticWideWebBot
from utils.interactables.HDC_button import HDCButton
from utils.interactables.github_button import GitHubButton
from utils.interactables.ko_fi_button import KoFiButton
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION
class BotDashboardContainer(ui.Container, ReprMixin):
    def __init__(self, bot: GalacticWideWebBot, user_installs: int):
        now = datetime.now()
        self.components = []
        commands_text = f"## The GWW has {len([c for c in bot.global_slash_commands if c.name not in ['gwe', 'global_event']])} commands available\n"
        for global_command in sorted(bot.global_slash_commands, key=lambda sc: sc.name):
            if global_command.name not in ["gwe", "global_event"]:
                for option in global_command.options:
                    if option.type == OptionType.sub_command:
                        commands_text += f"</{global_command.name} {option.name}:{global_command.id}> "
                commands_text += f"</{global_command.name}:{global_command.id}> "
        self.components.append(ui.TextDisplay(commands_text))

        self.components.append(ui.Separator())

        member_count = sum([guild.member_count for guild in bot.guilds])
        self.components.append(
            ui.Section(
                ui.TextDisplay(
                    (
                        f"Currently in **{len(bot.guilds)}** discord servers"
                        f"\n**{member_count:,}** Members of Democracy"
                        f"\n**{user_installs}** Approx. user installs"
                    )
                ),
                accessory=HDCButton(),
            )
        )

        self.components.append(ui.Separator())

        memory_used = Process(getpid()).memory_info().rss / 1024**2
        latency = 9999.999 if bot.latency == float(inf) else bot.latency
        self.components.append(
            ui.Section(
                ui.TextDisplay(
                    f"### Hardware Info\n-# **CPU**: {cpu_percent()}%\n-# **RAM**: {memory_used:.2f}MB\n-# **Last restart**: <t:{int(bot.startup_time.timestamp())}:R>\n-# **Latency**: {int(latency * 1000)}ms"
                ),
                accessory=KoFiButton(),
            )
        )

        self.components.append(ui.Separator())

        shardinfo = "\n".join(
            [
                f"-# **#{shard.id + 1}** - **{shard.latency * 1000:.0f}ms** - {len([g for g in bot.guilds if g.shard_id == shard.id])} Guilds"
                for shard in bot.shards.values()
            ]
        )
        self.components.append(
            ui.Section(
                ui.TextDisplay(f"### Shards\n{shardinfo}"), accessory=GitHubButton()
            )
        )
        loop_errors = ""
        embed_colours = {
            0: Colour.brand_green(),
            1: Colour.orange(),
            2: Colour.brand_red(),
        }
        errors = 0
        for loop in bot.loops:
            if not loop.next_iteration and not loop.count:
                loop_errors += f"{loop.coro.__name__} - **__ERROR__**:warning:\n"
                errors += 1
        if loop_errors:
            self.components.append(ui.Separator())
            self.components.append(ui.TextDisplay(f"# LOOP ERRORS\n{loop_errors}"))
        accent_colour = embed_colours.get(errors, Colour.from_rgb(0, 0, 0))
        self.components.append(
            ui.TextDisplay(f"-# Updated <t:{int(now.timestamp())}:R>")
        )

        super().__init__(*self.components, accent_colour=accent_colour)
