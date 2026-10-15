// SPDX-License-Identifier: GPL-2.0-or-later
    function moveViewer(lon, lat, options = {}) {
      const requestId = ++moveRequestId;
      const position = new naver.maps.LatLng(lat, lon);
      if (options.suppressBridge) {
        suppressBridgeSync();
      }
      map.setCenter(position);
      marker.setPosition(position);
      mapViewSnapshot = {lon, lat, zoom: typeof map.getZoom === "function" ? map.getZoom() : null};
      if (requestId !== moveRequestId || !roadview) {
        return;
      }
      programmaticRoadviewPanoId = roadview.getPanoId
        ? roadview.getPanoId()
        : null;
      if (typeof roadview.setPosition === "function") {
        roadview.setPosition(position);
        setStatus(`EPSG:4326 ${lat.toFixed(6)}, ${lon.toFixed(6)} - Street View requested.`);
      }
    }

    window.syncNaverView = function syncNaverView(lon, lat, metersPerPixel, preserveRoadview = false) {
      if (![lon, lat, metersPerPixel].every(Number.isFinite) || metersPerPixel <= 0 || Math.abs(lon) > 180 || Math.abs(lat) > 90) return;
      if (!map || !roadview) {
        pendingView = {lon, lat, metersPerPixel, preserveRoadview};
        return;
      }
      suppressBridgeSync();
      if (preserveRoadview) {
        map.setCenter(new naver.maps.LatLng(lat, lon));
      } else {
        moveViewer(lon, lat, {suppressBridge:true});
      }
      try {
        const target = Math.round(map.getZoom() + Math.log2(naverGroundResolution() / metersPerPixel));
        const minimum = map.getOptions("minZoom");
        const maximum = map.getOptions("maxZoom");
        const min = minimum == null ? 0 : Number(minimum);
        const max = maximum == null ? 21 : Number(maximum);
        const zoom = Math.max(Number.isFinite(min) ? min : 0, Math.min(Number.isFinite(max) ? max : 21, target));
        if (zoom !== map.getZoom()) map.setZoom(zoom, false);
      } catch (_error) { setStatus("지도 확대 비율을 맞추지 못했습니다."); }
      mapViewSnapshot = {lon, lat, zoom: map.getZoom()};
    };

    window.centerNaverMap = function centerNaverMap(lon, lat) {
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) {
        setStatus("Invalid coordinate received from QGIS.");
        return;
      }

      if (!map || !roadview) {
        pendingCenter = { lon, lat };
        setStatus(`Queued EPSG:4326 ${lat.toFixed(6)}, ${lon.toFixed(6)} until Naver API is ready.`);
        return;
      }

      moveViewer(lon, lat, { suppressBridge: true });
    };

    window.loadRouteHistoryInput = function loadRouteHistoryInput(payload) {
      clearRouteInputs(false);

      const origin = payload.origin || {};
      const destination = payload.destination || {};
      routeOriginInput.value = routeInputLabel(origin, "출발지");
      routeDestinationInput.value = routeInputLabel(destination, "도착지");
      routeOrigin = applyLoadedRoutePoint("origin", origin);
      routeDestination = applyLoadedRoutePoint("destination", destination);

      const waypoints = Array.isArray(payload.waypoints)
        ? payload.waypoints.slice(0, maxRouteWaypoints)
        : [];
      waypoints.forEach((waypointPayload) => {
        addWaypoint();
        const waypoint = routeWaypoints[routeWaypoints.length - 1];
        waypoint.input.value = routeInputLabel(
          waypointPayload,
          `경유지 ${routeWaypoints.length}`
        );
        waypoint.coordinate = applyLoadedRoutePoint(
          waypointPointId(waypoint),
          waypointPayload
        );
      });

      if (payload.priority && routePrioritySelect.querySelector(`option[value="${payload.priority}"]`)) {
        routePrioritySelect.value = payload.priority;
      }

      const avoid = Array.isArray(payload.avoid) ? payload.avoid : [];
      // Old histories may contain both choices; the old request used toll first.
      const effectiveAvoid = avoid.includes("toll") ? "toll" : avoid.includes("motorway") ? "motorway" : null;
      routeAvoidCheckboxes.forEach((checkbox) => {
        checkbox.checked = checkbox.value === effectiveAvoid;
      });
      updateRouteAvoidSummary();

      const vehicle = payload.vehicle || {};
      if (vehicle.car_type !== undefined) {
        routeCarType.value = String(vehicle.car_type);
        if (!routeCarType.value) routeCarType.value = "1";
      }
      if (vehicle.car_fuel) {
        routeCarFuel.value = String(vehicle.car_fuel).toLowerCase();
        if (!routeCarFuel.value) routeCarFuel.value = "gasoline";
      }
      routeCarHipass.checked = Boolean(vehicle.car_hipass);
      updateRouteVehicleSummary();

      updateRouteControls();
      if (routeOrigin) {
        moveViewer(routeOrigin.lon, routeOrigin.lat);
      }
      setStatus(avoid.length > 1
        ? "이전 이력의 복수 회피 설정은 당시 요청에 적용된 무료 우선으로 불러왔습니다."
        : "선택한 이력을 경로 입력창으로 불러왔습니다.");
    };

    updateRouteVehicleSummary();
    applyViewerSplit(savedViewerSplit());
    applyViewerLayout(savedViewerLayout());
    initQgisBridge();

    if (!naverAppKey) {
      setStatus("Set NAVER_MAP_CLIENT_ID or navermap_qgis_bridge/settings.json before loading the viewer.");
    } else {
      loadNaverScript(naverAppKey)
        .then(initViewer)
        .catch((error) => setStatus(error.message));
    }
