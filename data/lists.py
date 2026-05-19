json_dict = {
    "languages": {
        "en": {"path": "data/languages/en.json", "value": None},
        "fr": {"path": "data/languages/fr.json", "value": None},
        "de": {"path": "data/languages/de.json", "value": None},
        "it": {"path": "data/languages/it.json", "value": None},
        "pt-br": {"path": "data/languages/pt-br.json", "value": None},
        "ru": {"path": "data/languages/ru.json", "value": None},
        "es": {"path": "data/languages/es.json", "value": None},
        "zh-hant": {"path": "data/languages/zh-hant.json", "value": None},
        "tr": {"path": "data/languages/tr.json", "value": None},
    },
    "planets": {"path": "data/json/planets/planets.json", "value": None},
    "planetRegions": {"path": "data/json/planets/planetRegions.json", "value": None},
    "sectors": {"path": "data/json/planets/sectors.json", "value": None},
    "items": {
        "items": {"path": "data/json/items/items.json", "value": None},
        "boosters": {"path": "data/json/items/boosters.json", "value": None},
        "reward_types": {
            "path": "data/json/assignments/reward/type.json",
            "value": None,
        },
    },
    "enemy_ids": {"path": "data/json/enemies/enemy_ids.json", "value": None},
    "galactic_war_effects": {
        "path": "data/json/effects/galactic_war_effects/effect_types.json",
        "value": None,
    },
    "strings": {"path": "data/json/strings.json", "value": None},
}

CUSTOM_COLOURS = {
    "MO": (255, 220, 0),
    "DSS": (214, 232, 248),
}

HOMEWORLD_ICONS = {
    "humans": "https://cdn.discordapp.com/attachments/1212735927223590974/1470844299867328731/super_earth.png?ex=698cc600&is=698b7480&hm=2b4569859d9e09420085455de5ccd44b906e14d85ebe93914a5147e56c7286db&",
    "automaton": "https://cdn.discordapp.com/attachments/1212735927223590974/1470848423996555467/auto_homeworld.png?ex=698cc9d7&is=698b7857&hm=010592cc01e4c82ab68cfc85b192ef176a68680c8289cc5f891291e9dbc133b9&",
}

ATTACK_EMBED_ICONS = {
    "default": "https://media.discordapp.net/attachments/1212735927223590974/1484605118543298610/loss_default.png?ex=69bed5c2&is=69bd8442&hm=54e34e4498ddcfeb5838468941ba6a1f821c069e6f3ee9e8e2c2e5e4e3d1d3e7&=&format=webp&quality=lossless",
    "illuminate": "https://media.discordapp.net/attachments/1212735927223590974/1414959912269643847/illuminate.png?ex=68c1779b&is=68c0261b&hm=f7f450e22f313d28b50f03c5aa9ee5c21ded41f79f5a528ec4f819f5283c479c&=&format=webp&quality=lossless",
    "automaton": "https://media.discordapp.net/attachments/1212735927223590974/1414959911728709632/automaton.png?ex=68c1779b&is=68c0261b&hm=b5a82963ba2a5010f9a8e1b1f5ea0ab15f3ca29ace1dda6922053105b122fadf&=&format=webp&quality=lossless",
    "terminids": "https://media.discordapp.net/attachments/1212735927223590974/1414959912815169636/terminids.png?ex=68c1779b&is=68c0261b&hm=3c1ad5eea04d6ca74c0a99d70244780662fa37f5e25866d4039edc921e442b0b&=&format=webp&quality=lossless",
}

DEFENCE_EMBED_ICONS = {
    "default": "https://media.discordapp.net/attachments/1212735927223590974/1484605635713700121/0x1453ed31ade4af41.png?ex=69bed63e&is=69bd84be&hm=7d4b2ffd4b7072940e64c7a7b9c787208ae3955340c964891f587a5d05487539&=&format=webp&quality=lossless",
    "illuminate": "https://media.discordapp.net/attachments/1212735927223590974/1415077451565891705/illuminate.png?ex=68c1e513&is=68c09393&hm=baa0da180398b0273df5e807e89e48270bd635fa9d5b0bcd29135ce4d98d1e11&=&format=webp&quality=lossless",
    "automaton": "https://media.discordapp.net/attachments/1212735927223590974/1415077450488086588/automaton.png?ex=68c1e513&is=68c09393&hm=48a1b17fe45a3946bf8341619b52eb2c8872a682198f1ac727791a175ff7ad79&=&format=webp&quality=lossless",
    "terminids": "https://media.discordapp.net/attachments/1212735927223590974/1415077452513939657/terminids.png?ex=68c1e513&is=68c09393&hm=c9589861ef0fd2364083746746d767974150190220a50da44b156e1d85eb9880&=&format=webp&quality=lossless",
}

