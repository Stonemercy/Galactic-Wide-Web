from aiohttp import ClientSession
from datetime import datetime
from disnake import Colour, Embed
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from utils.bot import GalacticWideWebBot
from utils.emojis import Emojis


class GithubWatcherCog(Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.latest_sha: str = ""

    def cog_load(self) -> None:
        if not self.github_check.is_running():
            self.github_check.start()
            self.bot.loops.append(self.github_check)

    def cog_unload(self) -> None:
        if self.github_check.is_running():
            self.github_check.cancel()
        if self.github_check in self.bot.loops:
            self.bot.loops.remove(self.github_check)

    @loop(minutes=1)
    async def github_check(self) -> None:
        if not self.bot.ready:
            self.bot.logger.warning("github_check loop returning - the bot isn't ready")
            return
        async with ClientSession() as session:
            async with session.get(
                "https://api.github.com/repos/Stonemercy/Galactic-Wide-Web/commits"
            ) as response:
                if response.status == 200:
                    commits: list[dict] = await response.json()
                    commits = commits[::-1]
                else:
                    self.bot.logger.warning(
                        f"github_check loop - request returned {response.status}"
                    )
                    return

                if self.latest_sha == "":
                    self.latest_sha = commits[-1]["sha"]
                    self.bot.logger.info(
                        f"github_check loop - no sha found, using latest ({self.latest_sha})"
                    )
                else:
                    if (
                        latest_commit := next(
                            (c for c in commits if c["sha"] == self.latest_sha), None
                        )
                    ) is not None:
                        last_commit_index = commits.index(latest_commit)
                    else:
                        last_commit_index = -1
                    embeds = []
                    new_commits = commits[last_commit_index + 1 :]
                    for j, chunk in enumerate(
                        [
                            new_commits[i : i + 16]
                            for i in range(0, len(new_commits), 16)
                        ],
                        start=1,
                    ):
                        embed = Embed(
                            title=f"{Emojis.Icons.github} New bot updates!",
                            colour=Colour.brand_green(),
                        )
                        if len(new_commits) > 16:
                            embed.title += f" #{j}"
                        for i, commit in enumerate(
                            [c for c in chunk],
                            start=1,
                        ):
                            embed.add_field(
                                "",
                                (
                                    f"\n-# {commit['commit']['message']}"
                                    f"\n-# <t:{int(datetime.fromisoformat(commit['commit']['committer']['date']).timestamp())}:R>"
                                ),
                            )
                            if i % 2:
                                embed.add_field("", "")

                        if len(embed.fields) > 0:
                            embeds.append(embed)

                    if embeds != []:
                        try:
                            message = await self.bot.channels.dev_progress_channel.send(
                                embeds=embeds
                            )
                            await message.publish()
                        except:
                            return
                        self.latest_sha = commits[-1]["sha"]
                        self.bot.logger.info(
                            f"github_check successfully sent out {j} message(s)"
                        )

    @github_check.before_loop
    async def before_github_check(self) -> None:
        await self.bot.wait_until_ready()

    @github_check.error
    async def github_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "github_check loop")


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(GithubWatcherCog(bot))
