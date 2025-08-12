from dataclasses import dataclass
from disnake import Locale
from utils.emojis import Emojis

language_dict = {
    "English": "en",
    "Français": "fr",
    "Deutsch": "de",
    "Italian": "it",
    "Brazilian Portuguese": "pt-br",
    "Russian": "ru",
    "Spanish": "es",
}
"""Dictionary of languages supported by the bot

Format:

    "Full Language Name": "language-code"
    
Example:

    "English": "en"
"""

locales_dict = {
    Locale.fr: "fr",
    Locale.de: "de",
    Locale.it: "it",
    Locale.pt_BR: "pt-br",
    Locale.ru: "ru",
    Locale.es_ES: "es",
    Locale.es_LATAM: "es",
}
"""Dictionary of locales supported by the bot

Format:

    Disnake.Locale: "language-code"
    
Example:

    Locale.en_GB: "en"
"""

json_dict = {
    "languages": {
        "en": {"path": "data/languages/en.json", "value": None},
        "fr": {"path": "data/languages/fr.json", "value": None},
        "de": {"path": "data/languages/de.json", "value": None},
        "it": {"path": "data/languages/it.json", "value": None},
        "pt-br": {"path": "data/languages/pt-br.json", "value": None},
        "ru": {"path": "data/languages/ru.json", "value": None},
        "es": {"path": "data/languages/es.json", "value": None},
    },
    "stratagems": {"path": "data/json/stratagems/stratagems.json", "value": None},
    "warbonds": {
        "index": {"path": "data/json/warbonds.json", "value": None},
        "helldivers_mobilize": {
            "path": "data/json/warbonds/helldivers_mobilize.json",
            "value": None,
        },
        "steeled_veterans": {
            "path": "data/json/warbonds/steeled_veterans.json",
            "value": None,
        },
        "cutting_edge": {"path": "data/json/warbonds/cutting_edge.json", "value": None},
        "democratic_detonation": {
            "path": "data/json/warbonds/democratic_detonation.json",
            "value": None,
        },
        "polar_patriots": {
            "path": "data/json/warbonds/polar_patriots.json",
            "value": None,
        },
        "viper_commandos": {
            "path": "data/json/warbonds/viper_commandos.json",
            "value": None,
        },
        "freedoms_flame": {
            "path": "data/json/warbonds/freedoms_flame.json",
            "value": None,
        },
        "chemical_agents": {
            "path": "data/json/warbonds/chemical_agents.json",
            "value": None,
        },
        "truth_enforcers": {
            "path": "data/json/warbonds/truth_enforcers.json",
            "value": None,
        },
        "urban_legends": {
            "path": "data/json/warbonds/urban_legends.json",
            "value": None,
        },
        "servants_of_freedom": {
            "path": "data/json/warbonds/servants_of_freedom.json",
            "value": None,
        },
        "borderline_justice": {
            "path": "data/json/warbonds/borderline_justice.json",
            "value": None,
        },
        "masters_of_ceremony": {
            "path": "data/json/warbonds/masters_of_ceremony.json",
            "value": None,
        },
        "force_of_law": {
            "path": "data/json/warbonds/force_of_law.json",
            "value": None,
        },
        "control_group": {
            "path": "data/json/warbonds/control_group.json",
            "value": None,
        },
    },
    "planets": {"path": "data/json/planets/planets.json", "value": None},
    "planetRegions": {"path": "data/json/planets/planetRegions.json", "value": None},
    "sectors": {"path": "data/json/planets/sectors.json", "value": None},
    "items": {
        "item_names": {"path": "data/json/items/item_names.json", "value": None},
        "armor": {"path": "data/json/items/armor/armor.json", "value": None},
        "armor_perks": {"path": "data/json/items/armor/passive.json", "value": None},
        "armor_slots": {"path": "data/json/items/armor/slot.json", "value": None},
        "primary_weapons": {
            "path": "data/json/items/weapons/primary.json",
            "value": None,
        },
        "secondary_weapons": {
            "path": "data/json/items/weapons/secondary.json",
            "value": None,
        },
        "grenades": {"path": "data/json/items/weapons/grenades.json", "value": None},
        "weapon_types": {"path": "data/json/items/weapons/types.json", "value": None},
        "weapon_traits": {"path": "data/json/items/weapons/traits.json", "value": None},
        "fire_modes": {
            "path": "data/json/items/weapons/fire_modes.json",
            "value": None,
        },
        "boosters": {"path": "data/json/items/boosters.json", "value": None},
        "reward_types": {
            "path": "data/json/assignments/reward/type.json",
            "value": None,
        },
    },
    "enemies": {
        "enemy_ids": {"path": "data/json_custom/enemies/enemy_ids.json", "value": None},
        "automaton": {"path": "data/json_custom/enemies/automaton.json", "value": None},
        "illuminate": {
            "path": "data/json_custom/enemies/illuminate.json",
            "value": None,
        },
        "terminids": {"path": "data/json_custom/enemies/terminids.json", "value": None},
    },
    "planet_effects": {"path": "data/json/effects/planetEffects.json", "value": None},
}

