// SPDX-License-Identifier: GPL-2.0-or-later
    const viewerOptions = createNaverViewerOptions({
      getMap: () => map, getMaps: () => naver.maps,
      relayout: scheduleStableRelayout, onError: setStatus,
      onExplorerCollapse: () => {
        if (!routePanelOpened) {
          renderRouteHistory({items: routeHistory, selected_history_id: activeRouteHistoryId});
          activateRoutePanelTab("history");
        }
      }
    });

    function loadNaverScript(appKey) {
      return new Promise((resolve, reject) => {
        if (
          window.naver &&
          window.naver.maps &&
          window.naver.maps.Panorama &&
          window.naver.maps.Service
        ) {
          resolve();
          return;
        }

        const callbackName = `initNaverQgisBridge${Date.now()}`;
        const script = document.createElement("script");
        window[callbackName] = () => {
          delete window[callbackName];
          resolve();
        };
        script.src =
          "https://oapi.map.naver.com/openapi/v3/maps.js" +
          `?ncpKeyId=${encodeURIComponent(appKey)}` +
          "&submodules=panorama,geocoder" +
          `&language=${mapLanguage}` +
          `&callback=${encodeURIComponent(callbackName)}`;
        script.async = true;
        script.onerror = () => {
          delete window[callbackName];
          reject(new Error("Failed to load Naver Maps JavaScript API."));
        };
        document.head.appendChild(script);
      });
    }

    function initViewer() {
      const center = new naver.maps.LatLng(defaultCenter.lat, defaultCenter.lon);
      const mapElement = document.getElementById("map");
      const roadviewElement = document.getElementById("roadview");

      map = new naver.maps.Map(document.getElementById("map-surface"), {
        center,
        zoom: 16,
        size: elementSize(mapElement)
      });

      marker = new naver.maps.Marker({
        map,
        position: center
      });
      viewerOptions.initialize();

      naver.maps.Event.addListener(map, "drag", () => {
        mapDragActive = true;
        bridgeSyncSuppressedUntil = 0;
        scheduleNaverMapSync();
      });

      naver.maps.Event.addListener(map, "center_changed", () => {
        scheduleNaverMapSync();
      });

      naver.maps.Event.addListener(map, "zoom_changed", () => {
        scheduleNaverMapSync();
      });

      naver.maps.Event.addListener(map, "dragend", () => {
        window.setReverseSyncDiagnostic(uiText("NAVER dragend 감지"));
        window.clearTimeout(mapSyncTimer);
        mapSyncTimer = null;
        const wasDragging = mapDragActive;
        mapDragActive = false;
        syncNaverMapToQgis(true, wasDragging);
      });

      mapElement.addEventListener("pointerdown", () => {
        mapPointerActive = true;
        window.setReverseSyncDiagnostic(uiText("지도 pointerdown 감지"));
      }, true);
      document.addEventListener("pointerup", () => {
        if (!mapPointerActive) {
          return;
        }
        mapPointerActive = false;
        const wasDragging = mapDragActive;
        mapDragActive = false;
        window.setReverseSyncDiagnostic(uiText("지도 pointerup 감지"));
        window.clearTimeout(mapSyncTimer);
        mapSyncTimer = null;
        window.setTimeout(() => syncNaverMapToQgis(true, wasDragging), 0);
      }, true);
      document.addEventListener("pointercancel", () => {
        mapPointerActive = false;
        mapDragActive = false;
      }, true);

      naver.maps.Event.addListener(map, "idle", () => {
        window.clearTimeout(mapSyncTimer);
        mapSyncTimer = null;
        syncNaverMapToQgis();
      });

      naver.maps.Event.addListener(map, "click", () => {
        searchResults.hidden = true;
      });

      roadview = new naver.maps.Panorama("roadview-surface", {
        position: center,
        size: elementSize(roadviewElement),
        pov: {
          pan: 0,
          tilt: 0,
          fov: 100
        }
      });
      geocoderService = naver.maps.Service;
      searchQuery.disabled = false;
      searchSubmit.disabled = false;
      routeOriginInput.disabled = false;
      routeDestinationInput.disabled = false;
      routeOriginCurrentButton.disabled = false;
      routeDestinationCurrentButton.disabled = false;
      routePrioritySelect.disabled = false;
      routeAddWaypointButton.disabled = false;
      updateRouteControls();
      document.getElementById("open-history").disabled = false;

      naver.maps.Event.addListener(roadview, "pano_changed", () => {
        updateRoadviewPhotoDate();
        scheduleRoadviewStateSync();

        if (isBridgeSyncSuppressed()) {
          return;
        }

        const panoId = roadview.getPanoId();
        if (programmaticRoadviewPanoId === panoId) {
          programmaticRoadviewPanoId = null;
          return;
        }
        programmaticRoadviewPanoId = null;

        const position = currentRoadviewCoordinate();
        if (!position) {
          return;
        }

        const lat = position.lat();
        const lon = position.lng();
        map.setCenter(position);
        marker.setPosition(position);

        window.clearTimeout(roadviewSyncTimer);
        roadviewSyncTimer = window.setTimeout(() => {
          if (!qgisBridge) {
            setStatus("Roadview moved, but the QGIS bridge is not ready.");
            return;
          }

          qgisBridge.moveQgisCenter(lon, lat);
          setStatus(`Roadview -> QGIS EPSG:4326 ${lat.toFixed(6)}, ${lon.toFixed(6)}.`);
        }, 200);
      });

      naver.maps.Event.addListener(roadview, "pov_changed", () => {
        scheduleRoadviewStateSync();
      });

      naver.maps.Event.addListener(roadview, "init", () => {
        updateRoadviewPhotoDate();
        scheduleStableRelayout();
        scheduleRoadviewStateSync();
      });

      setStatus("Ready. QGIS, Naver Map, and Street View position sync is active.");
      moveViewer(defaultCenter.lon, defaultCenter.lat, { suppressBridge: true });
      scheduleStableRelayout();

      if (pendingCenter) {
        moveViewer(pendingCenter.lon, pendingCenter.lat);
        pendingCenter = null;
      }
      if (pendingView) {
        const view = pendingView;
        pendingView = null;
        window.syncNaverView(view.lon, view.lat, view.metersPerPixel, view.preserveRoadview);
      }
      restoreMapLanguageState();
      initializeMapLanguageButton();
    }

    viewerLayoutSelect.addEventListener("change", () => {
      applyViewerLayout(viewerLayoutSelect.value);
    });

    fullscreenToggle.addEventListener("click", async () => {
      if (qgisBridge && typeof qgisBridge.toggleFullScreen === "function") {
        await qgisBridge.toggleFullScreen();
        scheduleStableRelayout();
        return;
      }

      try {
        await toggleBrowserFullScreen();
      } catch (_error) {
        setStatus(uiText("전체화면 전환을 사용할 수 없습니다."));
      }
    });

    document.addEventListener("fullscreenchange", () => {
      fullscreenToggle.textContent = document.fullscreenElement ? "⛶" : "⛶";
      scheduleStableRelayout();
    });

    splitToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      applyViewerLayout(swappedViewerLayout());
    });

    viewSplitter.addEventListener("pointerdown", (event) => {
      if (event.target === splitToggle) {
        return;
      }
      event.preventDefault();
      viewSplitter.setPointerCapture(event.pointerId);

      const updateSplitFromPointer = (pointerEvent) => {
        const rect = viewer.getBoundingClientRect();
        const horizontal = isHorizontalSplitLayout();
        const headerHeight = searchForm.closest("header").offsetHeight;
        const footerHeight = document.getElementById("status-bar").offsetHeight;
        const available = horizontal
          ? Math.max(1, rect.height - headerHeight - footerHeight)
          : Math.max(1, rect.width);
        const offset = horizontal
          ? pointerEvent.clientY - rect.top - headerHeight
          : pointerEvent.clientX - rect.left;
        applyViewerSplit((offset / available) * 100);
      };

      const stopDrag = (pointerEvent) => {
        viewSplitter.releasePointerCapture(pointerEvent.pointerId);
        viewSplitter.removeEventListener("pointermove", updateSplitFromPointer);
        viewSplitter.removeEventListener("pointerup", stopDrag);
        viewSplitter.removeEventListener("pointercancel", stopDrag);
        scheduleStableRelayout();
      };

      viewSplitter.addEventListener("pointermove", updateSplitFromPointer);
      viewSplitter.addEventListener("pointerup", stopDrag);
      viewSplitter.addEventListener("pointercancel", stopDrag);
      updateSplitFromPointer(event);
    });

    window.addEventListener("resize", () => {
      updateSplitterState();
      scheduleStableRelayout();
    });

    window.addEventListener("focus", scheduleStableRelayout);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        scheduleStableRelayout();
      }
    });
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", scheduleStableRelayout);
      window.visualViewport.addEventListener("scroll", scheduleStableRelayout);
    }

    if (window.ResizeObserver) {
      const viewerResizeObserver = new ResizeObserver(() => {
        updateSplitterState();
        scheduleStableRelayout();
      });
      [
        viewer,
        document.getElementById("search-panel"),
        document.getElementById("map"),
        document.getElementById("roadview")
      ].forEach((element) => {
        if (element) {
          viewerResizeObserver.observe(element);
        }
      });
    }

    document.getElementById("open-history").addEventListener("click", () => {
      const position = currentRoadviewCoordinate() || (map && map.getCenter());
      if (!position || !qgisBridge) {
        setStatus("The Naver Street View link is not ready.");
        return;
      }

      qgisBridge.openNaverRoadview(position.lng(), position.lat());
    });

    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const query = searchQuery.value.trim();
      if (!query) {
        searchQuery.focus();
        return;
      }
      searchLocal(query);
    });

    searchQuery.addEventListener("input", () => {
      searchClear.disabled = !searchQuery.value;
    });

    searchQuery.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        searchResults.hidden = true;
      }
    });

    searchClear.addEventListener("click", () => {
      searchRequestId += 1;
      searchQuery.value = "";
      searchResults.textContent = "";
      searchResults.hidden = true;
      searchClear.disabled = true;
      searchSubmit.disabled = false;
      searchQuery.focus();
    });

    routeGuidanceToggle.addEventListener("click", () => {
      const collapsed = routeGuidancePanel.dataset.collapsed === "true";
      routeGuidancePanel.dataset.collapsed = collapsed ? "false" : "true";
      routeGuidanceToggle.textContent = collapsed ? "−" : "+";
      const label = collapsed ? uiText("경로 안내 접기") : uiText("경로 안내 펼치기");
      routeGuidanceToggle.title = label;
      routeGuidanceToggle.setAttribute("aria-label", label);
    });

    routeGuidanceTab.addEventListener("click", () => {
      activateRoutePanelTab("guidance");
    });

    routeHistoryTab.addEventListener("click", () => {
      activateRoutePanelTab("history");
    });

    routeHistoryOpenButton.addEventListener("click", () => {
      if (qgisBridge && qgisBridge.refreshRouteHistory) {
        qgisBridge.refreshRouteHistory();
      }
      routeGuidancePanel.dataset.collapsed = "false";
      routeGuidanceToggle.textContent = "−";
      routeGuidanceToggle.title = uiText("경로 안내 접기");
      routeGuidanceToggle.setAttribute("aria-label", uiText("경로 안내 접기"));
      activateRoutePanelTab("history");
      routeGuidancePanel.scrollIntoView({ block: "nearest" });
      setStatus(routeHistory.length ? uiText("경로 이력을 열었습니다.") : uiText("경로 이력을 확인하고 있습니다."));
    });

    routeAddWaypointButton.addEventListener("click", addWaypoint);

    routePrioritySelect.addEventListener("change", () => {
      const label = routePrioritySelect.options[routePrioritySelect.selectedIndex].text;
      setStatus(uiText`경로 유형: ${label}`);
    });

    routeAvoidToggle.addEventListener("click", () => {
      const opening = routeAvoidOptions.hidden;
      routeAvoidOptions.hidden = !opening;
      routeAvoidToggle.setAttribute("aria-expanded", opening ? "true" : "false");
      if (opening) {
        routeVehicleOptions.hidden = true;
        routeVehicleToggle.setAttribute("aria-expanded", "false");
      }
    });

    routeAvoidCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          routeAvoidCheckboxes.forEach((other) => {
            if (other !== checkbox) other.checked = false;
          });
        }
        updateRouteAvoidSummary();
        updateRouteControls();
        const count = selectedRouteAvoidOptions().length;
        setStatus(count ? uiText`경로 회피 옵션 ${count}개 선택` : uiText("경로 회피 옵션 없음"));
      });
    });

    routeVehicleToggle.addEventListener("click", () => {
      const opening = routeVehicleOptions.hidden;
      routeVehicleOptions.hidden = !opening;
      routeVehicleToggle.setAttribute("aria-expanded", opening ? "true" : "false");
      if (opening) {
        routeAvoidOptions.hidden = true;
        routeAvoidToggle.setAttribute("aria-expanded", "false");
      }
    });

    [routeCarType, routeCarFuel, routeCarHipass].forEach((control) => {
      control.addEventListener("change", () => {
        updateRouteVehicleSummary();
        setStatus(routeVehicleToggle.title);
      });
    });

    routeSwapButton.addEventListener("click", swapRouteEndpoints);

    bindRouteInput(
      routeOriginInput,
      () => "origin",
      () => uiText("출발지"),
      (coordinate) => {
        routeOrigin = coordinate;
      }
    );

    bindRouteInput(
      routeDestinationInput,
      () => "destination",
      () => uiText("도착지"),
      (coordinate) => {
        routeDestination = coordinate;
      }
    );

    window.setRoutePointFromCurrent = function setRoutePointFromCurrent(role) {
      window.clearTimeout(routeSearchTimer);
      searchRequestId += 1;
      searchResults.hidden = true;
      const coordinate = currentMapCoordinate();
      if (!coordinate) {
        setStatus(uiText("현재 NAVER 지도 중심을 읽지 못했습니다."));
        return;
      }
      if (role === "origin") {
        routeOrigin = coordinate;
        routeOriginInput.value = formatCoordinate(coordinate);
        publishRoutePoint("origin", coordinate);
        setStatus(uiText`출발지: ${coordinate.lat.toFixed(6)}, ${coordinate.lon.toFixed(6)}`);
      } else if (role === "destination") {
        routeDestination = coordinate;
        routeDestinationInput.value = formatCoordinate(coordinate);
        publishRoutePoint("destination", coordinate);
        setStatus(uiText`도착지: ${coordinate.lat.toFixed(6)}, ${coordinate.lon.toFixed(6)}`);
      }
      updateRouteControls();
    };

    routeCreateButton.addEventListener("click", async () => {
      if (!qgisBridge) {
        setStatus("QGIS route bridge is not ready.");
        return;
      }

      window.clearTimeout(routeSearchTimer);
      searchRequestId += 1;
      searchResults.hidden = true;
      routeAvoidOptions.hidden = true;
      routeAvoidToggle.setAttribute("aria-expanded", "false");
      routeVehicleOptions.hidden = true;
      routeVehicleToggle.setAttribute("aria-expanded", "false");
      routeBusy = true;
      const generation = ++routeGeneration;
      updateRouteControls();
      setStatus(uiText("출발지, 경유지, 도착지를 확인하고 있습니다..."));

      try {
        const locations = await Promise.all([
          routeOrigin || resolveRouteLocation(routeOriginInput.value),
          ...routeWaypoints.map((waypoint) => (
            waypoint.coordinate || resolveRouteLocation(waypoint.input.value)
          )),
          routeDestination || resolveRouteLocation(routeDestinationInput.value)
        ]);
        if (generation !== routeGeneration) return;
        routeOrigin = locations[0];
        routeDestination = locations[locations.length - 1];
        routeWaypoints.forEach((waypoint, index) => {
          waypoint.coordinate = locations[index + 1];
        });
      } catch (error) {
        if (generation !== routeGeneration) return;
        routeBusy = false;
        setStatus(error.message);
        updateRouteControls();
        return;
      }

      publishRoutePoint("origin", routeOrigin);
      publishRoutePoint("destination", routeDestination);
      routeWaypoints.forEach((waypoint) => {
        publishRoutePoint(waypointPointId(waypoint), waypoint.coordinate);
      });
      const waypointPayload = routeWaypoints.map((waypoint) => ({
        id: waypointPointId(waypoint),
        label: waypoint.input.value.trim(),
        lon: waypoint.coordinate.lon,
        lat: waypoint.coordinate.lat
      }));
      setStatus(
        routeWaypoints.length
          ? uiText`경유지 ${routeWaypoints.length}개를 포함한 경로를 탐색하고 있습니다...`
          : uiText("Naver Directions 경로를 탐색하고 있습니다...")
      );
      routeWatchdog = window.setTimeout(() => {
        if (generation !== routeGeneration || !routeBusy) return;
        cancelRouteSearch(uiText("경로 응답을 받지 못했습니다. 연결을 확인한 뒤 다시 조회하세요."));
      }, 35000);
      qgisBridge.requestRoute(
        routeOrigin.lon,
        routeOrigin.lat,
        routeDestination.lon,
        routeDestination.lat,
        routePrioritySelect.value,
        JSON.stringify(waypointPayload),
        JSON.stringify(selectedRouteAvoidOptions()),
        JSON.stringify({...selectedRouteVehicleOptions(), language: mapLanguage}),
        routeOriginInput.value.trim(),
        routeDestinationInput.value.trim()
      );
    });

    function cancelRouteSearch(message = uiText("경로 탐색을 취소했습니다.")) {
      routeGeneration += 1;
      searchRequestId += 1;
      routeBusy = false;
      window.clearTimeout(routeWatchdog);
      if (qgisBridge && typeof qgisBridge.cancelRoute === "function") qgisBridge.cancelRoute();
      updateRouteControls();
      setStatus(message);
    }
    routeCancelButton.addEventListener("click", () => cancelRouteSearch());

    routeResetButton.addEventListener("click", () => {
      clearRouteInputs(true);
      clearRoutePath();
      setStatus(uiText("경로 지점을 초기화했습니다."));
    });
