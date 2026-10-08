// SPDX-License-Identifier: GPL-2.0-or-later
(() => {
  document.documentElement.classList.add("external-browser");

  const handlers = {
    routeStatusChanged: [],
    localSearchResultsChanged: [],
    routeGuidanceChanged: [],
    routeHistoryChanged: [],
    loadRouteHistoryInput: []
  };
  let lastCenterSequence = -1;
  let lastEventSequence = 0;

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
    try {
      await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload || {})
      });
    } catch (error) {
      console.warn("Naver QGIS external bridge request failed", path, error);
    }
  }

  async function pollState() {
    try {
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) {
        return;
      }
      const state = await response.json();
      if (
        state.center &&
        state.center.sequence !== lastCenterSequence &&
        typeof window.centerNaverMap === "function"
      ) {
        lastCenterSequence = state.center.sequence;
        window.centerNaverMap(state.center.lon, state.center.lat);
      }
    } catch (error) {
      console.warn("Naver QGIS external bridge state polling failed", error);
    }
  }

  async function pollEvents() {
    try {
      const response = await fetch(`/api/events?since=${lastEventSequence}`, {
        cache: "no-store"
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      for (const event of payload.events || []) {
        lastEventSequence = Math.max(lastEventSequence, event.sequence || 0);
        for (const callback of handlers[event.signal] || []) {
          callback(...(event.args || []));
        }
      }
    } catch (error) {
      console.warn("Naver QGIS external bridge event polling failed", error);
    }
  }

  window.naverExternalBridge = {
    routeStatusChanged: signal("routeStatusChanged"),
    localSearchResultsChanged: signal("localSearchResultsChanged"),
    routeGuidanceChanged: signal("routeGuidanceChanged"),
    routeHistoryChanged: signal("routeHistoryChanged"),
    loadRouteHistoryInput: signal("loadRouteHistoryInput"),
    moveQgisCenter(lon, lat) {
      post("/api/move-center", { lon, lat });
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
  pollState();
  pollEvents();
})();
