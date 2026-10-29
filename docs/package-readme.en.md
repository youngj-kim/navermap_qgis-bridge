# Naver Map QGIS Bridge 1.0

[한국어](README.md) | English

Synchronize QGIS with NAVER Map and Street View, search places, generate driving routes/instructions, save history, and export GIS files. This 1.0 stable package targets QGIS 3.34 LTR or later and QGIS 4.x.

## Get started

1. Install this package through **Plugins → Manage and Install Plugins → Install from ZIP**.
2. Restart QGIS and enable **Naver Map QGIS Bridge**.
3. Enable Dynamic Map, Geocoding, and Directions 5 in your Maps Application and register Web URL `http://localhost`.
4. Set the Maps Client ID / Client Secret in the plugin menu, then open **Naver Map / Street View**.
5. Configure separate NAVER API HUB Client ID / Client Secret credentials for place-name searches.

Keys are stored in QGIS user settings without additional plugin encryption. Environment variables override stored settings. Do not share actual keys or save them in this folder. Native menus remain in Korean; the setup guide lists their exact labels.

## Included documentation

- [Installation, updates, and API keys](docs/setup.en.md)
- [User guide](docs/usage.en.md)
- [Troubleshooting](docs/troubleshooting.en.md)
- [Release notes and changelog](CHANGELOG.en.md)
- [Post-install checklist](docs/install-test-checklist.en.md) · [Browser checklist](docs/install-test-checklist.en.html)

Search defaults to Korean. Generate a new route in EN mode to request English place-name instructions. Existing history keeps its stored originals; changing language alone does not re-query names or routes.

History is available on the first panel collapse; directions/history has its own −/+ controls. For external mode, use **외부 연동 창 열기** (“Open external connection window”) in the dock to open a fresh tab. Keep QGIS running and close old session tabs.

Save required history to GeoPackage before closing. Batch deletion affects session history only, not original files. Use GPKG/GeoJSON if SHP text exceeds field limits.

On 2026-10-27, the user confirmed that fix4 worked correctly. Development verification used Windows QGIS 3.44.14 / 4.2.2; this does not mean exact QGIS 3.34 or all OS/viewer combinations were fully verified. Metadata is 1.0, marked non-experimental, and this package is prepared for a QGIS repository update. Repository upload/approval and publishing a GitHub Release are separate steps.

See the [GitHub repository](https://github.com/youngj-kim/navermap_qgis-bridge) for source, development documentation, and verification records. Development tests and build tools are not included in this installation package.

## License

[GPL-2.0-or-later](LICENSE). NAVER APIs are subject to the provider's terms and usage limits. This is not an official NAVER product and does not register map tiles as QGIS XYZ/TMS layers.
