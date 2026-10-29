# Naver Map QGIS Bridge

[한국어](README.md) | English

Synchronize the position and zoom of QGIS with NAVER Map and Street View. Search for places and addresses, generate driving routes with turn-by-turn instructions, manage route history, and export GIS files.

**Current version: 1.0 · Stable release** · [User guide](docs/usage.en.md) · [Installation and API keys](docs/setup.en.md) · [Changelog](CHANGELOG.en.md)

[1.0 stable release · Installation ZIP](https://github.com/youngj-kim/navermap_qgis-bridge/releases/tag/v1.0) · [QGIS plugin repository](https://plugins.qgis.org/plugins/navermap_qgis_bridge/)

## Install and get started

1. Install the plugin installation ZIP through **Plugins → Manage and Install Plugins → Install from ZIP** in QGIS.
2. Restart QGIS and enable **Naver Map QGIS Bridge**.
3. In your NAVER Cloud Maps Application, enable Dynamic Map, Geocoding, and Directions 5, and register `http://localhost` as the Web URL.
4. Set the Maps Client ID and Client Secret in the plugin menu, then open **Naver Map / Street View**.
5. For business and organization name searches, also configure a separate NAVER API HUB Client ID and Client Secret.

Each user supplies their own credentials. See [Installation and API keys](docs/setup.en.md) for obtaining credentials, distinguishing the four key settings, updating the plugin, and using an external browser. Native plugin menus remain in Korean; the setup guide identifies their exact labels.

For international users, NAVER Cloud account eligibility depends on the registration country and account type. As of October 29, 2026, individual registration outside Korea is not supported; business registration is supported in selected countries, subject to verification and payment requirements. Check the [official NAVER Cloud registration FAQ](https://www.ncloud.com/support/faq/all/1104) for current eligibility. English UI support does not guarantee API account eligibility. Overseas account registration and end-to-end API access with this plugin have not been verified. Place search and driving routes in this plugin target South Korea.

The 1.0 stable ZIP is prepared for a QGIS plugin repository update. The experimental 0.99.1 version was approved; this package prepares the stable 1.0 release. Repository upload/approval and publishing a GitHub Release are separate steps. **Code → Download ZIP** downloads the source repository, not a QGIS installation ZIP. The installation guide explains how to use a supplied installation package or build one from source.

## Main features

- QGIS↔NAVER Map movement and zoom synchronization, with Street View position and heading
- Place, address, and longitude/latitude search; normal/satellite maps and Street View coverage
- Driving routes, up to five waypoints, avoidance and vehicle settings, and ordered instructions
- Independently collapsible search/route controls and directions/history; four layouts and full screen
- Import multiple history files; select entries with checkboxes and delete them together
- GeoPackage, GeoJSON, Shapefile, and GPX export
- **EN / KR** switching, with API-provided English place names for new routes requested in EN mode

## Supported environments and verification

| Area | Target and behavior |
| --- | --- |
| QGIS | 3.34 LTR or later, and QGIS 4.x |
| Embedded viewer | Environments with Qt WebEngine and WebChannel |
| External browser | Fallback when the embedded web view is unavailable; also used with QGIS 3 |
| Development checks | Windows QGIS 3.44.14 / 4.2.2 runtimes and web tests with a mocked SDK |

On 2026-10-27, the user confirmed that the `fix4` build worked correctly. This does not establish verification on exact QGIS 3.34 or every operating-system/viewer combination. Detailed results are preserved in [TESTING.md (Korean)](TESTING.md).

## Before you use it

Route history is managed within the session. **Save to GeoPackage before closing.** Switching projects and closing the plugin have different history lifetimes; see the [user guide](docs/usage.en.md).

The initial language and place search default to Korean. New routes generated in EN mode request English instructions. Existing history keeps its original text; switching language alone does not request a new route.

Maps are displayed through the NAVER SDK, not registered as QGIS XYZ/TMS basemaps. **Current position** means the NAVER map center, not device GPS. API keys are saved in QGIS user settings without additional encryption by the plugin.

## Documentation

| What you need | Document |
| --- | --- |
| Installation, updates, API keys, localhost | [Installation and API keys](docs/setup.en.md) |
| Viewer, search, routes, history, language | [User guide](docs/usage.en.md) |
| Authentication, connection, and export issues | [Troubleshooting](docs/troubleshooting.en.md) |
| Version changes and development history | [Release notes and changelog](CHANGELOG.en.md) |
| Post-install checks | [Manual checklist](docs/install-test-checklist.en.md) · [Browser checklist](docs/install-test-checklist.en.html) |
| Development, testing, packaging | [Development guide](docs/development.en.md) · [Release checklist](docs/release-checklist.en.md) |
| Fare comparison with Kakao | [GPKG fare comparison](docs/fare-comparison.en.md) |
| Earlier implementation, reviews, and tests | [Archive index](docs/archive/README.en.md) |

## License

[GPL-2.0-or-later](LICENSE). NAVER maps and APIs are subject to the provider's terms and usage limits. This is not an official NAVER product. Actual API keys and map tiles are not distributed.