VICTORY_ICONS = {
    "default": "https://media.discordapp.net/attachments/1212735927223590974/1484608194184483089/vic_default.png?ex=69bed8a0&is=69bd8720&hm=61d9f13dd968e2877dc0864abd6e7b0f870334b823595a64d8955327a89bf4ab&=&format=webp&quality=lossless",
    "illuminate": "https://media.discordapp.net/attachments/1212735927223590974/1417225835894673408/vic_illuminate.png?ex=68c9b5ea&is=68c8646a&hm=4bbada8b099921db08a9548845dccdc9cadf9b8586a0f5b9a953aaed1d27c8fa&=&format=webp&quality=lossless",
    "automaton": "https://media.discordapp.net/attachments/1212735927223590974/1417225835399741621/vic_automaton.png?ex=68c9b5e9&is=68c86469&hm=0d4d869869fdb5d92077b94f58dbdb9d5f3e74ee0c7af39ee9e763d0d5cfde8a&=&format=webp&quality=lossless",
    "terminids": "https://media.discordapp.net/attachments/1212735927223590974/1417225836368498688/vic_teriminds.png?ex=68c9b5ea&is=68c8646a&hm=d4a95583a298f8b6d3d9dbf465fad301837a91b4446e9740800325173cb145f4&=&format=webp&quality=lossless",
}

LOSS_ICONS = {
    "default": "https://media.discordapp.net/attachments/1212735927223590974/1484605118543298610/loss_default.png?ex=69bed5c2&is=69bd8442&hm=54e34e4498ddcfeb5838468941ba6a1f821c069e6f3ee9e8e2c2e5e4e3d1d3e7&=&format=webp&quality=lossless",
    "illuminate": "https://media.discordapp.net/attachments/1212735927223590974/1424326308787392633/loss_illuminate.png?ex=68e38abe&is=68e2393e&hm=f388e59a228d25f08b251c262fd8ada7ecd37f639ec546b527ff4cb5542cd06f&=&format=webp&quality=lossless",
    "automaton": "https://media.discordapp.net/attachments/1212735927223590974/1424326308506107965/loss_automaton.png?ex=68e38abe&is=68e2393e&hm=2e7a9842c392a90a75e890489e0cd4c6315b3a61c44505eaa7510483f91de8d0&=&format=webp&quality=lossless",
    "terminids": "https://media.discordapp.net/attachments/1212735927223590974/1424326308191670355/loss_terminids.png?ex=68e38abe&is=68e2393e&hm=2b0ed2f554d3aef7761b947312fd59d59a4b7e9c18e636bf9d07385de1b02f8b&=&format=webp&quality=lossless",
}

URGENT_ICONS = {
    "default": "https://media.discordapp.net/attachments/1212735927223590974/1484600955457769654/urgent_default.png?ex=69bed1e2&is=69bd8062&hm=d03b43c424caaa5fe2c9225921d7dbe0e6ca6262bb97aabfae0c67cd21c080e8&=&format=webp&quality=lossless",
    "illuminate": "https://media.discordapp.net/attachments/1212735927223590974/1484600034447331438/urgent_illuminate.png?ex=69bed106&is=69bd7f86&hm=9c34ecece956b51463ae70b492843b87fb74382898e2cefb3ab194ec93e8870f&=&format=webp&quality=lossless",
    "automaton": "https://media.discordapp.net/attachments/1212735927223590974/1484600024859148518/urgent_automaton.png?ex=69bed104&is=69bd7f84&hm=c2257d88c42e6832bca42a79fe1e1c0f9a619edd47ddd478d7142c6bda222f07&=&format=webp&quality=lossless",
    "terminids": "https://media.discordapp.net/attachments/1212735927223590974/1484600044345884843/urgent_terminids.png?ex=69bed109&is=69bd7f89&hm=1b041e02ef31e44353ebf1d4f29bbf7c1912b48a4593ee6c40714787f7a8b579&=&format=webp&quality=lossless",
}

STRATAGEM_ID_DICT = {
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
    3564779466: "StA-X3 W.A.S.P. Launcher",
    1326547218: "MD-8 Gas Mines",
    3039399791: "MD-6 Anti-Personnel Minefield",
    1228689284: "A/MG-43 Machine Gun Sentry",
    2446402932: "A/G-16 Gatling Sentry",
    461790327: "A/M-12 Mortar Sentry",
    2616066963: "A/AC-8 Autocannon Sentry",
    3467463065: "A/MLS-4X Rocket Sentry",
    3157053145: "A/M-23 EMS Mortar Sentry",
    1671728820: "A/ARC-3 Tesla Tower",
    2682182269: "A/ARC-3 Tesla Tower",
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
    2138935687: "Arc-3 Arc Thrower",
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
    1247082912: "CQC-1 One True Flag",
    2265180087: "ONE TRUE FLAG",
    3560739565: "GL-52 De-Escalator",
    2961443701: "PLAS-45 Epoch",
    4030799106: "S-11 Speargun",
    4189624954: "EAT-700 Expendable Napalm",
    906184838: "MS-11 Solo Silo",
}

CURRENCIES = {
    2985106497: "Rare Sample",
    3992382197: "Common Sample",
    3608481516: "Requisition Slip",
}
