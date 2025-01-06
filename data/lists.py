language_dict = {
    "English": "en",
    "Français": "fr",
    "Deutsch": "de",
}

json_dict = {
    "languages": {
        "en": {"path": "data/languages/en.json", "value": None},
        "fr": {"path": "data/languages/fr.json", "value": None},
        "de": {"path": "data/languages/de.json", "value": None},
    },
    "stratagems": {"path": "data/json_custom/stratagems.json", "value": None},
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
        "cutting_edge": {
            "path": "data/json/warbonds/cutting_edge.json",
            "value": None,
        },
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
    },
    "planets": {
        "path": "data/json/planets/planets.json",
        "value": None,
    },
    "items": {
        "item_names": {
            "path": "data/json/items/item_names.json",
            "value": None,
        },
        "armor": {"path": "data/json/items/armor/armor.json", "value": None},
        "armor_perks": {
            "path": "data/json/items/armor/passive.json",
            "value": None,
        },
        "armor_slots": {
            "path": "data/json/items/armor/slot.json",
            "value": None,
        },
        "primary_weapons": {
            "path": "data/json/items/weapons/primary.json",
            "value": None,
        },
        "secondary_weapons": {
            "path": "data/json/items/weapons/secondary.json",
            "value": None,
        },
        "grenades": {
            "path": "data/json/items/weapons/grenades.json",
            "value": None,
        },
        "weapon_types": {
            "path": "data/json/items/weapons/types.json",
            "value": None,
        },
        "weapon_traits": {
            "path": "data/json/items/weapons/traits.json",
            "value": None,
        },
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
        "enemy_ids": {
            "path": "data/json_custom/enemies/enemy_ids.json",
            "value": None,
        },
        "automaton": {
            "path": "data/json_custom/enemies/automaton.json",
            "value": None,
        },
        "illuminate": {
            "path": "data/json_custom/enemies/illuminate.json",
            "value": None,
        },
        "terminids": {
            "path": "data/json_custom/enemies/terminids.json",
            "value": None,
        },
    },
}

supported_languages = {
    "en": "en-GB",
    "de": "de-DE",
    "es": "es-ES",
    "fr": "fr-FR",
    "it": "it-IT",
    "jp": "ja-JP",
    "ko": "ko-KO",
    "my": "ms-MY",
    "pl": "pl-PL",
    "pt": "pt-PT",
    "ru": "ru-RU",
    "zh": "zh-Hans",
}

faction_colours = {
    "Automaton": (252, 108, 115),
    "automaton": (126, 54, 57),
    "Terminids": (252, 188, 4),
    "terminids": (126, 99, 2),
    "Illuminate": (107, 59, 187),
    "illuminate": (53, 29, 93),
    "Humans": (36, 205, 76),
    "humans": (18, 102, 38),
    "MO": (254, 226, 76),
    "DSS": (105, 181, 209),
}

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
}

assignment_task_images_dict = {
    2: "https://cdn.discordapp.com/attachments/1212735927223590974/1323773697491996682/mo_icon_kill.PNG?ex=6775bbd4&is=67746a54&hm=6d529e202487c278d2f3a0da1c7315a00a84acc51947c81e101eaf015620eeb0&",
    3: "https://cdn.discordapp.com/attachments/1212735927223590974/1323773697491996682/mo_icon_kill.PNG?ex=6775bbd4&is=67746a54&hm=6d529e202487c278d2f3a0da1c7315a00a84acc51947c81e101eaf015620eeb0&",
    11: "https://cdn.discordapp.com/attachments/1212735927223590974/1323773697491996682/mo_icon_kill.PNG?ex=6775bbd4&is=67746a54&hm=6d529e202487c278d2f3a0da1c7315a00a84acc51947c81e101eaf015620eeb0&",
    12: "https://cdn.discordapp.com/attachments/1212735927223590974/1323773697491996682/mo_icon_kill.PNG?ex=6775bbd4&is=67746a54&hm=6d529e202487c278d2f3a0da1c7315a00a84acc51947c81e101eaf015620eeb0&",
    13: "https://cdn.discordapp.com/attachments/1212735927223590974/1323773697491996682/mo_icon_kill.PNG?ex=6775bbd4&is=67746a54&hm=6d529e202487c278d2f3a0da1c7315a00a84acc51947c81e101eaf015620eeb0&",
    15: "https://cdn.discordapp.com/attachments/1212735927223590974/1323773697491996682/mo_icon_kill.PNG?ex=6775bbd4&is=67746a54&hm=6d529e202487c278d2f3a0da1c7315a00a84acc51947c81e101eaf015620eeb0&",
}

