<h1 align="center">Galactic Wide Web</h1>

<p align="center">
  <a href="https://discord.gg/Z8Ae5H5DjZ">
    <img alt="Support Server" src="https://img.shields.io/discord/1212722266392109088?style=for-the-badge&logo=discord&label=Support%20Server">
  </a>
	<a href="https://discord.gg/Z8Ae5H5DjZ">
		<img alt="Servers" src="https://img.shields.io/badge/servers-5000+-brightgreen?&logo=discord&style=for-the-badge">
	</a>
  <a href="https://discord.gg/Z8Ae5H5DjZ">
		<img alt="User Installs" src="https://img.shields.io/badge/user installs-1300+-brightgreen?&logo=discord&style=for-the-badge">
	</a>
	<a href="https://discord.gg/Z8Ae5H5DjZ">
		<img alt="Visible Users" src="https://img.shields.io/badge/visible users-625,000+-brightgreen?&logo=discord&style=for-the-badge">
	</a>
  <br>
  <a href="LICENSE">
		<img alt="License" src="https://img.shields.io/github/license/Stonemercy/Galactic-Wide-Web?style=for-the-badge">
	</a>
	<img alt="Commits made" src="https://img.shields.io/github/last-commit/Stonemercy/Galactic-Wide-Web?style=for-the-badge">
  <img alt="Code Size" src="https://img.shields.io/github/languages/code-size/Stonemercy/Galactic-Wide-Web?style=for-the-badge">
  <img alt="Code Format" src="https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge">
  <br>
  <a href="https://ko-fi.com/R6R51OSRX8">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg">
  </a>
</p>

<p align="center">
  Galactic Wide Web is a Discord application/bot for Helldivers 2 players that provides real-time information on the Galactic War.
  <br>
  It pulls live data from the official Helldivers 2 API and the Steam API, and keeps an auto-updating dashboard refreshed every 15 minutes with a strategic overview of the current war effort.<br><br>
  The bot includes slash commands, interactive buttons, dropdowns, and embedded content. All interactions take place in text channels.
  <br>
  Server administrators (or those with Manage Server permissions) can configure which channels are used for dashboards and announcements.
  <br>
  The bot has a variety of Helldivers 2 data, including:
</p>
<div align="center">
  <ul style="display: inline-block; text-align: left;">
    <li>Personal Orders<br><b>EXCLUSIVE!</b></li>
    <li>DSS Vote counts<br><b>EXCLUSIVE!</b></li>
    <li>Major Orders</li>
    <li>Control Centre (campaigns)</li>
    <li>Superstore</li>
    <li>Warbonds</li>
    <li>Dispatches</li>
    <li>Global Events</li>
    <li>DSS movements and Tactical Action updates</li>
    <li>Planetary Region changes</li>
    <li>Campaign wins and losses</li>
    <li>and Steam patch notes.</li>
  </ul>
</div>
  <p align="center">
  <br>
  The bot also supports multilingual output, currently offering English, French, German, Italian, Portuguese (BR),
  <br>
  Russian, Spanish, Chinese (Traditional), and Turkish, with more languages welcome via contributions.
  <br><br>
  Built using Disnake, it stores settings in PostgreSQL and uses Pillow and opencv to generate maps.
</p>

## Quick Navigation
- [Inviting the Bot](#inviting-the-galactic-wide-web)
- [Examples](#examples)<br>
| Here are | the bots | commands |
|---|---|---|
| [`/check_missing_translations`](#check_missing_translations-language_to_check-fr) | [`/community_servers`](#community_servers) | [`/control_centre`](#control_centre) |
| [`/dispatches`](#dispatches) | [`/dss`](#dss) | [`/dss_votes`](#dss_votes) |
| [`/global_events`](#global_events) | [`/major_order`](#major_order) | [`/map`](#map) |
| [`/personal_order`](#personal_order) | [`/planet`](#planet-planet-124-bore-rock) | [`/setup`](#setup) |
| [`/steam`](#steam) | [`/subfaction`](#subfaction) | [`/superstore`](#superstore) |
| [`/warbonds`](#warbonds) | [`/warfront`](#warfront-faction-automaton) | |
- [Support](#support)
- [Contributing](#contributing)

## Inviting the Galactic Wide Web
Want to try out the GWW on your server or your account? [Invite Link](https://discord.com/oauth2/authorize?client_id=1212535586972369008)

## Examples
### `/check_missing_translations language_to_check: fr`
<img src="resources/readme/check_missing_translations.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/community_servers`
<img src="resources/readme/community_servers.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/control_centre`
<img src="resources/readme/control_centre.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/dispatches`
<img src="resources/readme/dispatches.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/dss`
<img src="resources/readme/dss.png">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/dss_votes`
<img src="resources/readme/dss_votes.png">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/global_events`
<img src="resources/readme/global_events.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/help command: check_missing_translations`
<img src="resources/readme/help.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/major_order`
<img src="resources/readme/major_order.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/map`
<img src="resources/readme/map.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/personal_order`
<img src="resources/readme/personal_order.png">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/planet planet: 124-BORE ROCK`
<img src="resources/readme/planet.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/setup`
<img src="resources/readme/setup.png">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/steam`
<img src="resources/readme/steam.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/subfaction`
<img src="resources/readme/subfaction.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/superstore`
<img src="resources/readme/superstore.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/warbonds`
<img src="resources/readme/warbonds.png" width="500">
<p align="right"><a href="#top">Back to Top ↑</a></p>

### `/warfront faction: Automaton`
<img src="resources/readme/warfront.png">
<p align="right"><a href="#top">Back to Top ↑</a></p>

## Support
Available here: [Discord Support Server](https://discord.gg/Z8Ae5H5DjZ)
<p align="right"><a href="#top">Back to Top ↑</a></p>

<iframe src="https://discord.com/widget?id=1212722266392109088&theme=dark" width="350" height="500" allowtransparency="true" frameborder="0" sandbox="allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts"></iframe>

## Contributing
Contributions are welcome!

To contribute to localization:
1. Open an issue with the Language Request template
2. Create a pull request and add a .json file to the [data/languages/](https://github.com/Stonemercy/Galactic-Wide-Web/tree/main/data/languages) folder

or just head to the Discord Support Server above
<p align="right"><a href="#top">Back to Top ↑</a></p>
