from dataclasses import dataclass


@dataclass
class WarbondImages:
    helldivers_mobilize = "https://media.discordapp.net/attachments/1212735927223590974/1234539583086264320/helldivers_mobilize.png?ex=66311a15&is=662fc895&hm=917734dcbeeb5b89a6d3a48c17fff8af49524c9c7187506e7d4ef8a6f37c8a00&=&format=webp&quality=lossless"
    steeled_veterans = "https://media.discordapp.net/attachments/1212735927223590974/1234539583438589952/steeled_veterans.png?ex=66311a15&is=662fc895&hm=3f5e97569e7581af8c0aa86b1fa39c48d29b0a6f557cbd9a5b09d77bbf6854fb&=&format=webp&quality=lossless"
    cutting_Edge = "https://media.discordapp.net/attachments/1212735927223590974/1234539582268112987/cutting_edge.png?ex=66311a15&is=662fc895&hm=152ca52dfb6499f403d77e5fc223252a36c612315d1a8eaabec3f4ca9165ffdf&=&format=webp&quality=lossless"
    democratic_detonation = "https://media.discordapp.net/attachments/1212735927223590974/1234539582671032441/democratic_detonation.png?ex=66311a15&is=662fc895&hm=a7ea39cebf97692bce42f0f1ef04b535b4e241279860439f87a1b13dda7c13b6&=&format=webp&quality=lossless"
    polar_patriots = "https://cdn.discordapp.com/attachments/1212735927223590974/1243556076113235978/polar_patriots.png?ex=6651e758&is=665095d8&hm=5892cb4b53945d328c6cc8e322f96a6dd42bbc1ab00af03ca8f0026564c13e8a&"
    viper_commandos = "https://cdn.discordapp.com/attachments/1212735927223590974/1250840006356893757/viper_commandos.png?ex=666c6708&is=666b1588&hm=14b58f35a78fdbc87aaf285fb02154a814778ededbccc870930261899cf12bef&"
    freedoms_flame = "https://cdn.discordapp.com/attachments/1212735927223590974/1283844729632591985/freedoms_flame.png?ex=66e47914&is=66e32794&hm=3a3d1bb0b9f67dbeb2f63e625511130971fc888d81d36b393996fe1771517fc8&"
    chemical_agents = "https://cdn.discordapp.com/attachments/1212735927223590974/1286254303001972736/chemical_agents.png?ex=66ed3d2b&is=66ebebab&hm=510de52a270f795006e61129f83f0e0b70bf438a042b8b2d9859111806574cf3&"
    truth_enforcers = "https://media.discordapp.net/attachments/1212735927223590974/1301502200849104947/truth_enforcers.png?ex=6724b5e1&is=67236461&hm=c36872146e2ac4fbbaac4ddab19a291927d2e938c6a3cdd00a9b333408e54d1e&=&format=webp&quality=lossless&width=1202&height=676"
    urban_legends = "https://cdn.discordapp.com/attachments/1212735927223590974/1317150385047081110/urban_legends.png?ex=675da363&is=675c51e3&hm=5e894ce871829ccc6ce2899b695692b15a08aad3921f0c390b14cd3b4685ce2c&"
    servants_of_freedom = "https://helldivers.wiki.gg/images/thumb/a/a9/Servants_of_Freedom_Premium_Warbond_Cover.png/1280px-Servants_of_Freedom_Premium_Warbond_Cover.png?e4ff67"
    borderline_justice = "https://helldivers.wiki.gg/images/d/db/Borderline_Justice_Premium_Warbond_Cover.png?df22f7=&format=original"
    masters_of_ceremony = "https://helldivers.wiki.gg/images/6/65/Masters_of_Ceremony_Premium_Warbond_Cover.png?6bb032=&format=original"
    force_of_law = "https://helldivers.wiki.gg/images/7/74/Force_of_Law_Premium_Warbond_Cover.png?2d54ef=&format=original"
    control_group = "https://helldivers.wiki.gg/images/Control_Group_Premium_Warbond_Cover.png?5db88e=&format=original"
    halo_3_odst = "https://helldivers.wiki.gg/images/thumb/Halo_ODST_Legendary_Warbond_Cover.png/1920px-Halo_ODST_Legendary_Warbond_Cover.png?3e16b0"
    dust_devils = (
        "https://helldivers.wiki.gg/images/Dust_Devils_Premium_Warbond_Cover.png?b8541f"
    )

    def get(name: str) -> str | None:
        return getattr(
            WarbondImages, name.replace(" ", "_").replace("'", "").lower(), None
        )
