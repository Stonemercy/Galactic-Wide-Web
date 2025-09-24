from dataclasses import dataclass


@dataclass
class AssignmentImages:
    _2 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964775007129661/Type_13_MO.png?ex=68c51f75&is=68c3cdf5&hm=586104cd845e87c2c59e44c3c82419ea2b21ea2c4a042cb573e3cd06a48dbcef&"
    _3 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964773211967561/mo_icon_kill.PNG?ex=68c51f75&is=68c3cdf5&hm=3c4ddd02b7333c9d6415eab3f5e0b4a365c672831bbcfc89393c8eda421edabe&"
    _7 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964775007129661/Type_13_MO.png?ex=68c51f75&is=68c3cdf5&hm=586104cd845e87c2c59e44c3c82419ea2b21ea2c4a042cb573e3cd06a48dbcef&"
    _9 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964775007129661/Type_13_MO.png?ex=68c51f75&is=68c3cdf5&hm=586104cd845e87c2c59e44c3c82419ea2b21ea2c4a042cb573e3cd06a48dbcef&"
    _11 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964773949902848/mo_icon_liberate.png?ex=68c51f75&is=68c3cdf5&hm=b019701f6c7ae76be3d0cf18db2ee2f53385be4ac52eaf14874cd6cadfae789a&"
    _12 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964772368777220/mo_icon_defend.png?ex=68c51f75&is=68c3cdf5&hm=893a16ca781bad19865b474932f1d2c54271a6f6c7bcb9eaa5cdd49559015547&"
    _13 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964772368777220/mo_icon_defend.png?ex=68c51f75&is=68c3cdf5&hm=893a16ca781bad19865b474932f1d2c54271a6f6c7bcb9eaa5cdd49559015547&"
    _15 = "https://cdn.discordapp.com/attachments/1212735927223590974/1415964775007129661/Type_13_MO.png?ex=68c51f75&is=68c3cdf5&hm=586104cd845e87c2c59e44c3c82419ea2b21ea2c4a042cb573e3cd06a48dbcef&"

    def get(id: int) -> str:
        return getattr(
            AssignmentImages,
            f"_{id}",
            "https://cdn.discordapp.com/attachments/1212735927223590974/1415964773949902848/mo_icon_liberate.png?ex=68c51f75&is=68c3cdf5&hm=b019701f6c7ae76be3d0cf18db2ee2f53385be4ac52eaf14874cd6cadfae789a&",
        )