task_type_15_progress_dict = {
    -10: 0,
    -8: 0.1,
    -6: 0.2,
    -4: 0.3,
    -2: 0.4,
    0: 0.5,
    2: 0.6,
    4: 0.7,
    6: 0.8,
    8: 0.9,
    10: 1,
}

help_dict = {
    "automaton": {
        "long_description": "Returns information on an Automaton or variation. This information is manually updated by the GWW's owner, if there are any inaccuracies please contact our support server.",
        "example_usage": "**`/automaton species:Hulk public:Yes`** would return information on the Hulk unit that other members in the server can see.",
    },
    "booster": {
        "long_description": "Returns the description of a specific booster. This information is updated by the folks at [helldivers-2/json](<https://github.com/helldivers-2/json>).",
        "example_usage": "**`/booster booster:Motivational Shocks public:Yes`** would return information for the Motivational Shocks booster that other members in the server can see.",
    },
    "dss": {
        "long_description": "Returns extended information on the Democracy Space Station",
        "example_usage": "**`/dss public:Yes`** would return information on the DSS that other members in the server can see.",
    },
    "feedback": {
        "long_description": "Provide feedback for the bot. The feedback sent through this modal will go directly to a private channel for me to review.",
        "example_usage": "**`/feedback`** opens a pop-up modal for you to enter your feedback into.",
    },
    "help": {
        "long_description": "Get some help for a specific command or all commands. You can obtain longer descriptions and examples when you lookup a specific command.",
        "example_usage": "**`/help command:Automatons public:Yes`** would return an embed with useful information about the Automatons command including example usage that other members in the server can see.",
    },
    "illuminate": {
        "long_description": "Returns information on an Illuminate or variation. This information is manually updated by the GWW's owner, if there are any inaccuracies please contact our support server.",
        "example_usage": "**`/illuminate species:Observer public:Yes`** would return information on the Observer unit that other members in the server can see.",
    },
    "major_order": {
        "long_description": "Returns information on the current Major Order, if there is one",
        "example_usage": "**`/major_order public:Yes`** would return information on the current Major Order that other members in the server can see.",
    },
    "map": {
        "long_description": "Get an up-to-date map of the galaxy. This is generated upon use of the command so it may take a couple of seconds.",
        "example_usage": "**`/map faction:Automaton public:Yes`** would return a map of the galaxy zoomed in on Automaton planets with names over active planets. It can also be seen by others in discord.",
    },
    "planet": {
        "long_description": "Returns the war details on a specific planet. This includes a lot of stats that arent available in the dashboard.",
        "example_usage": "**`/planet planet:Heeth with_map:Yes public:Yes`** returns a large embed with all of the stats the planet has. It also includes a map with an arrow pointing to the planet. It can also be seen by others in discord.",
    },
    "setup": {
        "long_description": "Change the GWW settings for your server.",
        "example_usage": "**`/setup`** brings up a message with buttons you can use to change the bot's settings.",
    },
    "steam": {
        "long_description": "Returns the latest patch notes",
        "example_usage": "**`/steam public:Yes`** returns an embed with the most recent patch notes, it also has a dropdown for the most recent 10 patch notes you can choose from. Other people can see this too.",
    },
    "stratagem": {
        "long_description": "Returns information on a stratagem. **THIS COMMAND IS A WORK IN PROGRESS**",
        "example_usage": "**`/strategem strategem:Reinforce public:Yes`** would return information on the Reinforce stratagem that other members of the server can see.",
    },
    "superstore": {
        "long_description": "Returns the current Superstore rotation",
        "example_usage": "**`/superstore public:Yes`** returns the current rotation of the Superstore that other people in the server can see.",
    },
    "terminid": {
        "long_description": "Returns information on a Terminid species or variation. This information is manually updated by the GWW's owner, if there are any inaccuracies please contact our support server.",
        "example_usage": "**`/terminid species:Shrieker public:Yes`** would return information on the Shrieker species that everyone else can see.",
    },
    "warbond": {
        "long_description": "Returns a basic summary of the items in a specific warbond, showing each item's name and cost, as well as the cost per page and base warbond cost.",
        "example_usage": "**`/warbond warbond:Polar Patriots public:Yes`** would return a paged embed with the warbond items in it that everyone in the server can see.",
    },
    "warfront": {
        "long_description": "Returns information on each campaign for a specific faction",
        "example_usage": "**`/warfront faction:Illuminate public:Yes`** would return information on the Illuminate warfront that other members in the server can see.",
    },
    "weapons": {
        "long_description": "Returns information on a specific weapon. This command has 3 sub-commands for each weapon slot, Primary, Secondary and Grenade.",
        "example_usage": "**`/weapons primary primary:AR-23C Liberator Concussive, public:Yes`** would return details on the AR-23 Liberator Concussive, including an image of the weapon. Other people in the server can see it too.",
    },
}

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
]

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
    "Patient Zero's Rememberance",
    "Proof of Faultless Virtue",
    "Pride of the Whistleblower",
    "Rebar Resolve",
    "Holder of the Yellow Line",
]

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
]

