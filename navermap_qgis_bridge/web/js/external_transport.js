// SPDX-License-Identifier: GPL-2.0-or-later
(() => {
  document.documentElement.classList.add("external-browser");

  const handlers = {
    routeStatusChanged: [],
    localSearchResultsChanged: [],
    routeGuidanceChanged: [],
    routeHistoryChanged: [],
    loadRouteHistoryInput: [],
    projectReset: []
  };
  const token = new URLSearchParams(window.location.hash.slice(1)).get("token") || "";
  const authHeaders = {"X-Bridge-Token": token};
  let cursorInitialized = false;
  let lastCenterSequence = -1;
  let lastEventSequence = 0;
  let projectEpoch = null;
  let accepting = false;
  let statePolling = false;
  let eventsPolling = false;

  function signal(name) {
    return {
      connect(callback) {
        if (typeof callback === "function") {
          handlers[name].push(callback);
        }
      }
    };
  }

  async function post(path, payload) {
    if (!accepting || projectEpoch === null) return;
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { ...authHeaders, "Content-Type": "application/json" },
        body: JSON.stringify({...payload, _epoch: projectEpoch})
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      console.warn("Naver QGIS external bridge request failed", path, error);
      if (path === "/api/request-route") {
        handlers.routeStatusChanged.forEach(callback => callback(false, "경로 요청을 전달하지 못했습니다. 연결을 확인하세요."));
      }
    }
  }

  async function pollState() {
    if (statePolling) return;
    statePolling = true;
    try {
      const response = await fetch("/api/state", { cache: "no-store", headers: authHeaders });
      if (!response.ok) {
        return;
      }
      const state = await response.json();
      if (!Number.isInteger(state.epoch)) return;
      const initialize = !cursorInitialized && Number.isInteger(state.sequence);
      if (initialize) {
        lastEventSequence = state.sequence;
        cursorInitialized = true;
      }
      const changed = projectEpoch !== null && projectEpoch !== state.epoch;
      projectEpoch = state.epoch;
      accepting = state.accepting === true;
      if (initialize || changed) window.naverExternalBridge.refreshRouteHistory();
      if (changed) {
        lastCenterSequence = -1;
        handlers.projectReset.forEach(callback => callback(projectEpoch));
      }
      if (
        state.center &&
        state.center.sequence !== lastCenterSequence &&
        typeof window.centerNaverMap === "function"
      ) {
        lastCenterSequence = state.center.sequence;
        if (typeof window.syncNaverView === "function" && Number.isFinite(state.center.meters_per_pixel)) {
          window.syncNaverView(state.center.lon, state.center.lat, state.center.meters_per_pixel, state.center.preserve_roadview);
        } else {
          window.centerNaverMap(state.center.lon, state.center.lat);
        }
      }
    } catch (error) {
      accepting = false;
      console.warn("Naver QGIS external bridge state polling failed", error);
    } finally {
      statePolling = false;
    }
  }

  async function pollEvents() {
    if (eventsPolling || !accepting) return;
    eventsPolling = true;
    try {
      const response = await fetch(`/api/events?since=${lastEventSequence}`, {
        cache: "no-store", headers: authHeaders
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      if (payload.epoch !== projectEpoch) return;
      if (payload.gap) {
        console.warn("Naver bridge event gap; refreshing history");
        lastEventSequence = Math.max(lastEventSequence, ...(payload.events || []).map(event => event.sequence));
        window.naverExternalBridge.refreshRouteHistory();
        return;
      }
      for (const event of payload.events || []) {
        if (event.epoch !== projectEpoch || event.sequence <= lastEventSequence) continue;
        lastEventSequence = Math.max(lastEventSequence, event.sequence || 0);
        for (const callback of handlers[event.signal] || []) {
          callback(...(event.args || []));
        }
      }
    } catch (error) {
      console.warn("Naver QGIS external bridge event polling failed", error);
    } finally {
      eventsPolling = false;
    }
  }

  window.naverExternalBridge = {
    projectReset: signal("projectReset"),
    cancelRoute() { post("/api/cancel-route", {}); },
    routeStatusChanged: signal("routeStatusChanged"),
    localSearchResultsChanged: signal("localSearchResultsChanged"),
    routeGuidanceChanged: signal("routeGuidanceChanged"),
    routeHistoryChanged: signal("routeHistoryChanged"),
    loadRouteHistoryInput: signal("loadRouteHistoryInput"),
    moveQgisCenter(lon, lat) {
      post("/api/move-center", { lon, lat });
    },
    zoomQgisView(lon, lat, meters_per_pixel) {
      post("/api/zoom-view", {lon, lat, meters_per_pixel});
    },
    updateRoadviewState(lon, lat, pan, tilt, zoom, pano_id) {
      post("/api/roadview-state", { lon, lat, pan, tilt, zoom, pano_id });
    },
    openNaverRoadview(lon, lat) {
      window.open(
        `https://map.naver.com/link/roadview/${lat.toFixed(8)},${lon.toFixed(8)}`,
        "_blank",
        "noopener"
      );
    },
    async toggleFullScreen() {
      const target = document.getElementById("viewer") || document.documentElement;
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else if (target.requestFullscreen) {
        await target.requestFullscreen();
      }
    },
    setRoutePoint(role, lon, lat) {
      post("/api/route-point", { role, lon, lat });
    },
    clearRoutePoint(role) {
      post("/api/clear-route-point", { role });
    },
    clearRoutePoints() {
      post("/api/clear-route-points", {});
    },
    selectRouteGuidance(sequence, lon, lat) {
      post("/api/select-route-guidance", { sequence, lon, lat });
    },
    selectRouteHistory(history_id) {
      post("/api/select-route-history", { history_id });
    },
    loadRouteHistory(history_id) {
      post("/api/load-route-history", { history_id });
    },
    deleteRouteHistory(history_id) {
      post("/api/delete-route-history", { history_id });
    },
    exportRouteHistory(history_id) {
      post("/api/export-route-history", { history_id });
    },
    refreshRouteHistory() {
      post("/api/refresh-route-history", {});
    },
    requestLocalSearch(request_id, query) {
      post("/api/request-local-search", { request_id, query });
    },
    requestRoute(
      origin_lon,
      origin_lat,
      destination_lon,
      destination_lat,
      priority,
      waypoints_json,
      avoid_json,
      vehicle_json,
      origin_label,
      destination_label
    ) {
      post("/api/request-route", {
        origin_lon,
        origin_lat,
        destination_lon,
        destination_lat,
        priority,
        waypoints_json,
        avoid_json,
        vehicle_json,
        origin_label,
        destination_label
      });
    }
  };

  setInterval(pollState, 400);
  setInterval(pollEvents, 400);
  pollState().then(pollEvents);
})();
