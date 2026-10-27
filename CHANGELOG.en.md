# Release notes and changelog

[한국어](CHANGELOG.md) | English · [Home](README.en.md) · [Update instructions](docs/setup.en.md) · [Release checklist](https://github.com/youngj-kim/navermap_qgis-bridge/blob/main/docs/release-checklist.en.md)

The version authority is `navermap_qgis_bridge/metadata.txt`. The current version is **0.2.0**, an **experimental development build**. No GitHub Release or official release tag has been published. Dates below group development changes; they do not each identify a new release. `fix1` through `fix4` are test-ZIP identifiers within the same version.

## Documentation organization — 2026-10-27

- Shortened the README to a starting point and separated installation/API keys, usage, troubleshooting, development, and release guidance.
- Added English counterparts for the README, all current guides, changelog, and checklists, with language links and English documentation in installation ZIPs.
- Consolidated user-facing changes here while preserving the original locations of earlier reviews and test records.
- Included user guides and the updated checklist in installation ZIPs. Plugin behavior and version are unchanged.

## 0.2.0 — Current development build (as of 2026-10-27)

### Viewer and language

- Separated the search/route controls from directions/history so each can collapse independently.
- Fixed the panel disappearing when an empty Directions tab was selected. History and file import remain available on the first collapse.
- Added EN/KR map/web UI switching, position/zoom/input/displayed-route restoration, and narrow-window layout improvements.
- Display known Korean TBT formats in English, including turns, roundabouts, entrances, exits, and side roads, with original-text tooltips.
- Send `lang=en` to NAVER when generating a new route in EN mode, using API-provided English place names. KR and missing language values use `ko`. The initial language and place search remain Korean.
- Preserve original history text and avoid re-querying routes merely when switching language.

### History and files

- Import files directly from History, including multiple files in one operation.
- Added entry checkboxes, Select all, and batch deletion, with confirmation, duplicate skipping, and rollback on batch-import failure.
- Fixed reimport rejection caused by rounded instruction coordinates in older GPKG files. New history coordinate attributes retain ten decimal places.

### Updating and verification scope

Save existing history before installing the new ZIP, then restart QGIS. Reopen external tabs through the plugin. Existing saved files remain importable, and importing does not overwrite originals.

On 2026-10-27, the user confirmed normal operation of `test-20261027-panel-tbt-fix4`. Their exact QGIS version, viewer mode, and per-scenario results were not specified. Python tests (70), web suites (9), QGIS 3.44.14/4.2.2 offline results, and remaining exact-QGIS-3.34/live-API checks are distinguished in [TESTING.md (Korean)](https://github.com/youngj-kim/navermap_qgis-bridge/blob/main/TESTING.md).

## 0.2.0 development changes — 2026-10-13–15

- Improved panel collapse, map types, Street View coverage, floating/redocked views, and narrow toolbars.
- Matched QGIS↔NAVER zoom using ground distance and preserved Street View position during zoom-only changes.
- Added route cancellation, a 30-second API limit, missing-response recovery, and stale-request rejection after project changes.
- Limited avoidance to one option and clarified that it replaces route priority. Disabled unsupported Hi-pass route settings and excluded motorcycles.
- Strengthened NAVER-code-based right-turn/roundabout categories, history validation, and external bridge request checks.
- Preserved toll/estimated-taxi fares, rejected overlong SHP text, and handled invalid GPX XML control characters.
- On 2026-10-15, the user confirmed that the reviewed build had no problems.

## 0.2.0 development changes — 2026-10-08

- Changed the default localhost port from 8082 to 8083. If you set an old `NAVER_MAP_BASE_URL`, see [installation](docs/setup.en.md).
- Split Python responsibilities for search, routes, history, exports, and canvas synchronization.
- Unified embedded/external document assembly through shared HTML, CSS, and a JavaScript manifest.
- Hid diagnostics by default, with `NAVER_BRIDGE_DEBUG=1` to enable them.
- Added automated checks, QGIS offline checks, and an installation-ZIP build tool.

## Initial development — 2026-07–09

- Connected NAVER Maps JavaScript API, Geocoding, Directions 5, and API HUB Local Search.
- Implemented bidirectional map/Street View/QGIS movement, coordinate search, route/instruction layers, history, and export.
- Established NAVER-specific credential menus and an independent plugin structure; improved search, synchronization, and viewer resizing.

See the [archive index](https://github.com/youngj-kim/navermap_qgis-bridge/blob/main/docs/archive/README.en.md) for dated implementation details and their original limitations. An unperformed historical check is not evidence that a later version passed it.
