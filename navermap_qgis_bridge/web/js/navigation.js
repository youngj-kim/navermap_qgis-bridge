// SPDX-License-Identifier: GPL-2.0-or-later
    function moveViewer(lon, lat, options = {}) {
      const requestId = ++moveRequestId;
      const position = new naver.maps.LatLng(lat, lon);
      if (options.suppressBridge) {
        suppressBridgeSync();
      }
      map.setCenter(position);
      marker.setPosition(position);
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
      routeAvoidCheckboxes.forEach((checkbox) => {
        checkbox.checked = avoid.includes(checkbox.value);
      });
      updateRouteAvoidSummary();

      const vehicle = payload.vehicle || {};
      if (vehicle.car_type !== undefined) {
        routeCarType.value = String(vehicle.car_type);
      }
      if (vehicle.car_fuel) {
        routeCarFuel.value = vehicle.car_fuel;
      }
      routeCarHipass.checked = Boolean(vehicle.car_hipass);
      updateRouteVehicleSummary();

      updateRouteControls();
      if (routeOrigin) {
        moveViewer(routeOrigin.lon, routeOrigin.lat);
      }
      setStatus("선택한 이력을 경로 입력창으로 불러왔습니다.");
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
