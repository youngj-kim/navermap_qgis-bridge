# Installation test checklist — 2026-10-27

[한국어](install-test-checklist.md) | English

Target: the `0.2.0` development build. [Installation and setup](setup.en.md) · [User guide](usage.en.md). Check items only after verifying the expected result in the actual viewer. Automated/offline checks have been completed, but environment-specific live NAVER integration and exact QGIS 3.34 verification remain outstanding.

## 1. Preparation and installation

- [ ] Record the QGIS version, operating system, and test ZIP filename.
- [ ] Prepare a test QGIS profile separate from any profile linked to development source.
- [ ] Install through **Plugins → Manage and Install Plugins → Install from ZIP**, then restart QGIS.
- [ ] The plugin menu/toolbar appears only once and the viewer opens.
- [ ] Enter Maps and API HUB credentials in local settings. Map/Street View display without authentication errors.

Do not put credentials in checklists, screenshots, or issue reports. Run QGIS 3/4 external-browser checks sequentially. Close an earlier QGIS external connection using default port 8083, and open a fresh tab from the plugin rather than reusing an old browser tab.

## 2. Priority checks: position and zoom

Run this group in both **QGIS 3.34+ with the external browser** and **QGIS 4 with the embedded viewer**. If QGIS 4 lacks an embedded web view, test external mode and record that fact.

- [ ] Moving the QGIS canvas moves the NAVER map and Street View to that location.
- [ ] Dragging the NAVER map moves the QGIS center without repeated jumping after release.
- [ ] Moving within Street View updates the map/QGIS position and heading.
- [ ] QGIS wheel zoom changes the NAVER map to a similar scale. **Street View capture position and the location marker stay unchanged.**
- [ ] NAVER wheel/button zoom changes the QGIS scale. **Street View capture position and the location marker stay unchanged.**
- [ ] Zooming around the pointer does not unnecessarily move Street View to a different place.
- [ ] Repeat movement/zoom checks with EPSG:4326, EPSG:3857, and your usual projected project CRS.

NAVER zoom levels are discrete, so displayed scale numbers need not be identical. Ground distance per pixel should be similar, without repeated zooming or oscillation.

## 3. Viewer and map settings

- [ ] All four layouts remain selectable when the search panel is hidden. Reopening it preserves query, origin/destination, waypoints, and results.
- [ ] Search displays results immediately; selecting one or clicking the map hides them. There is no separate results-expand button.
- [ ] Normal → satellite → satellite with labels switching works while preserving position, route, and Street View capture position.
- [ ] The coverage toggle shows/hides roads with Street View imagery; it does not change the capture date or position.
- [ ] Drag the divider and swap panes in all four layouts: map above, Street View above, map left, and Street View left.
- [ ] Floating/redocking and resizing the dock cause no white gaps, clipping, or obscured controls. The first floating window stays within the screen.
- [ ] Full-screen switching and Esc return work.
- [ ] Capture date updates when Street View moves; missing information displays **Capture date unavailable**, not the previous date.

## 4. Search and route settings

- [ ] Enter `127.1,37.4` to move directly without waiting for place-search results.
- [ ] Search a place such as `서울역` (Seoul Station), a road-name address, and a parcel address; select results to move.
- [ ] After a place search, enter coordinates; a late place result does not overwrite the coordinate selection.
- [ ] Generate a route with origin/destination and at least one waypoint; the route line and instruction points appear.
- [ ] Swapping origin/destination, reordering waypoints, and deleting them affect the next query. The maximum is five waypoints.
- [ ] Prioritize free and avoid motorways cannot both be selected. An avoidance choice disables route priority, and completion text shows the option actually used.
- [ ] Clearing avoidance restores real-time optimal/fast/comfortable selection. Comfortable is not labeled shortest distance.
- [ ] Hi-pass route settings are disabled as **unsupported**, and motorcycles are not in the vehicle list.
- [ ] Selecting an instruction moves to its location and selects the corresponding QGIS feature.

## 5. Cancellation, errors, and project changes

- [ ] Enter place names for origin/destination, generate, and immediately cancel. Late geocoding does not restart the route, and inputs become usable again.
- [ ] Cancel while waiting for a route response, then query again. An already completed route is not treated as a pending cancellation.
- [ ] Temporarily disconnect and query; an error/timeout appears and inputs recover. Route API timeout is 30 seconds; missing bridge response recovery is 35 seconds. Place resolution is separate.
- [ ] Create/open another project during a route query. An old response does not later add a route to the new project.
- [ ] Project changes clear the displayed route, instructions, input pins, and inputs, while **session history remains** selectable in the new project.
- [ ] A project change during a save/import dialog prevents the old operation from applying to the new project. Mark unperformed if this situation cannot be reproduced.
- [ ] Disabling/re-enabling the plugin does not duplicate menus or docks. This does not require session history to survive plugin shutdown/restart.

If a response is too fast to reproduce cancellation or timeout, record **unperformed**, not passed. Repeated live API queries are unnecessary.

## 6. History and files

- [ ] Select, load into inputs, and delete a newly generated route's history.
- [ ] Save to GeoPackage and reimport it, preserving route, instructions, and inputs.
- [ ] Export GeoJSON, Shapefile, and GPX; reopen in QGIS and check coordinates, geometry, and key attributes.
- [ ] New-route toll/estimated taxi fare survives GPKG/GeoJSON/SHP attributes. Older missing fares remain NULL rather than becoming zero.
- [ ] Load legacy history with uppercase fuel values or multiple avoidance values without errors. Multiple avoidance values are restored as the previously effective prioritize-free choice, with an explanation.
- [ ] If Kakao QGIS Bridge is installed, open the new NAVER GPKG in its route comparison and check distance, duration, toll, and taxi fare. Otherwise record unperformed.

The existing GPX extension format is retained; GPKG is the input format for this fare comparison.

## 7. Directions, history, and language

- [ ] On first use, hiding the search panel leaves History and Import files visible.
- [ ] From empty History, select Directions; tabs remain and an empty-instructions message appears. Collapse and reopen with −/+.
- [ ] Hiding/showing the search panel does not change the selected directions/history tab or its collapsed state.
- [ ] Import multiple history files, then select a duplicate file again without adding duplicate entries.
- [ ] Checkboxes, Select all, and Delete selected work. Canceling deletion preserves history and original files.
- [ ] The initial language and place search are Korean. EN/KR switching preserves map, inputs, and displayed route.
- [ ] Generate a new route in EN to display API-provided English names, then generate in KR to display Korean instructions.
- [ ] Switching language does not re-query existing history or replace stored originals. Known Korean formats display in English in EN mode, and original-text tooltips work.

## Result template

```text
ZIP filename:
QGIS version / OS:
Embedded viewer or external browser / browser version:
Project CRS:
Passed groups:
Failed item numbers and symptoms:
Steps to reproduce:
Expected / actual result:
Unperformed items and reasons:
Error messages or screenshots (without credentials):
```
