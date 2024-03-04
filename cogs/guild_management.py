from disnake import AppCmdInter, Guild
from disnake.ext import commands
from helpers.db import Guilds
from os import getenv


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Guild Management cog has finished loading")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        channel_id = int(getenv("MODERATION_CHANNEL"))
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
            channel_id
        )
        Guilds.set_info(guild_id=guild.id)
        await guild.owner.send(
            "Thanks for joining the Galactic Wide Web, use the `/setup` command to start observing Democracy!"
        )
        await channel.send(
            f"Just joined server #{len(self.bot.guilds)} `{guild.name}` with {guild.member_count} members"
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        channel_id = int(getenv("MODERATION_CHANNEL"))
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
            channel_id
        )
        Guilds.remove_from_db(guild.id)
        await channel.send(
            f"Just left `{guild.name}`, down to {len(self.bot.guilds)} servers"
        )

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def info(self, inter: AppCmdInter):
        await inter.send(
            (f"Guilds: {len(inter.bot.guilds)}\n", f"Users: {len(inter.bot.users)}")
        )

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def delete_message(self, inter: AppCmdInter, channel_id, message_id):
        try:
            channel = self.bot.get_channel(
                int(channel_id)
            ) or await self.bot.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            if message.author != self.bot.user:
                await inter.send(
                    "I won't delete messages that arent my own", ephemeral=True
                )
            await message.delete()
        except Exception as e:
            await inter.send(f"Couldn't do it:\n{e}", ephemeral=True)
        else:
            await inter.send("That worked", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(GuildManagementCog(bot))