faction_colours = {
    "Automaton": (252, 108, 115),
    "Terminids": (234, 167, 43),
    "Illuminate": (107, 59, 187),
    "Humans": (107, 183, 234),
    "MO": (255, 220, 0),
    "DSS": (214, 232, 248),
}
"""Dictionary of Colours used by the bot

Format:

    "faction": (int, int, int)

Exmaple:

    "Automaton": (214, 232, 248)
"""

warbond_images_dict = {
    "Helldivers Mobilize": "https://media.discordapp.net/attachments/1212735927223590974/1234539583086264320/helldivers_mobilize.png?ex=66311a15&is=662fc895&hm=917734dcbeeb5b89a6d3a48c17fff8af49524c9c7187506e7d4ef8a6f37c8a00&=&format=webp&quality=lossless",
    "Steeled Veterans": "https://media.discordapp.net/attachments/1212735927223590974/1234539583438589952/steeled_veterans.png?ex=66311a15&is=662fc895&hm=3f5e97569e7581af8c0aa86b1fa39c48d29b0a6f557cbd9a5b09d77bbf6854fb&=&format=webp&quality=lossless",
    "Cutting Edge": "https://media.discordapp.net/attachments/1212735927223590974/1234539582268112987/cutting_edge.png?ex=66311a15&is=662fc895&hm=152ca52dfb6499f403d77e5fc223252a36c612315d1a8eaabec3f4ca9165ffdf&=&format=webp&quality=lossless",
    "Democratic Detonation": "https://media.discordapp.net/attachments/1212735927223590974/1234539582671032441/democratic_detonation.png?ex=66311a15&is=662fc895&hm=a7ea39cebf97692bce42f0f1ef04b535b4e241279860439f87a1b13dda7c13b6&=&format=webp&quality=lossless",
    "Polar Patriots": "https://cdn.discordapp.com/attachments/1212735927223590974/1243556076113235978/polar_patriots.png?ex=6651e758&is=665095d8&hm=5892cb4b53945d328c6cc8e322f96a6dd42bbc1ab00af03ca8f0026564c13e8a&",
    "Viper Commandos": "https://cdn.discordapp.com/attachments/1212735927223590974/1250840006356893757/viper_commandos.png?ex=666c6708&is=666b1588&hm=14b58f35a78fdbc87aaf285fb02154a814778ededbccc870930261899cf12bef&",
    "Freedom's Flame": "https://cdn.discordapp.com/attachments/1212735927223590974/1283844729632591985/freedoms_flame.png?ex=66e47914&is=66e32794&hm=3a3d1bb0b9f67dbeb2f63e625511130971fc888d81d36b393996fe1771517fc8&",
    "Chemical Agents": "https://cdn.discordapp.com/attachments/1212735927223590974/1286254303001972736/chemical_agents.png?ex=66ed3d2b&is=66ebebab&hm=510de52a270f795006e61129f83f0e0b70bf438a042b8b2d9859111806574cf3&",
    "Truth Enforcers": "https://media.discordapp.net/attachments/1212735927223590974/1301502200849104947/truth_enforcers.png?ex=6724b5e1&is=67236461&hm=c36872146e2ac4fbbaac4ddab19a291927d2e938c6a3cdd00a9b333408e54d1e&=&format=webp&quality=lossless&width=1202&height=676",
    "Urban Legends": "https://cdn.discordapp.com/attachments/1212735927223590974/1317150385047081110/urban_legends.png?ex=675da363&is=675c51e3&hm=5e894ce871829ccc6ce2899b695692b15a08aad3921f0c390b14cd3b4685ce2c&",
    "Servants of Freedom": "https://helldivers.wiki.gg/images/thumb/a/a9/Servants_of_Freedom_Premium_Warbond_Cover.png/1280px-Servants_of_Freedom_Premium_Warbond_Cover.png?e4ff67",
    "Borderline Justice": "https://helldivers.wiki.gg/images/d/db/Borderline_Justice_Premium_Warbond_Cover.png?df22f7=&format=original",
    "Masters of Ceremony": "https://helldivers.wiki.gg/images/6/65/Masters_of_Ceremony_Premium_Warbond_Cover.png?6bb032=&format=original",
    "Force of Law": "https://helldivers.wiki.gg/images/7/74/Force_of_Law_Premium_Warbond_Cover.png?2d54ef=&format=original",
    "Control Group": "https://helldivers.wiki.gg/images/Control_Group_Premium_Warbond_Cover.png?5db88e=&format=original",
}
"""Dictionary of Warbond images hosted by Discord

Format:

    "Warbond Name": "link"

Example:

    "Helldivers Mobilize": "https://media.discordapp.net/attachments/edited/to/save.space"
"""

