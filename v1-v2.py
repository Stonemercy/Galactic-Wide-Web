from utils.db import GWWGuild as GWWGuildV1
from utils.dbv2 import Feature, GWWGuild, GWWGuilds as GWWGuildsV2

all_old_guilds = GWWGuildV1.get_all()
print(f"Processing {len(all_old_guilds)} V1 guilds")
for count, old_guild in enumerate(all_old_guilds, 1):
    new_guild = None
    print("=" * 25)
    print(f"#{count} Processing guild: {old_guild.id}")
    active_features = []
    if old_guild.announcement_channel_id != 0:
        active_features.extend(
            [
                Feature(feature, old_guild.id, old_guild.announcement_channel_id)
                for feature in ["war_announcements", "dss_announcements"]
            ]
        )
    if old_guild.detailed_dispatches:
        active_features.append(
            Feature(
                "detailed_dispatches", old_guild.id, old_guild.announcement_channel_id
            )
        )
    if 0 not in (old_guild.dashboard_channel_id, old_guild.dashboard_message_id):
        active_features.append(
            Feature(
                "dashboards",
                old_guild.id,
                old_guild.dashboard_channel_id,
                old_guild.dashboard_message_id,
            )
        )
    if old_guild.major_order_updates:
        active_features.append(
            Feature(
                "major_order_updates", old_guild.id, old_guild.announcement_channel_id
            )
        )
    if 0 not in (old_guild.map_channel_id, old_guild.map_message_id):
        active_features.append(
            Feature(
                "maps", old_guild.id, old_guild.map_channel_id, old_guild.map_message_id
            )
        )
    if old_guild.patch_notes:
        active_features.append(
            Feature("patch_notes", old_guild.id, old_guild.announcement_channel_id)
        )

    new_guild: GWWGuild = GWWGuildsV2.add(old_guild.id, old_guild.language, [])
    new_guild.features.extend(active_features)
    new_guild.update_features()
    new_guild.save_changes()

    new_guild_entry = GWWGuildsV2.get_specific_guild(old_guild.id)
    if not new_guild_entry:
        print("GUILD ENTRY DIDNT WORK")
    else:
        print("GUILD ENTRY SUCCESSFUL")
