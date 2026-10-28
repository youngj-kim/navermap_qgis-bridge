# Development, testing, and packaging

[한국어](development.md) | English · [Home](../README.en.md) · [Release checklist](release-checklist.en.md) · [Test records (Korean)](../TESTING.md)

## Source structure

| Location | Responsibility |
| --- | --- |
| `navermap_qgis_bridge/plugin.py` | Plugin lifetime, settings menus, embedded/external connections |
| `api_protocol.py`, `api_requests.py`, `api_transport.py` | Pure parameters, Qt requests, and request lifetime |
| `search_routes.py`, `route_inputs.py` | Search/route coordination and input validation |
| `route_history.py`, `history_operations.py`, `history_schema.py` | History, transactions, and field compatibility |
| `history_exports.py`, `gpx_export.py` | GIS/GPX files and styling |
| `canvas_sync.py`, `view_scale.py`, `map_layers.py` | Position/zoom synchronization and layers |
| `web_bridge.py`, `external_bridge.py`, `viewer_messages.py` | Qt/HTTP contracts and response delivery |
| `viewer_document.py`, `web/viewer_assets.json` | Shared embedded/external web-document assembly |
| `web/js/i18n.js`, `map_language.js`, `guidance_language.js` | UI dictionary, language switching, and display translation of existing TBT |
| `compat.py` | QGIS 3/4 API differences |

Entries shown as filenames also live under `navermap_qgis_bridge/`. The web manifest's script order controls initialization; do not reorder it arbitrarily. The source HTML contains assembly placeholders and is not a standalone runnable viewer.

## Automated checks

Run from the repository root. Checks do not use real credentials or automatically install development tools.

```powershell
python -B tests/run_checks.py --group core --group web
```

`core` covers Python inputs, parameters, transport, schemas, and document assembly. `web` uses Node.js and test-only Playwright with a mocked SDK to check language, search, external commands, zoom, layouts, and history. You may need `--node` or `NODE_PATH`. To use installed Chrome, set `TEST_BROWSER_CHANNEL=chrome`.

Web development dependencies are defined in `tests/web/package.json`. Install them only when needed:

```powershell
npm --prefix tests/web install
npm --prefix tests/web exec -- playwright install chromium
```

For QGIS runtime checks, specify installed launchers. These paths are examples from the development machine; replace them with your actual installation paths.

```powershell
python -B tests/run_checks.py --group qgis --qgis-launcher 'C:\Program Files\QGIS 3.44.14\bin\python-qgis-ltr.bat' --qgis-launcher 'C:\Program Files\QGIS 4.2.2\bin\python-qgis.bat'
```

The runtime group covers layers, files, localhost HTTP, project lifetime, history precision, batch operations, and request language. The fixed-port-8083 check can conflict with another service; close other QGIS external connections first. Record live NAVER SDK checks separately with the [installation checklist](install-test-checklist.en.md).

## Build an installation ZIP

```powershell
python -B tools/build_plugin.py --experimental
```

The version is read from `metadata.txt`; `--experimental` uses a version-only preview filename. Stable packages require `experimental=False` and `--release`. Use `--label YOUR_TEST_LABEL` for test packages. Output is `dist/navermap_qgis_bridge-0.99.zip`. Existing ZIPs are not overwritten, so use a different test label for another build.

The builder checks the single plugin root, Python syntax/internal imports, web assets, and ZIP CRC. It includes installation READMEs, setup/usage/troubleshooting guides, changelogs, and manual checklists in Korean and English. It excludes development tests/tools, local settings, and caches. Relative documentation links must work inside the ZIP.

## Change and release policy

Consider QGIS 3.34+ and 4.x, including external-browser and embedded viewers. Do not mark unexecuted checks as passed. Do not commit API keys, `settings.json`, or generated HTML containing credentials. Keep GPL-2.0-or-later compatibility.

Before release, follow the [release checklist](release-checklist.en.md). Record changes in [CHANGELOG.en.md](../CHANGELOG.en.md) and the Korean counterpart; detailed execution results remain in [TESTING.md (Korean)](../TESTING.md). Earlier design reasoning is retained in the [refactoring record (Korean)](../REFACTORING.md) and [archive index](archive/README.en.md).

## Reproduce repository security checks

Before upload, run Bandit and detect-secrets on the plugin folder included in the installation ZIP. These are development tools, not plugin runtime dependencies.

```powershell
python -m pip install --target dist/security-tools bandit detect-secrets flake8
$env:PYTHONPATH = "$PWD/dist/security-tools"
python -m bandit -r navermap_qgis_bridge
python -m detect_secrets scan --all-files navermap_qgis_bridge
python -m flake8 navermap_qgis_bridge --select E731,F821,F822,F823
```

Version 0.99.1 addresses the repository's three Bandit findings, seven secret detections, and four Qt6 findings. Setting identifiers are not credentials; only Python constant names change, preserving actual stored keys/environment names. GPX generates XML without parsing it, so the B405 review is documented on that single import. A regression guard limits the module to XML-generation APIs. No whole-rule/path exclusions or baseline are added.

Local results do not guarantee server approval. See the [official scanner guidance](https://plugins.qgis.org/docs/security-scanning/tools) and check Security/Qt6 results for the actual new version.
