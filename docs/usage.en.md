# User guide

[한국어](usage.md) | English · [Home](../README.en.md) · [Installation and API keys](setup.en.md) · [Troubleshooting](troubleshooting.en.md)

## Open and arrange the viewer

Open **Naver Map / Street View** in QGIS. If the embedded viewer is unavailable, use **외부 연동 창 열기** (“Open external connection window”) in the dock. QGIS must remain running in external mode.

Use the top layout selector to choose map above / Street View below, Street View above / map below, map left / Street View right, or Street View left / map right. Narrow windows may turn side-by-side layouts into stacked layouts. Drag the divider to adjust the split, and use ⇅/⇄ to swap panes. Use the full-screen button to expand and Esc to return.

**Hide panel** collapses only the search and route-input controls. History remains available even on the first collapse, so you can import files. Use **− / +** at the right of directions/history to collapse that section independently. Selecting an empty Directions tab does not remove the tabs. Opening or closing the search panel preserves the selected directions/history tab and its collapsed state.

## Position, zoom, and Street View

Moving the QGIS canvas or NAVER map synchronizes their centers. Moving within Street View also updates the map/QGIS position and heading. Zoom is matched to the nearest available level using ground distance, so scale numbers need not be identical. Zoom-only changes preserve the Street View capture position.

Choose normal, satellite, or satellite with labels as the map type. The Street View coverage toggle shows roads with imagery; it does not change the center or route.

The capture date comes from the API. When unavailable, the viewer displays “Capture date unavailable.” It is not a date selector for historical imagery.

## Search places, addresses, and coordinates

Enter a place name, road-name or parcel address, or **longitude,latitude**, then search. For example, use `127.1,37.4`, with longitude first. Coordinates bypass the place-search API for movement, but map and Street View display still require internet access.

Place names use NAVER API HUB Local Search; addresses use Maps Geocoding. Select a result to move there. Results hide when selected or when you click the map; there is no separate results-expand button. Search defaults to Korean. EN mode does not translate place-search results, addresses, or your input.

## Generate a driving route

1. Enter a place, address, or `longitude,latitude` for the origin and destination.
2. Use **+ Stop** to add up to five waypoints, reorder with the up/down buttons, or remove with ×.
3. Check route priority, avoidance, and vehicle settings.
4. Click **Get route**. The route appears in the map, with route-line and instruction-point layers in QGIS.
5. Select an instruction to move to its location and select the corresponding QGIS feature.

**Current position** for an origin, destination, or stop means the NAVER map center, not device GPS. ⇅ swaps the origin and destination; the route-input × resets the inputs.

### Route options

| Setting | Behavior |
| --- | --- |
| Real-time optimal / fast / comfortable | NAVER Directions 5 priorities; comfortable does not mean shortest distance |
| Prioritize free / avoid motorways | Only one avoidance option; it replaces route priority. Clear it to restore priority selection |
| Vehicle class and fuel | API settings for toll/fuel-cost calculations |
| Hi-pass | Route-selection setting is unsupported and disabled; Hi-pass tollgate instructions may still appear |
| Motorcycles | Unsupported by this driving API |

**Cancel** stops an in-progress route search. The route API timeout is 30 seconds; the web UI uses a 35-second recovery watchdog for missing bridge responses. Resolving origin/destination place names is a separate stage.

## EN / KR and English place names

The initial language is Korean. **EN** switches to English and **KR** switches to Korean. The browser profile remembers the selection. The viewer saves position, zoom, route inputs, and displayed route before reloading. Finish any running search/route operation before switching.

| Content | Language behavior |
| --- | --- |
| Map SDK and web controls | Switch to the selected language |
| Newly generated route | EN requests `lang=en`; KR requests `lang=ko` |
| Existing Korean instructions | Known instruction templates are displayed in English in EN mode; names retain their stored text |
| Instructions generated and saved in English | Switching to KR does not create a new Korean original |
| Place-search results, user input, native QGIS menus/dialogs | Not automatically translated |

For English names in the route instructions, use **select EN → generate a new route**. Names are displayed as returned by the API. Existing history is not automatically queried again, so switching language alone does not change the route or add API calls. Hover over an instruction to see its stored original. Unrecognized instruction formats keep their original text.

## Import and delete history

After generating routes, select an entry in History to display its route and instructions. **Load** restores the stored origin, stops, destination, and options to the inputs. To query again with changed inputs or language, click **Get route**.

Use **Import files** in History, or **경로 이력 불러오기...** (“Import route history...”) in the native plugin menu, to import GeoPackage, GeoJSON, or Shapefile history. Select multiple files with Ctrl/Shift. Duplicate history is skipped. Validation or import failure rolls back that batch.

Use entry checkboxes, or **Select all → Delete selected**, to delete several entries. After confirmation, the current session's history and instructions are removed; original files are untouched. Deleting the displayed entry also clears its route display.

## Save and export

History is not saved to a file automatically. Before closing or updating, use **경로 이력 GeoPackage 저장...** (“Save route history to GeoPackage...”) in the native plugin menu. Individual entries also have **Export**.

| Format | Purpose and considerations |
| --- | --- |
| GeoPackage | Preserve route, instructions, and input attributes for reimport; recommended default |
| GeoJSON | Exchange with GIS tools; keep the generated route and instruction files together |
| Shapefile | Exchange with existing GIS workflows; keep all component files and the route/instruction pair |
| GPX | Track/waypoint exchange; the plugin provides a style-aware import command |

If UTF-8 text or waypoint JSON exceeds SHP field limits, export fails instead of truncating it. Use GPKG or GeoJSON. GPX is for general exchange; prefer GPKG for full plugin history restoration.

Import checks EPSG:4326, geometry, coordinate ranges, and route/instruction correspondence. Instruction categories from older files are corrected during import/export. Save separately to apply corrections to a file; importing alone does not rewrite it. See [fare comparison](fare-comparison.en.md) for the Kakao plugin's GPKG comparison workflow.

## Switching projects and closing

Creating or opening another project resets pending requests, the displayed route, and current inputs. History remains selectable in the same running session. Session history is not guaranteed after closing QGIS or restarting the plugin; save required results to files.

If something goes wrong, consult [Troubleshooting](troubleshooting.en.md) and record reproduction conditions with the [installation checklist](install-test-checklist.en.md).
