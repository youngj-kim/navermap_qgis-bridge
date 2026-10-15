// SPDX-License-Identifier: GPL-2.0-or-later
    function currentMapCoordinate() {
      if (!map) {
        return null;
      }
      const center = map.getCenter();
      return {
        lon: center.lng(),
        lat: center.lat()
      };
    }

    function parseCoordinateInput(value) {
      const separator = value.includes(",") ? /\s*,\s*/ : /\s+/;
      const parts = value.trim().split(separator);
      if (parts.length !== 2 || parts.some((part) => !part)) {
        return null;
      }

      const first = Number(parts[0]);
      const second = Number(parts[1]);
      if (!Number.isFinite(first) || !Number.isFinite(second)) {
        return null;
      }

      let lon = first;
      let lat = second;
      if (Math.abs(second) > 90 && Math.abs(first) <= 90) {
        lon = second;
        lat = first;
      }

      if (Math.abs(lon) > 180 || Math.abs(lat) > 90) {
        return null;
      }
      return { lon, lat };
    }

    function formatCoordinate(coordinate) {
      return `${coordinate.lon.toFixed(7)}, ${coordinate.lat.toFixed(7)}`;
    }

    function resolveRouteLocation(value) {
      const query = value.trim();
      const coordinate = parseCoordinateInput(query);
      if (coordinate) {
        return Promise.resolve(coordinate);
      }
      if (!query) {
        return Promise.reject(new Error("입력값을 좌표나 장소로 해석할 수 없습니다."));
      }

      return geocodeAddress(query).then((results) => {
        if (!results.length) {
          throw new Error(`위치를 찾지 못했습니다: ${query}`);
        }
        return results[0];
      });
    }

    function updateRouteControls() {
      routeCancelButton.disabled = !routeBusy;
      const hasOrigin = Boolean(routeOriginInput.value.trim());
      const hasDestination = Boolean(routeDestinationInput.value.trim());
      const waypointsReady = routeWaypoints.every((waypoint) => waypoint.input.value.trim());
      routeCreateButton.disabled = routeBusy || !(hasOrigin && hasDestination && waypointsReady);
      routeHistoryOpenButton.disabled = routeBusy || !qgisBridge;
      routeResetButton.disabled = routeBusy || !(hasOrigin || hasDestination || routeWaypoints.length);
      routeSwapButton.disabled = !map || routeBusy || !(hasOrigin || hasDestination);
      routePrioritySelect.disabled = !map || routeBusy || selectedRouteAvoidOptions().length > 0;
      routeAvoidToggle.disabled = !map || routeBusy;
      routeAvoidCheckboxes.forEach((checkbox) => {
        checkbox.disabled = !map || routeBusy;
      });
      routeVehicleToggle.disabled = !map || routeBusy;
      routeCarType.disabled = !map || routeBusy;
      routeCarFuel.disabled = !map || routeBusy;
      routeCarHipass.disabled = true;
      routeAddWaypointButton.disabled = !map || routeBusy || routeWaypoints.length >= maxRouteWaypoints;
      routeOriginInput.disabled = !map || routeBusy;
      routeDestinationInput.disabled = !map || routeBusy;
      routeOriginCurrentButton.disabled = !map || routeBusy;
      routeDestinationCurrentButton.disabled = !map || routeBusy;
      routeWaypoints.forEach((waypoint, index) => {
        waypoint.input.disabled = !map || routeBusy;
        waypoint.currentButton.disabled = !map || routeBusy;
        waypoint.removeButton.disabled = routeBusy;
        waypoint.upButton.disabled = routeBusy || index === 0;
        waypoint.downButton.disabled = routeBusy || index === routeWaypoints.length - 1;
      });
    }

    function publishRoutePoint(role, coordinate) {
      if (qgisBridge && coordinate) {
        qgisBridge.setRoutePoint(role, coordinate.lon, coordinate.lat);
      }
    }

    function applyRouteSearchResult(
      input,
      pointId,
      label,
      coordinate,
      displayValue,
      onResolved
    ) {
      input.value = displayValue || formatCoordinate(coordinate);
      onResolved(coordinate);
      publishRoutePoint(pointId, coordinate);
      searchResults.hidden = true;

      if (map) {
        map.setZoom(16);
        moveViewer(coordinate.lon, coordinate.lat, { suppressBridge: true });
      }
      if (qgisBridge) {
        qgisBridge.moveQgisCenter(coordinate.lon, coordinate.lat);
      }
      setStatus(
        `${label} 지정: ${coordinate.lat.toFixed(6)}, ${coordinate.lon.toFixed(6)}`
      );
      updateRouteControls();
    }

    function searchRouteInput(
      input,
      pointIdProvider,
      labelProvider,
      onResolved,
      selectFirst = false
    ) {
      const query = input.value.trim();
      if (!query) {
        return;
      }

      const pointId = pointIdProvider();
      const label = labelProvider();
      const coordinate = parseCoordinateInput(query);
      if (coordinate) {
        applyRouteSearchResult(
          input,
          pointId,
          label,
          coordinate,
          formatCoordinate(coordinate),
          onResolved
        );
        return;
      }

      searchLocal(
        query,
        (result) => {
          applyRouteSearchResult(
            input,
            pointId,
            label,
            { lon: result.lon, lat: result.lat },
            result.title || result.address,
            onResolved
          );
        },
        false,
        selectFirst
      );
    }

    function bindRouteInput(input, pointIdProvider, labelProvider, onResolved) {
      input.addEventListener("input", () => {
        onResolved(null);
        searchRequestId += 1;
        searchResults.hidden = true;
        if (qgisBridge) {
          qgisBridge.clearRoutePoint(pointIdProvider());
        }
        updateRouteControls();

        window.clearTimeout(routeSearchTimer);
        if (!input.value.trim()) {
          return;
        }
        routeSearchTimer = window.setTimeout(() => {
          searchRouteInput(input, pointIdProvider, labelProvider, onResolved);
        }, 500);
      });

      input.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
          return;
        }
        event.preventDefault();
        window.clearTimeout(routeSearchTimer);
        searchRouteInput(
          input,
          pointIdProvider,
          labelProvider,
          onResolved,
          true
        );
      });
    }

    function waypointPointId(waypoint) {
      return `waypoint:${waypoint.id}`;
    }

    function updateWaypointLabels() {
      routeWaypoints.forEach((waypoint, index) => {
        waypoint.label.textContent = `경유 ${index + 1}`;
        waypoint.input.setAttribute("aria-label", `경유지 ${index + 1}`);
        waypoint.currentButton.title = `현재 지도 중심을 경유지 ${index + 1}로 사용`;
        waypoint.removeButton.title = `경유지 ${index + 1} 삭제`;
        waypoint.removeButton.setAttribute("aria-label", `경유지 ${index + 1} 삭제`);
        waypoint.upButton.title = `경유지 ${index + 1} 위로 이동`;
        waypoint.upButton.setAttribute("aria-label", `경유지 ${index + 1} 위로 이동`);
        waypoint.downButton.title = `경유지 ${index + 1} 아래로 이동`;
        waypoint.downButton.setAttribute("aria-label", `경유지 ${index + 1} 아래로 이동`);
      });
    }

    function moveWaypoint(waypoint, offset) {
      const index = routeWaypoints.indexOf(waypoint);
      const targetIndex = index + offset;
      if (index < 0 || targetIndex < 0 || targetIndex >= routeWaypoints.length) {
        return;
      }

      window.clearTimeout(routeSearchTimer);
      searchRequestId += 1;
      searchResults.hidden = true;
      routeWaypoints.splice(index, 1);
      routeWaypoints.splice(targetIndex, 0, waypoint);
      routeWaypointsContainer.replaceChildren(
        ...routeWaypoints.map((candidate) => candidate.row)
      );
      updateWaypointLabels();
      updateRouteControls();
      setStatus(`경유지 ${targetIndex + 1} 순서로 이동했습니다.`);
    }

    function swapRouteEndpoints() {
      window.clearTimeout(routeSearchTimer);
      searchRequestId += 1;
      searchResults.hidden = true;

      const originValue = routeOriginInput.value;
      routeOriginInput.value = routeDestinationInput.value;
      routeDestinationInput.value = originValue;
      [routeOrigin, routeDestination] = [routeDestination, routeOrigin];

      if (qgisBridge) {
        qgisBridge.clearRoutePoint("origin");
        qgisBridge.clearRoutePoint("destination");
        publishRoutePoint("origin", routeOrigin);
        publishRoutePoint("destination", routeDestination);
      }
      updateRouteControls();
      setStatus("출발지와 도착지를 바꿨습니다.");
    }

    function removeWaypoint(waypoint) {
      const index = routeWaypoints.indexOf(waypoint);
      if (index < 0) {
        return;
      }
      window.clearTimeout(routeSearchTimer);
      searchRequestId += 1;
      searchResults.hidden = true;
      if (qgisBridge) {
        qgisBridge.clearRoutePoint(waypointPointId(waypoint));
      }
      routeWaypoints.splice(index, 1);
      waypoint.row.remove();
      updateWaypointLabels();
      updateRouteControls();
      setStatus("경유지를 삭제했습니다.");
    }

    function addWaypoint() {
      if (routeWaypoints.length >= maxRouteWaypoints) {
        setStatus(`경유지는 최대 ${maxRouteWaypoints}개까지 추가할 수 있습니다.`);
        return;
      }

      const row = document.createElement("div");
      row.className = "route-waypoint";

      const label = document.createElement("span");
      label.className = "route-label";

      const input = document.createElement("input");
      input.className = "route-input";
      input.type = "text";
        input.placeholder = "장소, 주소 또는 경도,위도";
      input.autocomplete = "off";

      const currentButton = document.createElement("button");
      currentButton.className = "route-current";
      currentButton.type = "button";
      currentButton.textContent = "현재 위치";

      const removeButton = document.createElement("button");
      removeButton.className = "route-waypoint-remove";
      removeButton.type = "button";
      removeButton.textContent = "×";

      const orderContainer = document.createElement("span");
      orderContainer.className = "route-waypoint-order";

      const upButton = document.createElement("button");
      upButton.type = "button";
      upButton.textContent = "↑";

      const downButton = document.createElement("button");
      downButton.type = "button";
      downButton.textContent = "↓";

      const waypoint = {
        id: nextWaypointId++,
        coordinate: null,
        row,
        label,
        input,
        currentButton,
        removeButton,
        upButton,
        downButton
      };

      bindRouteInput(
        input,
        () => waypointPointId(waypoint),
        () => `경유지 ${routeWaypoints.indexOf(waypoint) + 1}`,
        (coordinate) => {
          waypoint.coordinate = coordinate;
        }
      );

      currentButton.addEventListener("click", () => {
        window.clearTimeout(routeSearchTimer);
        searchRequestId += 1;
        searchResults.hidden = true;
        waypoint.coordinate = currentMapCoordinate();
        if (waypoint.coordinate) {
          input.value = formatCoordinate(waypoint.coordinate);
          publishRoutePoint(waypointPointId(waypoint), waypoint.coordinate);
          const index = routeWaypoints.indexOf(waypoint) + 1;
          setStatus(
            `경유지 ${index}: ${waypoint.coordinate.lat.toFixed(6)}, ` +
            waypoint.coordinate.lon.toFixed(6)
          );
        }
        updateRouteControls();
      });

      removeButton.addEventListener("click", () => removeWaypoint(waypoint));
      upButton.addEventListener("click", () => moveWaypoint(waypoint, -1));
      downButton.addEventListener("click", () => moveWaypoint(waypoint, 1));
      orderContainer.append(upButton, downButton);

      row.append(label, input, currentButton, orderContainer, removeButton);
      routeWaypoints.push(waypoint);
      routeWaypointsContainer.appendChild(row);
      updateWaypointLabels();
      updateRouteControls();
      input.focus();
      setStatus(`${routeWaypoints.length}번째 경유지를 추가했습니다.`);
    }

    function clearRouteInputs(resetOptions = true) {
      routeGeneration += 1;
      routeBusy = false;
      window.clearTimeout(routeWatchdog);
      window.clearTimeout(routeSearchTimer);
      searchRequestId += 1;
      searchResults.hidden = true;
      routeOrigin = null;
      routeDestination = null;
      routeOriginInput.value = "";
      routeDestinationInput.value = "";
      routeWaypoints.forEach((waypoint) => waypoint.row.remove());
      routeWaypoints.length = 0;
      nextWaypointId = 1;

      if (resetOptions) {
        routePrioritySelect.value = "RECOMMEND";
        routeAvoidCheckboxes.forEach((checkbox) => {
          checkbox.checked = false;
        });
        routeCarType.value = "1";
        routeCarFuel.value = "gasoline";
        routeCarHipass.checked = false;
      }

      routeAvoidOptions.hidden = true;
      routeAvoidToggle.setAttribute("aria-expanded", "false");
      updateRouteAvoidSummary();
      routeVehicleOptions.hidden = true;
      routeVehicleToggle.setAttribute("aria-expanded", "false");
      updateRouteVehicleSummary();
      if (qgisBridge) {
        qgisBridge.clearRoutePoints();
      }
      updateRouteControls();
    }

    function routeInputLabel(location, fallback) {
      const label = location && location.label ? String(location.label).trim() : "";
      if (label) {
        return label;
      }
      if (
        location &&
        Number.isFinite(Number(location.lon)) &&
        Number.isFinite(Number(location.lat))
      ) {
        return formatCoordinate({
          lon: Number(location.lon),
          lat: Number(location.lat)
        });
      }
      return fallback;
    }

    function applyLoadedRoutePoint(pointId, location) {
      const coordinate = {
        lon: Number(location.lon),
        lat: Number(location.lat)
      };
      if (!Number.isFinite(coordinate.lon) || !Number.isFinite(coordinate.lat)) {
        return null;
      }
      publishRoutePoint(pointId, coordinate);
      return coordinate;
    }
