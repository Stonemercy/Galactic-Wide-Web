from dataclasses import dataclass


@dataclass
class AssignmentImages:
    _2 = "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&"
    _3 = "https://cdn.discordapp.com/attachments/1212735927223590974/1338186059934339182/mo_icon_kill.PNG?ex=67aa2a62&is=67a8d8e2&hm=91476d98d8765002e207cddde0c42a32794853904bf86689608c934b33a10ac5&"
    _11 = "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&"
    _12 = "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496552865885/mo_icon_defend.png?ex=67aa2acb&is=67a8d94b&hm=d541951b20b1bb70b9e827907b036fd4384fc5d304b4454dc5208cc0593add00&"
    _13 = "https://cdn.discordapp.com/attachments/1212735927223590974/1340985264780218418/Type_13_MO.png?ex=67b45959&is=67b307d9&hm=fd3feddc3481aeb00a9f66262dba473c88d1401ba177caa0d176639ec5fdde89&"
    _18 = "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&"

    def get(id: int) -> str:
        return getattr(
            AssignmentImages,
            f"_{id}",
            "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&",
        )
