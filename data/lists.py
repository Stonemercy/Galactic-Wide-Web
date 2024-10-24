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
    "stratagems": {"path": "data/json/stratagems.json", "value": None},
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
        "automaton": {
            "path": "data/json/enemies/automaton.json",
            "value": None,
        },
        "illuminate": {
            "path": "data/json/enemies/illuminate.json",
            "value": None,
        },
        "terminids": {
            "path": "data/json/enemies/terminids.json",
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

faction_colors = {
    "Automaton": (252, 76, 79),
    "automaton": (126, 38, 22),
    "Terminids": (253, 165, 58),
    "terminids": (126, 82, 29),
    "Illuminate": (103, 43, 166),
    "illuminate": (51, 21, 83),
    "Humans": (36, 205, 76),
    "humans": (18, 102, 38),
    "MO": (254, 226, 76),
}

emojis_dict = {
    "discordlogo": "<:discordlogo:1298574603098132512>",
    "kofilogo": "<:kofilogo:1298575039859396628>",
    "githublogo": "<:githublogo:1298575626864955414>",
    "Semi Automatic": "<:semiautomatic:1233068104029044838>",
    "Burst": "<:burst:1233068096885882932>",
    "Automatic": "<:automatic:1233068105442263121>",
    "Pump Action": "",
    "Double Action": "",
    "Beam": "<:beam:1233068107065458858>",
    "Heat": "<:heat:1233071845612191874>",
    "Stimulative": "",
    "Explosive": "<:explosive:1233069923539091476>",
    "Unarmored 1": "<:unarmored_1:1297111802072793098>",
    "Unarmored 2": "<:unarmored_2:1297110236146045031>",
    "Light Armor Penetrating": "<:light_armor_penetrating:1297110874024050711>",
    "Medium Armor Penetrating": "<:medium_armor_penetrating:1297111813837820038>",
    "Heavy Armor Penetrating": "<:heavy_armor_penetrating:1297111784825557023>",
    "Anti Tank 1": "<:anti_tank_1:1297111716575969311>",
    "Anti Tank 2": "<:anti_tank_2:1297111728424747081>",
    "Anti Tank 3": "<:anti_tank_3:1297111737979502663>",
    "Anti Tank 4": "<:anti_tank_4:1297111751296553001>",
    "Anti Tank 5": "<:anti_tank_5:1297111760540532766>",
    "Anti Tank 6": "<:anti_tank_6:1297111768673423360>",
    "Chargeup": "",
    "Incendiary": "<:incendiary:1290281034532913185>",
    "One Handed": "",
    "Rounds Reload": "",
    "All Barrels": "",
    "Left Banner": "<:left_banner:1272562768897376328>",
    "Right Banner": "<:right_banner:1272562767597015151>",
    "Capacity": "<:capacity:1233129432852729961>",
    "Super Credits": "<:super_credits:1233145615031074946>",
    "Primary": "<:primary:1248032009968681111>",
    "Secondary": "<:secondary:1248032011617173624>",
    "Grenade": "<:grenade:1248032017736532101>",
    "Head": "<:helmet:1247853903509327942>",
    "Body": "<:body:1247853233330847754>",
    "Cloak": "<:cape:1247852505547935794>",
    "Automaton": "<:a_:1215036421551685672>",
    "Terminids": "<:t_:1215036423090999376>",
    "Illuminate": "<:i_:1218283483240206576>",
    "up": "<:Up_Arrow:1277557874041557002>",
    "down": "<:Down_Arrow:1277557875849302107>",
    "left": "<:Left_Arrow:1277557877787066389>",
    "right": "<:Right_Arrow:1277557872246652928> ",
    "victory": "<:victory:1238069280508215337>",
    "medal": "<:medal:1226254158278037504>",
    "MO": "<:MO:1240706769043456031>",
    "wiki": "<:wiki:1296193978525417524>",
    "difficulty1": "<:trivial:1297107859766640661>",
    "difficulty2": "<:easy:1297107895254519842>",
    "difficulty3": "<:medium:1297108514057097261>",
    "difficulty4": "<:challenging:1297108398663532554>",
    "difficulty5": "<:hard:1297108434323247218>",
    "difficulty6": "<:extreme:1297108419290857512>",
    "difficulty7": "<:suicide_mission:1297108547515191306>",
    "difficulty8": "<:impossible:1297108475196997663>",
    "difficulty9": "<:helldive:1297108452124131348>",
    "difficulty10": "<:super_helldive:1219238179551318067>",
    "difficulty?": "?",
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
}

help_dict = {
    "automaton": {
        "long_description": "Returns information on an Automaton or variation. This information is manually updated by the GWW's owner, if there are any inaccuracies please contact our support server.",
        "example_usage": "**`/automaton species:Hulk`** would return information on the Hulk unit.",
    },
    "booster": {
        "long_description": "Returns the description of a specific booster. This information is updated by the folks at [helldivers-2/json](<https://github.com/helldivers-2/json>).",
        "example_usage": "**`/booster booster: Motivational Shocks`** would return the description for the Motivational Shocks booster.",
    },
    "feedback": {
        "long_description": "Provide feedback for the bot. The feedback sent through this modal will go directly to a private channel for me to review.",
        "example_usage": "**`/feedback`** opens a pop-up modal for you to enter your feedback into.",
    },
    "help": {
        "long_description": "Get some help for a specific command or all commands. You can obtain longer descriptions and examples when you lookup a specific command.",
        "example_usage": "**`/help command: Automatons`** would return an embed with useful information about the Automatons command including example usage.",
    },
    "illuminate": {
        "long_description": "Returns information on an Illuminate or variation. This information is manually updated by the GWW's owner, if there are any inaccuracies please contact our support server.",
        "example_usage": "This command has no use as the Illuminate were removed from our galaxy in the first Galactic War.",
    },
    "map": {
        "long_description": "Get an up-to-date map of the galaxy. This is generated upon use of the command so it may take a couple of seconds.",
        "example_usage": "**`/map faction: Automaton public: Yes`** would return a map of the galaxy zoomed in on Automaton planets with names over active planets. It can also be seen by others in discord.",
    },
    "planet": {
        "long_description": "Returns the war details on a specific planet. This includes a lot of stats that arent available in the dashboard.",
        "example_usage": "**`/planet planet: Heeth public: Yes`** returns a large embed with all of the stats the planet has. It also includes a map with an arrow pointing to the planet. It can also be seen by others in discord.",
    },
    "setup": {
        "long_description": "Change the GWW settings for your server. Using this command with no options shows what your current setup is.",
        "example_usage": "**`/setup`** would return a list of the settings for the bot.\n- **`/setup dashboard_channel:#dashboard language:Français`** would setup a dashboard in the #dashboard channel and change the bot's language to French.",
    },
    "stratagem": {
        "long_description": "Returns information on a stratagem. **THIS COMMAND IS A WORK IN PROGRESS**",
        "example_usage": "**`/strategem strategem:Reinforce`** would return information on the Reinforce stratagem",
    },
    "terminid": {
        "long_description": "Returns information on a Terminid species or variation. This information is manually updated by the GWW's owner, if there are any inaccuracies please contact our support server.",
        "example_usage": "**`/terminid species:Shrieker`** would return information on the Shrieker species.",
    },
    "warbond": {
        "long_description": "Returns a basic summary of the items in a specific warbond, showing each item's name and cost, as well as the cost per page and base warbond cost.",
        "example_usage": "**`/warbond warbond:Polar Patriots`** would return a paged embed with the warbond items in it.",
    },
    "weapons": {
        "long_description": "Returns information on a specific weapon. This command has 3 sub-commands for each weapon slot, Primary, Secondary and Grenade.",
        "example_usage": "**`/weapons primary primary:AR-23C Liberator Concussive`** would return details on the AR-23 Liberator Concussive, including an image of the weapon.",
    },
    "stats": {
        "long_description": "Returns information on the GWW bot itself.",
        "example_usage": "**`/stats`**",
    },
    "major_order": {
        "long_description": "Returns information on the current Major Order, if there is one",
        "example_usage": "**`/major_order public: Yes`**",
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
]

stratagem_permit_list = ["TX-41 Sterilizer", "AX/TX-13 'Guard Dog' Dog Breath"]