assignment_task_images_dict = {
    2: "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&",
    3: "https://cdn.discordapp.com/attachments/1212735927223590974/1338186059934339182/mo_icon_kill.PNG?ex=67aa2a62&is=67a8d8e2&hm=91476d98d8765002e207cddde0c42a32794853904bf86689608c934b33a10ac5&",
    11: "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&",
    12: "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496552865885/mo_icon_defend.png?ex=67aa2acb&is=67a8d94b&hm=d541951b20b1bb70b9e827907b036fd4384fc5d304b4454dc5208cc0593add00&",
    13: "https://cdn.discordapp.com/attachments/1212735927223590974/1340985264780218418/Type_13_MO.png?ex=67b45959&is=67b307d9&hm=fd3feddc3481aeb00a9f66262dba473c88d1401ba177caa0d176639ec5fdde89&",
    15: "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&",
}
"""Dictionary of Assignment images hosted by Discord

Format:

    task_type: "link"

Example:

    2: "https://cdn.discordapp.com/attachments/edited/to/save.some?space"
"""

emotes_list = [
    "Casual Salute",
    "High-Five",
    "Rock Paper Scissors",
    "Hug",
    "Explosive Handshake",
    "Scout Handshake",
    "Test of Conviction",
    "Natural Gas Extraction",
    "At Ease",
    "This is Democracy",
    "Raise Weapon",
    "Tip Hat",
    "Lockstep",
    "Signal: Hold",
    "Signal: Silence",
    "Signal: Group Up",
    "Protect Eardrums",
]
"""A list of emote names

Example:

    "Casual Salute"
"""

victory_poses_list = [
    "Clapping",
    "Flex",
    "Loosen Up",
    "Roll 'Em",
    "Finger Guns",
    "Salute",
    "Super Person",
    "Big Whoop",
    "You're Next",
    "Head Tap",
    "Shotgun Show",
    "Presentable",
    "Squat",
    "Courtly Bow",
    "Boxer",
    "Mime Instrumentation",
    "Call the Helldivers",
    "Distribute Ballots",
    "Welcome Adoration",
    "Guns of Liberty",
    "Big Stretch",
    "Deep Reflection",
    "Thoracic Collision Exultation Maneuver",
    "Ew",
]
"""A list of victory pose names

Example:

    "Clapping"
"""