stratagem_permit_list = [
    "TX-41 Sterilizer",
    "AX/TX-13 'Guard Dog' Dog Breath",
    "Flame Sentry",
    "Anti-Tank Emplacement",
    "Directional Shield",
]

stratagem_id_dict = {
    1078307866: "Orbital Gatling Barrage",
    2928105092: "Orbital 120mm HE Barrage",
    2831720448: "Orbital Airburst Strike",
    4158531749: "Orbital 380mm HE Barrage",
    808823003: "Orbital Walking Barrage",
    1520012896: "Orbital Laser",
    2197477188: "Orbital Railcannon Strike",
    3039399791: "Anti-Personnel Minefield",
    336620886: "Supply Pack",
    961518079: "Laser Cannon",
    1159284196: "Grenade Launcher",
    3111134131: "Incendiary Mines",
    4277455125: '"Guard Dog" Rover',
    2369837022: "Ballistic Shield Backpack",
    2138935687: "Arc Thrower",
    783152568: "Anti-Tank Mines",
    1597673685: "Quasar Cannon",
    485637029: "Shield Generator Pack",
    3484474549: '"Guard Dog" Dog Breath',
    1228689284: "Machine Gun Sentry",
    2446402932: "Gatling Sentry",
    461790327: "Mortar Sentry",
    3791047893: '"Guard Dog"',
    2616066963: "Autocannon Sentry",
    3467463065: "Rocket Sentry",
    3157053145: "EMS Mortar Sentry",
    2391781446: "Orbital Precision Strike",
    1134323464: "Orbital Gas Strike",
    3551336597: "Orbital EMS Strike",
    1363304012: "Orbital Smoke Strike",
    70017975: "Shield Generator Relay",
    3827587060: "HMG Emplacement",
    1671728820: "Tesla Tower",
    3857719901: "Patriot Exosuit",
    754365924: "Emancipator Exosuit",
    2025422424: "Eagle Strafing Run",
    700547364: "Eagle Airstrike",
    1220665708: "Eagle Cluster Bomb",
    1427614189: "Eagle Napalm Airstrike",
    1062482104: "Eagle Smoke Strike",
    3863540692: "Jump Pack",
    3723465233: "Eagle 100mm Rocket Pods",
    1982351727: "Eagle 500kg Bomb",
    934703916: "Machine Gun",
    1978117092: "Stalwart",
    376960160: "Anti-Materiel Rifle",
    1207425221: "Expendable Anti-Tank",
    1594211884: "Recoilless Rifle",
    1944161163: "Flamethrower",
    841182351: "Autocannon",
    4038802832: "Heavy Machine Gun",
    3201417018: "Airburst Rocket Launcher",
    3212037062: "Commando",
    202236804: "Spear",
    295440526: "Railgun",
    1725541340: "Sterilizer",
}
