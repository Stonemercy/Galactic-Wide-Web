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
`/help`
- Get some help for a specific command, or a list of every command by using "all".
  - Options:
    - `command`: string [Required] - The command you want to lookup, use "all" for a list of all available commands
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/major_order`
- Returns information on an Automaton or variation.
  - Options:
    - `public`: string <Optional> - If you want the response to be seen by others in the server.

`/map`
- Get an up-to-date map of the galaxy
  - Options:
    - `faction`: string <Optional> - The faction to focus on
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/meridia`
- Get current and historical location data of the Meridian Wormhole
  - Options:
    - `public`: string <Optional> - If you want the response to be seen by others in the server.

`/planet`
- Returns the war details on a specific planet.
  - Options:
    - `planet`: string [Required] - The planet you want to lookup
    - `with_map`: string <Optional> - Do you want a map showing where this planet is?
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/setup`
- Change the GWW settings for your server.

`/steam`
- Get previous Steam posts
  - Options:
    - `public`: string <Optional> - Do you want other people to see the response to this command?

`/warfront`
- Returns information on a specific War front
  - Options:
    - `faction`: string [Required] - The faction to focus on
    - `public`: string <Optional> - If you want the response to be seen by others in the server.

`/wiki`
- Browse the GWW's wiki. Uses buttons to check information on the following subjects: 
  - DSS
  - Enemies
    - Automaton
    - Illuminate
    - Terminids
  - Warbonds
  - Equipment
    - Weapons
      - Primary
      - Secondary
      - Grenade
    - Boosters
    - Stratagems

## Support
Available here: [Discord Support Server](https://discord.gg/Z8Ae5H5DjZ)

## Contributing
Contributions are welcome!

To contribute to localization:
1. Open an issue with the Language Request template
2. Create a pull request and add a .json file with your language's code found [here](https://github.com/Stonemercy/Galactic-Wide-Web/blob/d28d96b81c43655ed7be0c07e118f4752ba11acf/data/lists.py#L521)
