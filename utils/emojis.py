from dataclasses import dataclass


@dataclass
class Emojis:

    @dataclass
    class Wiki:
        main_menu = "<:_:1354916944142274620>"
        primary = "<:_:1354951675567145130>"
        secondary = "<:_:1354955761758765126>"
        grenade = "<:_:1354955442652188692>"
        booster = "<:_:1354953966261244126>"
        stratagem = "<:_:1354953975123935424>"
        equipment = "<:_:1354957720658120814>"
        weapons = "<:_:1354956549012979865>"
        warbond = "<:_:1354958322293411942>"
        enemies = "<:_:1354958906576732221>"

    @dataclass
    class Armour:
        head = "<:_:1247853903509327942>"
        body = "<:_:1247853233330847754>"
        cloak = "<:_:1247852505547935794>"

    @dataclass
    class Items:
        super_credits = "<:_:1233145615031074946>"
        medal = "<:_:1226254158278037504>"
        common_sample = "<:_:1306611420510687334>"
        rare_sample = "<:_:1306611408406052874>"
        requisition_slip = "<:_:1306611395986587689>"

    @dataclass
    class Icons:
        discord = "<:_:1298574603098132512>"
        kofi = "<:_:1298575039859396628>"
        github = "<:_:1298575626864955414>"
        wiki = "<:_:1296193978525417524>"
        hdc = "<:_:1336735906350104586>"
        victory = "<:_:1238069280508215337>"
        mo = "<:_:1240706769043456031>"
        mo_task_complete = "<:_:1325865957037445192>"
        mo_task_incomplete = "<:_:1325865167359316042>"

    @dataclass
    class Factions:
        # 1: "<:_:1306623209465974925>"
        # 2: "<:_:1312127076169682965>"
        # 3: "<:_:1312126862989725707>"
        # 4: "<:_:1317057914145603635>"
        humans = "<:_:1306623209465974925>"
        terminids = "<:_:1312127076169682965>"
        automaton = "<:_:1312126862989725707>"
        illuminate = "<:_:1317057914145603635>"

    @dataclass
    class Decoration:
        left_banner = "<:_:1272562768897376328>"
        right_banner = "<:_:1272562767597015151>"

    @dataclass
    class Stratagems:
        up = "<:_:1277557874041557002>"
        down = "<:_:1277557875849302107>"
        left = "<:_:1277557877787066389>"
        right = "<:_:1277557872246652928> "

    @dataclass
    class Difficulty:
        difficulty1 = "<:_:1297107859766640661>"
        difficulty2 = "<:_:1297107895254519842>"
        difficulty3 = "<:_:1297108514057097261>"
        difficulty4 = "<:_:1297108398663532554>"
        difficulty5 = "<:_:1297108434323247218>"
        difficulty6 = "<:_:1297108419290857512>"
        difficulty7 = "<:_:1297108547515191306>"
        difficulty8 = "<:_:1297108475196997663>"
        difficulty9 = "<:_:1297108452124131348>"
        difficulty10 = "<:_:1219238179551318067>"
        difficultyunknown = "?"

    @dataclass
    class DSS:
        icon = "<:_:1308177676250513449>"
        orbital_blockade = "<:_:1318875016909029388>"
        heavy_ordnance_distribution = "<:_:1318874283350687816>"
        eagle_storm = "<:_:1318874257773690881>"
        operational_support = "<:_:1340990960120631376>"

    @dataclass
    class Weather:
        intense_heat = "<:_:1340988491374264360>"
        tremors = "<:_:1340991266510475296>"

    @dataclass
    class PlanetEffects:
        pass
