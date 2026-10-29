# Installation and API keys

[한국어](setup.md) | English · [Home](../README.en.md) · [User guide](usage.en.md) · [Troubleshooting](troubleshooting.en.md)

## 1. Requirements

Use QGIS 3.34 LTR or later, or QGIS 4.x, an internet connection, and your own NAVER Cloud credentials. A plugin installation does not require separate Python, Node.js, or Playwright installations; those tools are for source development and tests.

The embedded viewer needs Qt WebEngine and WebChannel. When unavailable, the plugin provides an external-browser connection screen. QGIS version alone does not determine whether an embedded web view is available.

## 2. Install and update

### Using an installation ZIP

1. Obtain a plugin installation ZIP. Its only top-level folder must be `navermap_qgis_bridge`.
2. In QGIS, open **Plugins → Manage and Install Plugins → Install from ZIP**. Labels depend on the QGIS interface language.
3. Select the ZIP, install it, and restart QGIS.
4. Enable **Naver Map QGIS Bridge** in the installed plugins list.
5. Open **Naver Map / Street View** from the plugin menu or toolbar.

Before updating, save any history you need and close old external-browser tabs. Install the new ZIP, restart QGIS, and open a fresh tab from the plugin. Credentials in the same QGIS profile are stored separately from the plugin folder.

The current metadata version is `1.0`, marked non-experimental. Names such as `fix4` identify earlier 0.2.0 test packages. Use `navermap_qgis_bridge-1.0.zip` for the 1.0 stable release upload. Installation packages can be found under [Releases](https://github.com/youngj-kim/navermap_qgis-bridge/releases).

### Installing from source

Do not install the repository's **Code → Download ZIP** directly in QGIS. It also contains development documentation and tests. Use the build tool in the [development guide](https://github.com/youngj-kim/navermap_qgis-bridge/blob/main/docs/development.en.md), or copy only the plugin folder.

Find the actual profile with **Settings → User Profiles → Open Active Profile Folder**, then install under `python/plugins/navermap_qgis_bridge`. Include every HTML, CSS, JavaScript, manifest, and SVG resource under `web`. If your development source is linked through a junction or symbolic link, test ZIP installation in a separate profile.

## 3. Required APIs and credentials

| Feature | NAVER service | Credential used by the plugin |
| --- | --- | --- |
| Map and Street View | Maps Dynamic Map / JavaScript API | Maps Client ID |
| Address search | Maps Geocoding through the JavaScript SDK | Maps Client ID |
| Driving routes and English place-name instructions | Maps Directions 5 | Maps Client ID + Client Secret |
| Business, organization, and place-name search | NAVER API HUB Search → Local | API HUB Client ID + Client Secret |

The plugin manages Maps and API HUB credentials separately. Do not substitute general NAVER Developers Search API keys or Cloud account Access Keys. Local search uses the endpoint and authentication scheme documented in [NAVER API HUB Local Search](https://api.ncloud-docs.com/docs/en/naver-api-hub-search-local).

### Maps Application

1. Open the Maps service in the [NAVER Cloud console](https://console.ncloud.com/) and create or select an Application.
2. Enable Dynamic Map, Geocoding, and Directions 5.
3. Find the Client ID and Client Secret in the Application's authentication information.
4. Register this **Web URL** under the service environment:

```text
http://localhost
```

Do not include a port number or path in the console Web URL. This follows [NAVER's authentication troubleshooting guidance](https://guide.ncloud-docs.com/docs/en/application-maps-troubleshoot). Console navigation can change; use the service's Application and authentication settings as the reference.

### NAVER API HUB

In NAVER Cloud's NAVER API HUB, configure an Application for **Search → Local** and obtain its Client ID and Client Secret separately from your Maps credentials. Consult the [official API HUB documentation](https://api.ncloud-docs.com/docs/en/naver-api-hub-overview) for service registration, usage limits, and billing terms.

## 4. Enter credentials in QGIS

Use the four plugin menu commands below. These native menu labels remain in Korean even when the web viewer is in EN mode; `설정...` means “Settings...”.

| Actual plugin menu label | Value to enter |
| --- | --- |
| Naver Maps Client ID 설정... | Maps Client ID |
| Naver Maps Client Secret 설정... | Maps Client Secret |
| Naver API HUB Client ID 설정... | API HUB Client ID |
| Naver API HUB Client Secret 설정... | API HUB Client Secret |

Keys must contain printable ASCII characters without spaces or line breaks. They are stored in the current QGIS user profile. The plugin adds no encryption, so manage access to the profile and computer. Do not include keys in issue reports, screenshots, or repositories.

### Environment variables

Environment variables override values saved in QGIS. IDs in this PowerShell example are placeholders; enter Client Secrets at runtime. Read-Host input is visible, so use the QGIS password dialog when sharing your screen. Launch QGIS from a process that inherits these variables; setting them later does not update an already-running QGIS process.

```powershell
$env:NAVER_MAP_CLIENT_ID = "YOUR_NAVER_MAP_CLIENT_ID"
$env:NAVER_MAP_CLIENT_SECRET = Read-Host "Enter Maps Client Secret"
$env:NAVER_API_HUB_CLIENT_ID = "YOUR_NAVER_API_HUB_CLIENT_ID"
$env:NAVER_API_HUB_CLIENT_SECRET = Read-Host "Enter API HUB Client Secret"
```

Legacy `settings.json` is read only as a compatibility source for the Maps JavaScript Client ID. For new installations, use QGIS settings or environment variables. Copying the example JSON alone does not configure all four credentials.

## 5. localhost and the external browser

| Purpose | Address or behavior |
| --- | --- |
| NAVER console registration | `http://localhost`, without port or path |
| Default embedded-document origin | `http://localhost:8083/navermap_qgis_bridge/` |
| External connection | Local server on port 8083 by default; another port is selected if busy |

In external mode, click **외부 연동 창 열기** (“Open external connection window”) in the QGIS dock. Keep QGIS running. Use the fresh address opened by the plugin so session authentication and commands work. Do not reuse an old session's tab or address.

`NAVER_MAP_BASE_URL` is an advanced override for the embedded document's origin and usually need not be set. If you previously specified port 8082 or another value, remove the override to use the default, or update it as below and restart QGIS. It does not fix the external server's actual listening port.

```powershell
$env:NAVER_MAP_BASE_URL = "http://localhost:8083/navermap_qgis_bridge/"
```

## 6. First-run check

Check map/Street View display → coordinate movement with `127.1,37.4` → place/address search → a short driving route → GeoPackage export. To check English place names, **select EN, then generate a new route**. See [Troubleshooting](troubleshooting.en.md) if anything fails.