player_cards_list = [
    "Independence Bringer",
    "Liberty's Herald",
    "Tideturner",
    "Stars and Suffrage",
    "Unblemished Allegiance",
    "Judgement Day",
    "Cresting Honor",
    "Mantle of True Citizenship",
    "Blazing Samaritan",
    "Light of Eternal Liberty",
    "Tyrant Hunter",
    "Cloak of Posterity's Gratitude",
    "Bastion of Integrity",
    "Botslayer",
    "Martyris Rex",
    "Agent of Oblivion",
    "Harbringer of True Equality",
    "Eagle's Fury",
    "Freedom's Tapestry",
    "Dissident's Nightmare",
    "Pinions of Everlasting Glory",
    "Order of the Venerated Ballot",
    "Mark of the Crimson Fang",
    "Executioner's Canopy",
    "Purifying Eclipse",
    "The Breach",
    "Standard of Safe Distance",
    "Patient Zero's Remembrance",
    "Proof of Faultless Virtue",
    "Pride of the Whistleblower",
    "Rebar Resolve",
    "Holder of the Yellow Line",
    "Fre Liberam",
    "Per Democrasum",
    "Reaper of Bounties",
    "Way of the Bandolier",
    "Federation's Embrace",
    "Humble Regalia",
    "Miranda's Legacy",
    "Mother Eagle's Wings",
    "Conductor of Brilliance",
    "Over Artifice Triumphant",
]
"""A list of player card names

Example:

    "Independence Bringer"
"""

titles_list = [
    "Cadet",
    "Space Cadet",
    "Sergeant",
    "Master Sergeant",
    "Chief",
    "Space Chief Prime",
    "Death Captain",
    "Marshal",
    "Star Marshal",
    "Admiral",
    "Skull Admiral",
    "Fleet Admiral",
    "Admirable Admiral",
    "Commander",
    "Galactic Commander",
    "Hell Commander",
    "General",
    "5-Star General",
    "10-Star General",
    "Private",
    "Super Private",
    "Super Citizen",
    "Viper Commando",
    "Fire Safety Officer",
    "Expert Exterminator",
    "Free of Thought",
    "Super Pedestrian",
    "Assault Infantry",
    "Servant of Freedom",
    "Super Sheriff",
    "Decorated Hero",
    "Extra Judicial",
    "Exemplary Subject",
]
"""A list of title names

Example:

    "Cadet"
"""

stratagem_permit_list = [
    "TX-41 Sterilizer",
    "AX/TX-13 'Guard Dog' Dog Breath",
    "Flame Sentry",
    "Anti-Tank Emplacement",
    "Directional Shield",
    "Portable Hellbomb",
    "LIFT-860 Hover Pack",
    "One True Flag",
    "GL-52 De-Escalator",
    "AX/ARC-3 'Guard Dog' K-9",
    "PLAS-45 Epoch",
    "A/LAS-98 Laser Sentry",
    "LIFT-182 Warp Pack",
]
"""A list of stratagem permit names

Example:

    "TX-41 Sterilizer"
"""

