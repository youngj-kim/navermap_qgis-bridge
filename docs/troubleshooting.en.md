# Troubleshooting

[한국어](troubleshooting.md) | English · [Home](../README.en.md) · [Installation and API keys](setup.en.md) · [User guide](usage.en.md)

## Check by symptom

| Symptom | First checks |
| --- | --- |
| Map authentication error or blank map | Maps Client ID, Dynamic Map enabled, and console Web URL `http://localhost` without port/path |
| Coordinates work but place names do not | API HUB Local Search enabled and its separate Client ID / Client Secret |
| Only address search fails | Maps Geocoding enabled and map SDK authentication |
| Only route generation fails | Maps Directions 5 enabled and its Client ID / Client Secret |
| Changing a key in the menu has no effect | Environment variables override stored values; check the QGIS launch environment/profile and restart |
| External connection screen instead of embedded viewer | Qt WebEngine/WebChannel availability; continue with the external-window button |
| External tab opens but does not synchronize | Keep QGIS running; open a fresh tab from the plugin and close the old session tab |
| Port 8083 is busy | Another port is selected automatically; use the plugin-opened address rather than fixing two servers to one port |
| Korean names in EN instructions | Check whether this is existing Korean history; select EN and generate a new route to request English names |
| English instructions in KR mode | English stored originals are retained; generate a new route in KR for Korean instructions |
| No history after hiding controls | Use the 2026-10-27 fix4 build or later; reinstall the ZIP and restart QGIS and external tabs |
| History reimport fails | Check the GPKG or route/instruction file pair, and use a build with the coordinate-precision fix |
| SHP export fails on long text | Use GPKG/GeoJSON; check UTF-8 byte width and waypoint field limits |
| QGIS/map scale numbers differ slightly | NAVER has discrete zoom levels; check for repeated movement/oscillation rather than relying on exact numbers |

## Connection and request recovery

External mode uses a session-authenticated local server. Old tabs or manually entered URLs without the session token may be rejected. A map left visible after QGIS closes is no longer connected.

Use **Cancel** during route search. Place resolution and route API requests are separate stages, so waiting times depend on the connection. Once inputs recover after a timeout, check settings/connectivity before retrying.

For credentials, permissions, and usage limits, see [Maps troubleshooting](https://guide.ncloud-docs.com/docs/en/application-maps-troubleshoot) and the [API HUB documentation](https://api.ncloud-docs.com/docs/en/naver-api-hub-overview). Do not replace a key with credentials for a different service.

## Report an issue

Use [GitHub Issues](https://github.com/youngj-kim/navermap_qgis-bridge/issues) and provide the information below. Remove Client IDs, Client Secrets, and session tokens from screenshots and external-viewer URLs before sharing.

```text
Plugin version / installation ZIP name:
QGIS version / operating system:
Embedded viewer or external browser / browser version:
Steps to reproduce:
Expected / actual result:
Error message (without credentials or session tokens):
```

Do not attach QGIS settings files containing credentials or generated viewer HTML. If a history file is needed to reproduce the issue, prepare an example without sensitive locations or addresses.
