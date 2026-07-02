from datetime import datetime, timedelta, timezone
from data.lists import CUSTOM_COLOURS
from disnake import ButtonStyle, Colour, MediaGalleryItem
from disnake.ui import (
    ActionRow,
    Button,
    Container,
    MediaGallery,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)
from utils.api_wrapper.models import ControlCentre, Dispatch
from utils.dataclasses.enums import ControlCentreStatus, ControlCentrePage
from utils.emojis import Emojis
from utils.interactables import (
    ActiveCampaignButton,
    OverviewButton,
    PastCampaignsButton,
)
from utils.interactables.control_centre import ControlCentreActiveCampaignsStringSelect

STATUS_DICT = {
    ControlCentreStatus.InProgress: "IN PROGRESS",
    ControlCentreStatus.Success: "SUCCESS",
    ControlCentreStatus.Failed: "FAILURE",
}


class ControlCentreContainer(Container):
    def __init__(
        self,
        control_centre: ControlCentre,
        required_images: list[str],
        dispatches: list[Dispatch],
        page: ControlCentrePage,
        phase_id: int = None,
        episode_id: int = None,
    ):
        self.control_centre = control_centre
        self.required_images = required_images
        self.dispatches = dispatches
        self.phase_id = phase_id
        self.episode_id = episode_id
        self.components = []
        self.accent_colour = Colour.from_rgb(*CUSTOM_COLOURS["MO"])

        match page:
            case ControlCentrePage.Overview:
                self.add_overview_page()
            case ControlCentrePage.ActiveCampaign:
                self.add_active_campaign_page()
            case ControlCentrePage.PastCampaigns:
                self.add_past_campaigns_page()

        self.components.append(
            ActionRow(
                *(
                    OverviewButton(is_active=page == ControlCentrePage.Overview),
                    ActiveCampaignButton(
                        is_active=page == ControlCentrePage.ActiveCampaign
                    ),
                    PastCampaignsButton(
                        is_active=page == ControlCentrePage.PastCampaigns
                    ),
                )
            )
        )

        super().__init__(*self.components, accent_colour=self.accent_colour)

    def add_overview_page(self):
        section1 = []
        active_campaign = next(
            (e for e in self.control_centre.episodes[::-1]),
            None,
        )
        self.accent_color = Colour.from_rgb(
            *active_campaign.faction.colour if active_campaign.faction else (0, 0, 0)
        )
        section1.append(TextDisplay("## **Active Campaign**"))

        if active_campaign.image_id != 0:
            image_id = f"{active_campaign.image_id}.png"
            if image_id in self.required_images:
                section1.append(
                    MediaGallery(MediaGalleryItem(f"attachment://{image_id}"))
                )
            else:
                section1.append(
                    TextDisplay(
                        "-# Image unavailable. Please contact GWW admin to have this fixed."
                    )
                )
        faction_emoji = (
            active_campaign.faction.emoji
            if active_campaign.faction
            else Emojis.Factions.humans
        )
        section1.append(
            TextDisplay(
                f"# {faction_emoji} **{active_campaign.title}** {faction_emoji}"
                f"\n{active_campaign.description}"
            )
        )
        self.components.extend(section1 + [Separator()])

        section2 = []
        active_phase = next(
            (p for p in active_campaign.phases[::-1]),
            None,
        )
        section2.append(TextDisplay("## **Active Major Order**"))
        if not active_phase:
            section2.append(TextDisplay("### No Major Order active"))
        else:
            reward_result_emoji = ""
            match active_phase.status:
                case ControlCentreStatus.InProgress:
                    section2.append(
                        TextDisplay(
                            "### Complete the Major Order to earn the Major Order Reward."
                        )
                    )
                case ControlCentreStatus.Success:
                    section2.append(
                        TextDisplay(
                            "### Major Order was successfully completed and reward paid out to participants."
                        )
                    )
                    reward_result_emoji = "✅"
                case ControlCentreStatus.Failed:
                    section2.append(
                        TextDisplay(
                            "### Major Order was failed and no reward was paid out."
                        )
                    )
                    reward_result_emoji = "❌"
                case _:
                    section2.append(
                        TextDisplay("### Unknown status."),
                    )
            section2.append(TextDisplay("## **Major Order Reward**"))
            mo_rewards_text = ""
            for reward in active_phase.rewards:
                mo_rewards_text += f"**{reward.amount}** x {reward.item_name} {reward.emoji} {reward_result_emoji}"

            if mo_rewards_text != "":
                section2.append(TextDisplay(mo_rewards_text))

        section2.append(TextDisplay("## **Campaign Reward**"))
        reward_result_emoji = ""
        match active_campaign.status:
            case ControlCentreStatus.InProgress:
                section2.append(
                    TextDisplay(
                        "### Complete the majority of the Major Orders in this Campaign to earn the Campaign Reward."
                    ),
                )
            case ControlCentreStatus.Success:
                section2.append(
                    TextDisplay(
                        "### Campaign was successfully completed and reward paid out to participants."
                    )
                )
                reward_result_emoji = "✅"
            case ControlCentreStatus.Failed:
                section2.append(
                    TextDisplay("### Campaign was failed and no reward was paid out.")
                )
                reward_result_emoji = "❌"
            case _:
                section2.append(TextDisplay("### Unknown Status."))
        campaign_rewards_text = ""
        for reward in active_campaign.rewards:
            campaign_rewards_text += f"**{reward.amount}** x {reward.item_name} {reward.emoji} {reward_result_emoji}"
        if campaign_rewards_text != "":
            section2.append(TextDisplay(campaign_rewards_text))
        self.components.extend(section2 + [Separator()])

        section3 = []
        section3.append(TextDisplay(f"## {Emojis.Factions.humans} Dispatches"))
        time_cutoff = datetime.now(tz=timezone.utc) - timedelta(days=3)
        for dispatch in [
            d for d in self.dispatches[::-1][:2] if d.published_at > time_cutoff
        ]:
            section3.append(
                TextDisplay(
                    f"### {dispatch.title}"
                    f"\n{dispatch.description}"
                    f"\n<t:{int(dispatch.published_at.timestamp())}:R>"
                )
            )
        self.components.extend(section3 + [Separator()])

    def add_active_campaign_page(self):
        campaign = (
            self.control_centre.episodes[-1]
            if not self.episode_id
            else next(
                (e for e in self.control_centre.episodes if e.id == self.episode_id)
            )
        )
        phase = (
            campaign.phases[-1]
            if not self.phase_id
            else next((p for p in campaign.phases if p.id == self.phase_id))
        )
        index = campaign.phases.index(phase)

        section1 = []
        section1.append(TextDisplay("## **Major Order Briefing**"))
        if image_id := phase.outro_image_id or phase.intro_image_id:
            image_id = f"{image_id}.png"
            if image_id in self.required_images:
                section1.append(
                    MediaGallery(MediaGalleryItem(f"attachment://{image_id}"))
                )
            else:
                section1.append(
                    TextDisplay(
                        "-# Image unavailable. Please contact GWW admin to have this fixed."
                    )
                )
        faction_emoji = (
            campaign.faction.emoji if campaign.faction else Emojis.Factions.humans
        )
        section1.append(
            TextDisplay(
                f"-# {campaign.title} {index + 1}/{len(campaign.phases)}"
                f"\n# {faction_emoji} **{phase.intro_title}** {faction_emoji}"
                f"\n**Outcome - {STATUS_DICT.get(phase.status, 'UNKNOWN')}**"
                f"\n{phase.intro_message if phase.status == ControlCentreStatus.InProgress else phase.outro_message}"
            )
        )
        self.accent_color = Colour.from_rgb(*campaign.faction.colour)
        self.components.extend(section1 + [Separator()])

        section2 = []
        section2.append(TextDisplay("## **Major Order Reward**"))
        reward_result_emoji = ""
        match phase.status:
            case ControlCentreStatus.InProgress:
                section2.append(
                    TextDisplay(
                        "### Complete the Major Order to earn the Major Order Reward."
                    )
                )
            case ControlCentreStatus.Success:
                section2.append(
                    TextDisplay(
                        "### Major Order was successfully completed and reward paid out to participants."
                    )
                )
                reward_result_emoji = "✅"
            case ControlCentreStatus.Failed:
                section2.append(
                    TextDisplay(
                        "### Major Order was failed and no reward was paid out."
                    )
                )
                reward_result_emoji = "❌"
            case _:
                section2.append(
                    TextDisplay("### Unknown Status"),
                )
        mo_rewards_text = ""
        for reward in phase.rewards:
            mo_rewards_text += f"**{reward.amount}** x {reward.item_name} {reward.emoji} {reward_result_emoji}"
        if mo_rewards_text != "":
            section2.append(TextDisplay(mo_rewards_text))

        section2.append(TextDisplay("## **Campaign Reward**"))
        reward_result_emoji = ""
        match campaign.status:
            case ControlCentreStatus.InProgress:
                section2.append(
                    TextDisplay(
                        "### Complete the majority of the Major Orders in this Campaign to earn the Campaign Reward."
                    ),
                )
            case ControlCentreStatus.Success:
                section2.append(
                    TextDisplay(
                        "### Campaign was successfully completed and reward paid out to participants."
                    )
                )
                reward_result_emoji = "✅"
            case ControlCentreStatus.Failed:
                section2.append(
                    TextDisplay("### Campaign was failed and no reward was paid out.")
                )
                reward_result_emoji = "❌"
            case _:
                section2.append(TextDisplay("### Unknown status."))
        campaign_rewards_text = ""
        for reward in campaign.rewards:
            campaign_rewards_text += f"**{reward.amount}** x {reward.item_name} {reward.emoji} {reward_result_emoji}"
        if campaign_rewards_text != "":
            section2.append(TextDisplay(campaign_rewards_text))
        self.components.extend(section2 + [Separator()])

        self.components.extend(
            [
                ActionRow(
                    ControlCentreActiveCampaignsStringSelect(
                        campaign.id, campaign.phases
                    )
                ),
                Separator(),
            ]
        )

    def add_past_campaigns_page(self):
        archive_sections = []
        for campaign in self.control_centre.episodes:
            if campaign.status == ControlCentreStatus.InProgress:
                continue

            section = []
            title = TextDisplay(
                f"-# Archive Data Entry"
                + " " * 115
                + f"<t:{int(campaign.end_time_datetime.timestamp())}:R>"
            )

            if f"{campaign.image_id}.png" in self.required_images:
                accessory = Thumbnail(f"attachment://{campaign.image_id}.png")
                needs_button = True
            else:
                accessory = Button(
                    style=ButtonStyle.blurple,
                    label="View",
                    custom_id=f"control_centre_{campaign.id}",
                )
                needs_button = False

            description = (
                f"## {campaign.faction.emoji} {campaign.title} {campaign.faction.emoji}"
            )
            description += f"\n### {STATUS_DICT[campaign.status]}"
            match campaign.status:
                case ControlCentreStatus.Failed:
                    description += " ❌"
                case ControlCentreStatus.Success:
                    description += " ✅"
            description += f"\n{campaign.description}"
            description = TextDisplay(description)

            section.append(Section(title, description, accessory=accessory))
            if needs_button:
                section.append(
                    ActionRow(
                        Button(
                            style=ButtonStyle.blurple,
                            emoji=Emojis.Stratagems.up,
                            label=f"View",
                            custom_id=f"control_centre_{campaign.id}",
                        )
                    )
                )
            section.append(Separator())
            archive_sections.extend(section)

        self.components.extend(archive_sections)
