from utils.dbv2 import GWWGuilds

for guild in GWWGuilds(fetch_all=True):
    guild.delete()
