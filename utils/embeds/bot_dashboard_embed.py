from datetime import datetime
from disnake import Colour, Embed, OptionType
from math import inf
from os import getpid
from psutil import Process, cpu_percent
from utils.bot import GalacticWideWebBot
from utils.mixins import EmbedReprMixin


class BotDashboardEmbed(Embed, EmbedReprMixin):
    def __init__(self, bot: GalacticWideWebBot, user_installs: int):
        super().__init__(colour=Colour.green(), title="GWW Overview")
        now = datetime.now()
        self.description = (
            "This is the dashboard for all information about the GWW itself"
        )
        commands = ""
        for global_command in sorted(bot.global_slash_commands, key=lambda sc: sc.name):
            if global_command.name in ["gwe", "global_events"]:
                continue
            for option in global_command.options:
                if option.type == OptionType.sub_command:
                    commands += (
                        f"</{global_command.name} {option.name}:{global_command.id}> "
                    )
            if global_command.name != "weapons":
                commands += f"</{global_command.name}:{global_command.id}> "

        member_count = sum([guild.member_count for guild in bot.guilds])
        self.add_field(
            "The GWW has",
            f"{len(bot.global_slash_commands)} commands available:\n{commands}",
            inline=False,
        ).add_field("Currently in", f"{len(bot.guilds)} discord servers").add_field(
            "Members of Democracy", f"{member_count:,}"
        ).add_field(
            "Approx. user installs", user_installs
        )

        memory_used = Process(getpid()).memory_info().rss / 1024**2
        latency = 9999.999 if bot.latency == float(inf) else bot.latency
        self.add_field(
            "Hardware Info",
            (
                f"**CPU**: {cpu_percent()}%\n"
                f"**RAM**: {memory_used:.2f}MB\n"
                f"**Last restart**: <t:{int(bot.startup_time.timestamp())}:R>\n"
                f"**Latency**: {int(latency * 1000)}ms"
            ),
        )
        shardinfo = "\n".join(
            [
                f"Shard **#{shard.id}** - **{shard.latency * 1000:.0f}ms**"
                for shard in bot.shards.values()
            ]
        )
        self.add_field("Shards", f"Total Shards: {bot.shard_count}\n{shardinfo}")
        self.add_field("", "", inline=False)
        self.add_field(
            "Credits",
            (
                "https://helldivers.wiki.gg/ - Most of my enemy information is from them, as well as a lot of the enemy images.\n\n"
                "https://helldivers.news/ - Planet images are from them\n\n"
                "https://github.com/helldivers-2/ - The people over here are kind and helpful, great work too!\n\n"
                "and **You**\n"
            ),
            inline=False,
        )
        loop_errors = ""
        for loop in bot.loops:
            if not loop.next_iteration and not loop.count:
                loop_errors += f"{loop.coro.__name__} - **__ERROR__**:warning:\n"
        if loop_errors:
            self.add_field("Loop errors", loop_errors, inline=False)
        self.add_field("", f"-# Updated <t:{int(now.timestamp())}:R>")
