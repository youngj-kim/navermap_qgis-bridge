// SPDX-License-Identifier: GPL-2.0-or-later
// The SDK language is a load-time option; reload through the native bridge for
// setHtml documents, and through the existing authenticated URL in browsers.
const mapLanguageKey = "naver-qgis-map-language";
const mapLanguageStateKey = "naver-qgis-map-language-state";
let mapLanguage = "ko";
let mapLanguageState = null;
try {
  mapLanguage = window.localStorage.getItem(mapLanguageKey) === "en" ? "en" : "ko";
} catch (_error) { /* Session storage below can still carry the selected language. */ }
try {
  mapLanguageState = JSON.parse(window.sessionStorage.getItem(mapLanguageStateKey) || "null");
  window.sessionStorage.removeItem(mapLanguageStateKey);
  if (mapLanguageState && ["ko", "en"].includes(mapLanguageState.language)) {
    mapLanguage = mapLanguageState.language;
  }
} catch (_error) { /* A new viewer can still use the saved/default language. */ }

const mapLanguageButton = document.getElementById("map-language-toggle");
translateViewerUi();
function initializeMapLanguageButton() {
  mapLanguageButton.disabled = false;
  mapLanguageButton.textContent = mapLanguage === "en" ? "KR" : "EN";
  mapLanguageButton.setAttribute("aria-pressed", String(mapLanguage === "en"));
  mapLanguageButton.setAttribute("aria-label", mapLanguage === "en" ? uiText("한국어 지도로 전환") : uiText("영문 지도로 전환"));
}

mapLanguageButton.addEventListener("click", () => {
  if (!map || mapLanguageButton.disabled) return;
  if (routeBusy || localSearchRequests.size) {
    setStatus(uiText("검색이 끝난 뒤 지도 언어를 전환하세요."));
    return;
  }
  const external = Boolean(window.naverExternalBridge);
  if (!external && (!qgisBridge || typeof qgisBridge.reloadViewer !== "function")) {
    setStatus(uiText("QGIS 연결이 준비된 뒤 지도 언어를 전환하세요."));
    return;
  }
  const nextLanguage = mapLanguage === "ko" ? "en" : "ko";
  const center = map.getCenter();
  const state = {
    language: nextLanguage, center: {lat: center.lat(), lon: center.lng()},
    zoom: map.getZoom(), type: document.getElementById("map-type").value,
    street: document.getElementById("street-toggle").getAttribute("aria-pressed") === "true",
    marker: {lat: marker.getPosition().lat(), lon: marker.getPosition().lng()},
    roadview: roadview ? {position: currentRoadviewCoordinate() && {
      lat: currentRoadviewCoordinate().lat(), lon: currentRoadviewCoordinate().lng()
    }, pov: roadview.getPov()} : null,
    origin: routeOrigin, destination: routeDestination,
    waypoints: routeWaypoints.map(point => ({coordinate: point.coordinate, label: point.input.value})),
    inputs: Array.from(document.querySelectorAll("input[id], select[id]")).map(input =>
      ({id: input.id, value: input.value, checked: input.checked})),
    route: displayedRoutePayload, history: {items: routeHistory, selected_history_id: activeRouteHistoryId},
    collapsed: document.getElementById("explorer-body").hidden
  };
  try {
    // Do not discard the current view if storage is unavailable or full.
    window.sessionStorage.setItem(mapLanguageStateKey, JSON.stringify(state));
  } catch (_error) {
    setStatus(uiText("현재 화면을 보관하지 못해 언어 전환을 중단했습니다."));
    return;
  }
  try { window.localStorage.setItem(mapLanguageKey, nextLanguage); } catch (_error) { /* Session fallback above. */ }
  mapLanguageButton.disabled = true;
  if (external) window.location.reload();
  else qgisBridge.reloadViewer();
});

function restoreMapLanguageState() {
  const state = mapLanguageState;
  mapLanguageState = null;
  if (!state) return;
  bridgeSyncSuppressedUntil = Date.now() + 1500;
  routeOrigin = state.origin;
  routeDestination = state.destination;
  state.waypoints.forEach(point => {
    addWaypoint();
    const waypoint = routeWaypoints[routeWaypoints.length - 1];
    waypoint.coordinate = point.coordinate;
    waypoint.input.value = point.label;
  });
  state.inputs.forEach(input => {
    const element = document.getElementById(input.id);
    if (element) {
      element.value = input.value;
      if (typeof input.checked === "boolean") element.checked = input.checked;
    }
  });
  updateRouteAvoidSummary();
  updateRouteVehicleSummary();
  updateRouteControls();
  renderRouteHistory(state.history);
  if (state.route) renderRouteGuidance(state.route);
  document.getElementById("map-type").value = state.type;
  document.getElementById("map-type").dispatchEvent(new Event("change"));
  if (state.street) document.getElementById("street-toggle").click();
  if (state.collapsed) document.getElementById("explorer-toggle").click();
  applyViewerLayout(viewerLayoutSelect.value);
  map.setCenter(new naver.maps.LatLng(state.center.lat, state.center.lon));
  map.setZoom(state.zoom);
  marker.setPosition(new naver.maps.LatLng(state.marker.lat, state.marker.lon));
  if (state.roadview && state.roadview.position) {
    const position = state.roadview.position;
    roadview.setPosition(new naver.maps.LatLng(position.lat, position.lon));
    roadview.setPov(state.roadview.pov);
  }
  setStatus(mapLanguage === "en" ? uiText("영문 지도로 전환했습니다.") : uiText("한국어 지도로 전환했습니다."));
}
