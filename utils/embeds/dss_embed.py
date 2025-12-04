from data.lists import CUSTOM_COLOURS
from datetime import datetime
from disnake import Colour, Embed
from utils.api_wrapper.models import DSS
from utils.emojis import Emojis
from utils.functions import health_bar
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTrackerEntry

STATUSES = {
    0: "inactive",
    1: "preparing",
    2: "active",
    3: "on_cooldown",
}


class DSSEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        language_json: dict,
        dss_data: DSS,
    ):
        super().__init__(
            title=language_json["wiki"]["embeds"]["DSSEmbed"]["title"],
            colour=Colour.from_rgb(*CUSTOM_COLOURS["DSS"]),
        )
        if dss_data.flags == 2:
            self.add_field("The DSS is currently unavailable.", "")
            self.colour = Colour.brand_red()
            return
        self.description = language_json["wiki"]["embeds"]["DSSEmbed"][
            "stationed_at"
        ].format(
            planet=dss_data.planet.loc_names[language_json["code_long"]],
            faction_emoji=getattr(
                Emojis.Factions, dss_data.planet.faction.full_name.lower()
            ),
        )
        self.description += language_json["wiki"]["embeds"]["DSSEmbed"][
            "next_move"
        ].format(timestamp=f"<t:{int(dss_data.move_timer_datetime.timestamp())}:R>")
        self.set_thumbnail(
            "https://media.discordapp.net/attachments/1212735927223590974/1413612410819969114/0xfbbeedfa99b09fec.png?ex=68bc90a6&is=68bb3f26&hm=cd8bf236a355bbed28f4847d3d62b5908d050a7eeb7396bb9a891e108acc0241&=&format=webp&quality=lossless"
        ).set_image(
            "https://cdn.discordapp.com/attachments/1212735927223590974/1312448218398986331/dss.jpg?ex=674c8827&is=674b36a7&hm=def01cbdf1920b85617b1028a95ec982484c70a5cf9bed14b9072319fd018246&"
        )
        for tactical_action in dss_data.tactical_actions:
            tactical_action: DSS.TacticalAction
            status = STATUSES[tactical_action.status]
            if status == "preparing":
                cost = ""
                for ta_cost in tactical_action.cost:
                    ta_cost_change: BaseTrackerEntry = tactical_action.cost_changes[
                        ta_cost.item
                    ]
                    change_text = ""
                    if ta_cost_change and ta_cost_change.change_rate_per_hour != 0:
                        change = f"{ta_cost_change.change_rate_per_hour:+.2%}/hr"
                        change_text = f"\n`{change:^25}`"
                        change_text += f"\n-# {language_json['embeds']['Dashboard']['DSSEmbed']['active']} <t:{int(datetime.now().timestamp() + ta_cost_change.seconds_until_complete)}:R>"
                        ta_cost_health_bar = health_bar(
                            ta_cost.progress,
                            "MO" if ta_cost.progress != 1 else "Humans",
                            anim=True,
                            increasing=ta_cost_change.change_rate_per_hour > 0,
                        )
                    else:
                        ta_cost_health_bar = health_bar(
                            ta_cost.progress,
                            "MO" if ta_cost.progress != 1 else "Humans",
                        )
                    cost = (
                        f"{ta_cost_health_bar}\n"
                        f"`{ta_cost.progress:^25.2%}`"
                        f"{change_text}"
                    )
            elif status == "active":
                cost = f"{language_json['wiki']['embeds']['DSSEmbed']['on_cooldown'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            elif status == "on_cooldown":
                cost = f"{language_json['wiki']['embeds']['DSSEmbed']['preparing'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            else:
                continue
            localized_ta = language_json["wiki"]["embeds"]["DSSEmbed"][
                "tactical_actions"
            ].get(
                tactical_action.name,
                {
                    "name": tactical_action.name,
                    "description": tactical_action.description,
                },
            )
            self.add_field(
                f"{tactical_action.emoji} {localized_ta['name']}",
                (
                    f"{language_json['wiki']['embeds']['DSSEmbed']['status']}: **{language_json['wiki']['embeds']['DSSEmbed'][status].capitalize()}**"
                    f"\n{localized_ta['description']}"
                    f"\n{cost}\n\u200b\n"
                ),
                inline=False,
            )
        if dss_data.votes:
            votes_text = "Current Votes:"
            for index, planet_votes_dict in enumerate(
                sorted(
                    dss_data.votes.available_planets,
                    key=lambda x: x[1],
                    reverse=True,
                ),
                start=1,
            ):
                votes_text += f"\n-# #{index} - {planet_votes_dict[0].faction.emoji} {planet_votes_dict[0].loc_names[language_json['code_long']]} - ({(planet_votes_dict[1]/dss_data.votes.total_votes):.0%})"
            self.add_field("", votes_text, inline=False)
