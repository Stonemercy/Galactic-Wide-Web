from dataclasses import dataclass


@dataclass
class DSSImages:
    class EAGLE_STORM:
        active = "https://media.discordapp.net/attachments/1212735927223590974/1417879516059144234/Eagle_Storm_Active.png?ex=68cc16b3&is=68cac533&hm=4bba9cb812bdb92a88173158cfef0e13755bdec5b4688bb457938ba34db9a204&=&format=webp&quality=lossless"
        preparing = "https://media.discordapp.net/attachments/1212735927223590974/1417879517401448468/Eagle_Storm_Preparing.png?ex=68cc16b3&is=68cac533&hm=35d9e8d1f9449667bf4b275759a4ec4efc025876fd4568c26ce1f3638ee10b79&=&format=webp&quality=lossless"
        on_cooldown = "https://media.discordapp.net/attachments/1212735927223590974/1417879516726165564/Eagle_Storm_On_Cooldown.png?ex=68cc16b3&is=68cac533&hm=f2269e5c4aacdb7b24e767148f8b2c0120c39c461a72ee1dfe7572e2874e62ed&=&format=webp&quality=lossless"

    class ORBITAL_BLOCKADE:
        active = "https://media.discordapp.net/attachments/1212735927223590974/1417879517879472279/Orbital_Blockade_Active.png?ex=68cc16b3&is=68cac533&hm=5077f84de02156b588921e2c84cc6a28d80caee4019e03c89735fdcd1a09ecc9&=&format=webp&quality=lossless"
        preparing = "https://media.discordapp.net/attachments/1212735927223590974/1417879518668001300/Orbital_Blockade_Preparing.png?ex=68cc16b4&is=68cac534&hm=9162540c3e52dc251222a4d20798e3b0f396b8f7365719969efa57c3a481e61f&=&format=webp&quality=lossless"
        on_cooldown = "https://media.discordapp.net/attachments/1212735927223590974/1417879518299033641/Orbital_Blockade_On_Cooldown.png?ex=68cc16b4&is=68cac534&hm=36ca3e97fbef6ebe61ad87500af91e8d7db3b1053beb9b944830a6be2b3e645d&=&format=webp&quality=lossless"

    class HEAVY_ORDNANCE_DISTRIBUTION:
        active = "https://media.discordapp.net/attachments/1212735927223590974/1417879519167254594/Planetary_Bombardment_Active.png?ex=68cc16b4&is=68cac534&hm=5f33aa830246d81d3d0a8e1e6846f8a78c39dfffd47618e44e773e7b758602eb&=&format=webp&quality=lossless"
        preparing = "https://media.discordapp.net/attachments/1212735927223590974/1417879520278478920/Planetary_Bombardment_Preparing.png?ex=68cc16b4&is=68cac534&hm=066104ef537304fc2a907ad2dfb481647bf00dffb0776f6e9545762406520351&=&format=webp&quality=lossless"
        on_cooldown = "https://media.discordapp.net/attachments/1212735927223590974/1417879519871766558/Planetary_Bombardment_On_Cooldown.png?ex=68cc16b4&is=68cac534&hm=7ea9318d5559ca9bef3a4f962d2bcc5e0409fa4b62df0be620fb68851142ad85&=&format=webp&quality=lossless"

    UNKNOWN = "https://media.discordapp.net/attachments/1212735927223590974/1417426057753137316/0xf8864d4e183fe078.png?ex=68ca7062&is=68c91ee2&hm=6b22c54ed82f37c79ea165dbad85754e6f46056ab82b7a50eb628512944c954f&=&format=webp&quality=lossless"

    def get(ta_name: str, status: str) -> str | None:
        ta_name = ta_name.replace(" ", "_").upper()
        try:
            ta_obj = getattr(DSSImages, ta_name, None)
            if ta_obj is None:
                return None
            return getattr(ta_obj, status, None)
        except AttributeError:
            return DSSImages.UNKNOWN
