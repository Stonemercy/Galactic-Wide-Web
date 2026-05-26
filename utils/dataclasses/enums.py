from enum import Enum


class CampaignType(Enum):
    Liberation = 0
    """Regular liberation campaigns"""
    Recon = 1
    """Campaigns that don't do any damage to planets"""
    HighPriority = 2
    """High priority campaigns that have a marker on the map"""
    Attrition = 3
    """Sieges tied to a global resource"""
    Event = 4
    """Campaigns with an event on the planet"""


class EventType(Enum):
    UrgentLiberation = 0
    """Planet is owned by non-human faction and marked on the map

    Planet changes owner if event is won by Helldivers"""
    Defence = 1
    """Human owned planet is attacked by the enemy with a duration
    
    Planet changes owner if event is won by Helldivers"""
    Invasion = 2
    """Human owned planet attacked by non-human faction
    
    Planet does not change owner if event is won"""


class SpaceStationType(Enum):
    UNKNOWN = 0
    DSS = 749875195


class AssignmentTaskType(Enum):
    """The names I have given for Assignment Task Types\n
    UNKNOWN = -1\n
    ExtractFromLocations = 1\n
    ExtractWithItem = 2\n
    KillEnemies = 3\n
    CompleteObjectives = 4\n
    PlayObjectives = 5\n
    UseItems = 6\n
    ExtractFromMission = 7\n
    CompleteOperations = 9\n
    DonateItems = 10\n
    LiberateLocationsSpecific = 11\n
    DefendFromAttacks = 12\n
    HoldLocationsUntilEnd = 13\n
    LiberateLocationsCount = 14\n
    NetLiberation = 15
    """

    UNKNOWN = -1

    ExtractFromLocations = 1
    ExtractWithItem = 2
    KillEnemies = 3
    CompleteObjectives = 4
    PlayObjectives = 5
    UseItems = 6
    ExtractFromMission = 7
    CompleteOperations = 9
    DonateItems = 10
    LiberateLocationsSpecific = 11
    DefendFromAttacks = 12
    HoldLocationsUntilEnd = 13
    LiberateLocationsCount = 14
    NetLiberation = 15

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN


class EventType(Enum):
    UrgentLiberation = 0
    Defence = 1
    Invasion = 2
