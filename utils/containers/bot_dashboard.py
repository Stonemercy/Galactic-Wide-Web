from datetime import datetime, timezone
from disnake import Colour, OptionType, ui
from math import inf
from os import getpid
from psutil import Process, cpu_percent, net_io_counters, virtual_memory
from utils.bot import GalacticWideWebBot
from utils.functions import short_format
from utils.interactables.HDC_button import HDCButton
from utils.interactables.github_button import GitHubButton
from utils.interactables.ko_fi_button import KoFiButton
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION
class BotDashboardContainer(ui.Container, ReprMixin):
    def __init__(self, bot: GalacticWideWebBot, user_installs: int):
        self.components = []

        public_commands = [
            c
            for c in bot.global_slash_commands
            if c.name not in ["gwe", "global_event", "pmajor_order"]
        ]
        commands_text = f"## The GWW has {len(public_commands)} commands available\n"
        for global_command in sorted(public_commands, key=lambda sc: sc.name):
            for option in global_command.options:
                if option.type == OptionType.sub_command:
                    commands_text += (
                        f"</{global_command.name} {option.name}:{global_command.id}> "
                    )
            commands_text += f"</{global_command.name}:{global_command.id}> "
        self.components.extend([ui.TextDisplay(commands_text), ui.Separator()])

        quickest_server = sorted(
            bot.guilds, key=lambda x: (x.me.joined_at - x.created_at)
        )[0]
        self.components.append(
            ui.TextDisplay(
                f"**Fastest server to add the bot after creation**\n-# **{(quickest_server.me.joined_at - quickest_server.created_at).total_seconds():.0f} seconds**"
            )
        )

        servers_by_age = sorted(bot.guilds, key=lambda x: x.created_at)
        oldest_server = servers_by_age[0]
        newest_server = servers_by_age[-1]
        community_servers = len([g for g in bot.guilds if "COMMUNITY" in g.features])
        member_count = sum(guild.member_count for guild in bot.guilds)
        text_channels = sum(len(g.text_channels) for g in bot.guilds)
        voice_channels = sum(len(g.voice_channels) for g in bot.guilds)
        total_emojis = sum(len(g.emojis) for g in bot.guilds)
        self.components.append(
            ui.Section(
                ui.TextDisplay(
                    (
                        f"Servers: **{len(bot.guilds):,}**"
                        f"\n-# ├ Newest Server: Created **<t:{int(newest_server.created_at.timestamp())}:R>**"
                        f"\n-# ├ Oldest Server: Created **<t:{int(oldest_server.created_at.timestamp())}:R>**"
                        f"\n-# └ Community Servers: **{community_servers:,}**"
                        f"\nMembers of Democracy: **{member_count:,}**"
                        f"\nTotal Channels"
                        f"\n-# ├ Text: **{text_channels:,}**"
                        f"\n-# └ Voice: **{voice_channels:,}**"
                        f"\nEmojis: **{total_emojis:,}**"
                        f"\nUser installs: **{short_format(user_installs)}**"
                    )
                ),
                accessory=HDCButton(),
            )
        )

        self.components.append(ui.Separator())

        memory_used = Process(getpid()).memory_info().rss / 1024**3
        total_system_memory = virtual_memory().total / 1024**3
        memory_percentage = memory_used / total_system_memory
        memory_bar = "█" * round(memory_percentage / 100 * 30) + "░" * (
            30 - round(memory_percentage / 100 * 30)
        )
        latency = 9999.999 if bot.latency == float(inf) else bot.latency
        core_percents = cpu_percent(percpu=True)
        overall_cpu = cpu_percent()
        overall_bar = "█" * round(overall_cpu / 100 * 35) + "░" * (
            35 - round(overall_cpu / 100 * 35)
        )
        cpu_text = ""
        for i, percent in enumerate(core_percents, start=1):
            filled = round(percent / 100 * 5)
            bar = "█" * filled + "░" * (5 - filled)
            if i % 2:
                cpu_text += "\n"
            else:
                cpu_text += f"          "
            cpu_text += f"Core {i:2}: {bar} {percent:4.1f}%"

        self.components.append(
            ui.Section(
                ui.TextDisplay(
                    f"### :desktop: Hardware Info"
                    f"\n```CPU:"
                    f"\nOverall: {overall_bar} {overall_cpu:4.1f}%"
                    f"\n{cpu_text}"
                    f"\n\nRAM: {memory_bar} {memory_used:.2f}GB/{total_system_memory:.2f}GB```"
                    f"\n-# **Last restart**: <t:{int(bot.startup_time.timestamp())}:R>"
                    f"\n-# **Latency**: {int(latency * 1000)}ms"
                ),
                accessory=KoFiButton(),
            )
        )

        net_io = net_io_counters()
        bytes_sent_gb = net_io.bytes_sent / (1024**3)
        bytes_recv_gb = net_io.bytes_recv / (1024**3)

        self.components.append(
            ui.TextDisplay(
                f"### :satellite: Network Info\n-# **Sent**: {bytes_sent_gb:.2f}GB\n-# **Received:** {bytes_recv_gb:.2f}GB"
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
                ui.TextDisplay(f"### :jigsaw: Shards\n{shardinfo}"),
                accessory=GitHubButton(),
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
            if not loop.is_running() and not loop.count:
                loop_errors += f"{loop.coro.__name__} - **__ERROR__**:warning:\n"
                errors += 1
        if loop_errors:
            self.components.append(ui.Separator())
            self.components.append(ui.TextDisplay(f"# LOOP ERRORS\n{loop_errors}"))
        accent_colour = embed_colours.get(errors, Colour.from_rgb(0, 0, 0))
        self.components.append(
            ui.TextDisplay(
                f"-# Updated <t:{int(datetime.now(tz=timezone.utc).timestamp())}:R>"
            )
        )

        super().__init__(*self.components, accent_colour=accent_colour)