stratagem_id_dict = {
    1078307866: "Orbital Gatling Barrage",
    2928105092: "Orbital 120mm HE Barrage",
    2831720448: "Orbital Airburst Strike",
    4158531749: "Orbital 380mm HE Barrage",
    808823003: "Orbital Walking Barrage",
    1520012896: "Orbital Laser",
    2197477188: "Orbital Railcannon Strike",
    201738752: "Orbital Railcannon Strike",
    2391781446: "Orbital Precision Strike",
    1134323464: "Orbital Gas Strike",
    3551336597: "Orbital EMS Strike",
    1363304012: "Orbital Smoke Strike",
    691091357: "Orbital Napalm Barrage",
    336620886: "B-1 Supply Pack",
    4277455125: 'AX/LAS-5 "Guard Dog" Rover',
    2369837022: "SH-20 Ballistic Shield Backpack",
    485637029: "SH-32 Shield Generator Pack",
    3484474549: 'AX/TX-13 "Guard Dog" Dog Breath',
    3791047893: 'AX/AR-23 "Guard Dog"',
    3863540692: "LIFT-850 Jump Pack",
    1382612374: "SH-51 Directional Shield",
    66059712: "PB-100 Portable Hellbomb",
    230501979: "LIFT-860 Hover Pack",
    2686392625: "AX/ARC-3 'Guard Dog' K-9",
    3123380863: "LIFT-182 Warp Pack",
    3111134131: "MD-I4 Incendiary Mines",
    783152568: "MD-17 Anti-Tank Mines",
    3564779466: "MD-8 Gas Mines",
    3039399791: "MD-6 Anti-Personnel Minefield",
    1228689284: "A/MG-43 Machine Gun Sentry",
    2446402932: "A/G-16 Gatling Sentry",
    461790327: "A/M-12 Mortar Sentry",
    2616066963: "A/AC-8 Autocannon Sentry",
    3467463065: "A/MLS-4X Rocket Sentry",
    3157053145: "A/M-23 EMS Mortar Sentry",
    1671728820: "A/ARC-3 Tesla Tower",
    70017975: "FX-12 Shield Generator Relay",
    3827587060: "E/MG-101 HMG Emplacement",
    669794144: "A/FLAM-40 Flame Sentry",
    3106925116: "E/AT-12 Anti-Tank Emplacement",
    1736727415: "E/GL-21 Grenadier Battlement",
    914471076: "A/LAS-98 Laser Sentry",
    3857719901: "EXO-45 Patriot Exosuit",
    754365924: "EXO-49 Emancipator Exosuit",
    2074801524: "M-102 Fast Reconnaissance Vehicle",
    700547364: "Eagle Airstrike",
    2025422424: "Eagle Strafing Run",
    1220665708: "Eagle Cluster Bomb",
    1427614189: "Eagle Napalm Airstrike",
    1062482104: "Eagle Smoke Strike",
    3723465233: "Eagle 100mm Rocket Pods",
    1982351727: "Eagle 500kg Bomb",
    961518079: "LAS-98 Laser Cannon",
    1159284196: "GL-21 Grenade Launcher",
    2138935687: "ARC-3 Arc Thrower",
    1597673685: "LAS-99 Quasar Cannon",
    934703916: "MG-43 Machine Gun",
    1978117092: "M-105 Stalwart",
    376960160: "APW-1 Anti-Materiel Rifle",
    1207425221: "EAT-17 Expendable Anti-Tank",
    1594211884: "GR-8 Recoilless Rifle",
    1944161163: "FLAM-40 Flamethrower",
    841182351: "AC-8 Autocannon",
    4038802832: "MG-206 Heavy Machine Gun",
    3201417018: "RL-77 Airburst Rocket Launcher",
    3212037062: "MLS-4X Commando",
    202236804: "FAF-14 Spear",
    295440526: "RS-422 Railgun",
    1725541340: "TX-41 Sterilizer",
    1326547218: "CQC-1 One True Flag",
    3560739565: "GL-52 De-Escalator",
    2961443701: "PLAS-45 Epoch",
}
"""Dictionary of stratagem ID's and names

Format:

    stratagem_id: "Stratagem Name"

Example:

    1078307866: "Orbital Gatling Barrage",
"""


@dataclass
class SpecialUnits:
    unit_codes_map = {
        ("THE JET BRIGADE", Emojis.SpecialUnits.jet_brigade): {1202, 1203},
        ("PREDATOR STRAIN", Emojis.SpecialUnits.predator_strain): {1243, 1245},
        ("SPORE BURSTER STRAIN", Emojis.SpecialUnits.spore_burster_strain): {1244},
        ("INCINERATION CORPS", Emojis.SpecialUnits.incineration_corps): {1248, 1249},
        ("THE GREAT HOST", Emojis.SpecialUnits.the_great_host): {1269},
    }

    @classmethod
    def get_from_effects_list(
        cls, active_effects: set[int]
    ) -> set | set[tuple[str, str]]:
        special_units = set()
        for unit_info, required_codes in cls.unit_codes_map.items():
            if required_codes.issubset(active_effects):
                special_units.add(unit_info)
        return special_units
