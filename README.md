# Galactic World Web
<p align="center">
    <a href="https://github.com/Stonemercy/Galactic-Wide-Web/commits/main"><img src="https://img.shields.io/github/last-commit/Stonemercy/Galactic-Wide-Web"></a>
    <a href="https://github.com/Stonemercy/Galactic-Wide-Web"><img src="https://img.shields.io/github/languages/code-size/Stonemercy/Galactic-Wide-Web"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
	<a href="https://ko-fi.com/Z8Z6WR2CS"><img src="https://ko-fi.com/img/githubbutton_sm.svg"></a>
</p>

While this bot not designed for others to setup, you can use this repo for ideas for your projects.
If you wish to use the GWW bot itself, I have it hosted and you can invite it [here](hhttps://discord.com/application-directory/1212535586972369008)

## Commands
`/automaton`
- Returns information on an Automaton or variation.
  - Options:
    - `species`: string <Optional> - A specific 'main' automaton
    - `variation`: string <Optional> - A specific variant of an automaton

`/booster`
- Returns the description of a specific booster.
  - Options:
    - `booster`: string [Required] - The booster you want to lookup

`/help`
- Get some help for a specific command, or a list of every command by using "all".
  - Options:
    - `command`: string [Required] - The command you want to lookup, use "all" for a list of all available commands

`/map`
- Get an up-to-date map of the galaxy
  - Options:
    - `faction`: string <Optional> - The faction to focus on
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/map`
- Get an up-to-date map of the galaxy
  - Options:
    - `faction`: string <Optional> - The faction to focus on
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/planet`
- Returns the war details on a specific planet.
  - Options:
    - `planet`: string [Required] - The planet you want to lookup
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/setup`
- Change the GWW settings for your server. Use this without options to see your set settings.
  - Options:
    - `dashboard_channel`: channel <Optional> - The channel you want the dashboard to be sent to. Set this to your current set channel to unset it.
    - `announcement_channel`: channel <Optional> - The channel you want announcements sent to. Set this to your current set channel to unset it.
    - `patch_notes`: string <Optional> - Toggle if you want patch notes sent to the announcements channel, default = No
    - `map_channel`: channel <Optional> - The channel you want the map sent to. Set this to your current set channel to unset it.
    - `language`: string <Optional> - The language you want the bot to respond in

`/terminid`
- Returns information on a Terminid or variation.
  - Options:
    - `species`: string <Optional> - A specific 'main' species
    - `variation`: string <Optional> - A specific variant of a species

`/warbond`
- Returns a basic summary of the items in a specific warbond.
  - Options:
    - `warbond`: string [Required] - The warbond you want to lookup

`/weapons`
- Returns information on a specific weapon.
  - Options:
    - `/weapons primary`
      - `primary`: string [Required]- The Primary weapon you want to lookup
    - `/weapons secondary`
      - `secondary`: string [Required]- The Secondary weapon you want to lookup
    - `/weapons grenade`
      - `grenade`: string [Required]- The Grenade you want to lookup

`/illuminate`
- Returns information on an Illuminate or variation.
  - Options:
    - `species`: string <Optional> - A specific 'main' illuminate
    - `variation`: string <Optional> - A specific variant of an illuminate

`/stratagem`
- Returns information on a stratagem.
  - Options:
    - `stratagem`: string [Required] - The stratagem you want to lookup

`/feedback`
- Provide feedback for the bot that goes directly to me

`/stats`
- Returns information on the bot

`/major_order`
- Returns information on an Automaton or variation.
  - Options:
    - `public`: string <Optional> - If you want the response to be seen by others in the server.

## Support
Available here: [Discord Support Server](https://discord.gg/Z8Ae5H5DjZ)

## Contributing
Contributions are welcome!

To contribute to localization:
1. Open an issue with the Language Request template
2. Create a pull request and add a .json file with your language's code found [here](https://github.com/Stonemercy/Galactic-Wide-Web/blob/d28d96b81c43655ed7be0c07e118f4752ba11acf/data/lists.py#L521)
