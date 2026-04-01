from enum import Enum


class CampaignType(Enum):
    Liberation = 0
    Recon = 1
    HighPriority = 2
    Event = 4


class EventType(Enum):
    UrgentLiberation = 0
    Defence = 1
    Invasion = 2
