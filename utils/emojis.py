from dataclasses import dataclass


@dataclass
class Emojis:

    @dataclass
    class Wiki:
        main_menu = "<:s:1354916944142274620>"
        primary = "<:s:1354951675567145130>"
        secondary = "<:s:1354955761758765126>"
        grenade = "<:s:1354955442652188692>"
        booster = "<:s:1354953966261244126>"
        stratagem = "<:s:1354953975123935424>"
        equipment = "<:s:1354957720658120814>"
        weapons = "<:s:1354956549012979865>"
        warbond = "<:s:1354958322293411942>"
        enemies = "<:s:1354958906576732221>"

    @dataclass
    class Armour:
        head = "<:s:1247853903509327942>"
        body = "<:s:1247853233330847754>"
        cloak = "<:s:1247852505547935794>"

    @dataclass
    class Items:
        super_credits = "<:s:1233145615031074946>"
        medal = "<:s:1226254158278037504>"
        common_sample = "<:s:1306611420510687334>"
        rare_sample = "<:s:1306611408406052874>"
        requisition_slip = "<:s:1306611395986587689>"

    @dataclass
    class Icons:
        discord = "<:s:1298574603098132512>"
        kofi = "<:s:1298575039859396628>"
        github = "<:s:1298575626864955414>"
        wiki = "<:s:1296193978525417524>"
        hdc = "<:s:1336735906350104586>"
        victory = "<:s:1238069280508215337>"
        mo = "<:s:1240706769043456031>"
        mo_task_complete = "<:s:1325865957037445192>"
        mo_task_incomplete = "<:s:1325865167359316042>"

    @dataclass
    class Factions:
        humans = "<:s:1306623209465974925>"
        terminids = "<:s:1312127076169682965>"
        automaton = "<:s:1312126862989725707>"
        illuminate = "<:s:1317057914145603635>"

    @dataclass
    class Decoration:
        left_banner = "<:s:1272562768897376328>"
        right_banner = "<:s:1272562767597015151>"

    @dataclass
    class Stratagems:
        up = "<:s:1277557874041557002>"
        down = "<:s:1277557875849302107>"
        left = "<:s:1277557877787066389>"
        right = "<:s:1277557872246652928> "

    @dataclass
    class Difficulty:
        difficulty1 = "<:s:1297107859766640661>"
        difficulty2 = "<:s:1297107895254519842>"
        difficulty3 = "<:s:1297108514057097261>"
        difficulty4 = "<:s:1297108398663532554>"
        difficulty5 = "<:s:1297108434323247218>"
        difficulty6 = "<:s:1297108419290857512>"
        difficulty7 = "<:s:1297108547515191306>"
        difficulty8 = "<:s:1297108475196997663>"
        difficulty9 = "<:s:1297108452124131348>"
        difficulty10 = "<:s:1219238179551318067>"
        difficultyunknown = "?"

    @dataclass
    class DSS:
        icon = "<:s:1308177676250513449>"
        orbital_blockade = "<:s:1318875016909029388>"
        heavy_ordnance_distribution = "<:s:1318874283350687816>"
        eagle_storm = "<:s:1318874257773690881>"
        operational_support = "<:s:1340990960120631376>"

    @dataclass
    class Weather:
        intense_heat = "<:s:1357272522227318847>"
        fire_tornadoes = "<:s:1357272531798851584>"
        extreme_cold = "<:s:1357272540413825075>"
        blizzards = "<:s:1357272548626268340>"
        tremors = "<:s:1357278857232646164>"

    @dataclass
    class SpecialUnits:
        predator_strain = "<:s:1355905145992646877>"
        jet_brigade = "<:s:1355912552143393039>"
        incineration_corps = "<:s:1355913678704349336>"
