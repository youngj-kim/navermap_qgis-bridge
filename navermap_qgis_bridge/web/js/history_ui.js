// SPDX-License-Identifier: GPL-2.0-or-later
    function formatGuidanceDistance(distance) {
      if (!Number.isFinite(distance) || distance <= 0) {
        return "";
      }
      if (distance < 1000) {
        return `${Math.round(distance)} m`;
      }
      return `${(distance / 1000).toFixed(1)} km`;
    }

    function formatGuidanceDuration(duration) {
      if (!Number.isFinite(duration) || duration <= 0) {
        return "";
      }
      if (duration < 60) {
        return `${Math.round(duration)}초`;
      }
      return `${Math.max(1, Math.round(duration / 60))}분`;
    }

    function selectedRouteAvoidOptions() {
      return routeAvoidCheckboxes
        .filter((checkbox) => checkbox.checked)
        .map((checkbox) => checkbox.value);
    }

    function updateRouteAvoidSummary() {
      const selected = routeAvoidCheckboxes.filter((checkbox) => checkbox.checked);
      routeAvoidToggle.textContent = `회피 ${selected.length}`;
      const labels = selected.map((checkbox) => checkbox.parentElement.textContent.trim());
      routeAvoidToggle.title = labels.length
        ? `경로 회피: ${labels.join(", ")}`
        : "경로 회피 옵션";
    }

    function selectedRouteVehicleOptions() {
      return {
        car_type: Number(routeCarType.value),
        car_fuel: routeCarFuel.value,
        car_hipass: routeCarHipass.checked
      };
    }

    function updateRouteVehicleSummary() {
      const typeLabel = routeCarType.options[routeCarType.selectedIndex].text;
      const fuelLabel = routeCarFuel.options[routeCarFuel.selectedIndex].text;
      const hipassLabel = routeCarHipass.checked ? ", 하이패스" : "";
      routeVehicleToggle.title = `차량: ${typeLabel}, ${fuelLabel}${hipassLabel}`;
    }

    function guidanceIconText(category) {
      const icons = {
        start: "출",
        destination: "도",
        waypoint: "경",
        straight: "↑",
        left: "↰",
        right: "↱",
        uturn: "↶",
        roundabout: "⟳",
        transition: "↗",
        other: "•"
      };
      return icons[category] || icons.other;
    }

    function routePriorityLabel(priority) {
      const labels = {
        RECOMMEND: "추천",
        TIME: "최단 시간",
        DISTANCE: "최단 거리"
      };
      return labels[priority] || priority || "";
    }

    function formatHistoryTime(value) {
      if (!value) {
        return "";
      }
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return value;
      }
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      const hour = String(date.getHours()).padStart(2, "0");
      const minute = String(date.getMinutes()).padStart(2, "0");
      return `${month}-${day} ${hour}:${minute}`;
    }

    function updateRoutePanelVisibility() {
      routeGuidancePanel.hidden =
        !routeGuidance.length &&
        !routeHistory.length &&
        activeRoutePanelTab !== "history";
    }

    function activateRoutePanelTab(tabName) {
      activeRoutePanelTab = tabName === "history" ? "history" : "guidance";
      const showingHistory = activeRoutePanelTab === "history";
      routeGuidanceTab.classList.toggle("is-active", !showingHistory);
      routeHistoryTab.classList.toggle("is-active", showingHistory);
      routeGuidanceTab.setAttribute("aria-selected", showingHistory ? "false" : "true");
      routeHistoryTab.setAttribute("aria-selected", showingHistory ? "true" : "false");
      routeGuidanceList.hidden = showingHistory;
      routeHistoryList.hidden = !showingHistory;
      routeGuidanceSummaryText.textContent = showingHistory
        ? `경로 이력 ${routeHistory.length}건`
        : routeGuidanceSummaryText.dataset.guidanceSummary || "";
      updateRoutePanelVisibility();
    }

    function selectRouteHistory(history, item) {
      activeRouteHistoryId = history.history_id || "";
      routeHistoryList.querySelectorAll(".history-item").forEach((candidate) => {
        candidate.classList.toggle("is-active", candidate === item);
      });
      if (qgisBridge && activeRouteHistoryId) {
        qgisBridge.selectRouteHistory(activeRouteHistoryId);
      }
      setStatus(`${history.origin_name || "출발지"} → ${history.destination_name || "도착지"}`);
    }

    function renderRouteHistory(payload) {
      const items = Array.isArray(payload.items) ? payload.items : [];
      const previousHistoryId = activeRouteHistoryId;
      routeHistory = items;
      const selectedHistoryId = payload.selected_history_id || activeRouteHistoryId || "";
      const selectedExists = items.some((history) => history.history_id === selectedHistoryId);
      activeRouteHistoryId = selectedExists ? selectedHistoryId : "";
      routeHistoryList.textContent = "";

      if (previousHistoryId && !activeRouteHistoryId) {
        renderRouteGuidance({ history_id: "", summary: {}, path: [], guides: [] });
      }

      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "history-empty";
        empty.textContent = "아직 경로 이력이 없습니다.";
        routeHistoryList.appendChild(empty);
      }

      items.forEach((history) => {
        const item = document.createElement("div");
        item.className = "history-item";
        item.setAttribute("role", "option");
        item.setAttribute("tabindex", "0");
        if (history.history_id === activeRouteHistoryId) {
          item.classList.add("is-active");
        }

        const title = document.createElement("span");
        title.className = "history-title";
        title.textContent = `${history.origin_name || "출발지"} → ${history.destination_name || "도착지"}`;

        const summary = document.createElement("span");
        summary.className = "history-meta";
        summary.textContent = history.result_summary || [
          formatGuidanceDuration(Number(history.duration_s)),
          formatGuidanceDistance(Number(history.distance_m)),
          `안내 ${Number(history.guidance_count) || 0}개`
        ].filter(Boolean).join(" · ");

        const options = document.createElement("span");
        options.className = "history-meta";
        const optionParts = [
          routePriorityLabel(history.priority),
          history.avoid ? `회피 ${history.avoid.split("|").filter(Boolean).length}` : "",
          formatHistoryTime(history.searched_at)
        ].filter(Boolean);
        options.textContent = optionParts.join(" · ");

        const actions = document.createElement("span");
        actions.className = "history-actions";
        [
          ["불러오기", "loadRouteHistory"],
          ["삭제", "deleteRouteHistory"],
          ["내보내기", "exportRouteHistory"]
        ].forEach(([label, bridgeMethod]) => {
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = label;
          button.addEventListener("click", (event) => {
            event.stopPropagation();
            if (bridgeMethod === "loadRouteHistory") {
              if (history.input) {
                window.loadRouteHistoryInput(history.input);
                selectRouteHistory(history, item);
                return;
              }
              setStatus("이력 입력 정보를 찾지 못했습니다.");
            }
            if (qgisBridge && history.history_id) {
              qgisBridge[bridgeMethod](history.history_id);
            } else {
              setStatus("QGIS 경로 이력 연결이 준비되지 않았습니다.");
            }
          });
          actions.appendChild(button);
        });

        item.append(title, summary, options, actions);
        item.addEventListener("click", () => selectRouteHistory(history, item));
        item.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectRouteHistory(history, item);
          }
        });
        routeHistoryList.appendChild(item);
      });

      if (activeRoutePanelTab === "history") {
        activateRoutePanelTab("history");
      }
      updateRouteControls();
      updateRoutePanelVisibility();
    }

    function selectRouteGuidance(guide, item) {
      activeGuidanceSequence = guide.sequence;
      routeGuidanceList.querySelectorAll(".guidance-item").forEach((candidate) => {
        candidate.classList.toggle("is-active", candidate === item);
      });

      moveViewer(guide.longitude, guide.latitude);
      if (qgisBridge) {
        qgisBridge.selectRouteGuidance(
          guide.sequence,
          guide.longitude,
          guide.latitude
        );
      }
      setStatus(`${guide.sequence}. ${guide.guidance}`);
    }

    function clearRoutePath() {
      if (routePolyline) {
        routePolyline.setMap(null);
        routePolyline = null;
      }
    }

    function renderRoutePath(path) {
      clearRoutePath();
      if (!map || !Array.isArray(path) || path.length < 2) {
        return;
      }

      const linePath = path
        .map((point) => ({
          lat: Number(point.lat),
          lon: Number(point.lon)
        }))
        .filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lon))
        .map((point) => new naver.maps.LatLng(point.lat, point.lon));

      if (linePath.length < 2) {
        return;
      }

      routePolyline = new naver.maps.Polyline({
        map,
        path: linePath,
        strokeWeight: 5,
        strokeColor: "#1976d2",
        strokeOpacity: 0.9,
        strokeStyle: "solid"
      });

      const bounds = new naver.maps.LatLngBounds();
      linePath.forEach((point) => bounds.extend(point));
      if (typeof map.fitBounds === "function") {
        map.fitBounds(bounds);
      }
      scheduleStableRelayout();
    }

    function renderRouteGuidance(payload) {
      const guides = Array.isArray(payload.guides) ? payload.guides : [];
      routeGuidance = guides;
      activeGuidanceSequence = null;
      routeGuidanceList.textContent = "";
      renderRoutePath(payload.path);

      if (!guides.length) {
        routeGuidanceSummaryText.dataset.guidanceSummary = "";
        updateRoutePanelVisibility();
        return;
      }

      const summary = payload.summary || {};
      const vehicle = summary.vehicle || {};
      const vehicleTypeLabels = {
        1: "소형",
        2: "중형",
        3: "대형",
        4: "대형 화물",
        5: "특수 화물",
        6: "경차",
        7: "이륜차"
      };
      const summaryParts = [
        formatGuidanceDuration(Number(summary.duration_s)),
        formatGuidanceDistance(Number(summary.distance_m)),
        Array.isArray(summary.avoid) && summary.avoid.length
          ? `회피 ${summary.avoid.length}`
          : "",
        vehicleTypeLabels[vehicle.car_type] || "",
        `안내 ${guides.length}개`
      ].filter(Boolean);
      routeGuidanceSummaryText.dataset.guidanceSummary = summaryParts.join(" · ");
      routeGuidancePanel.dataset.collapsed = "false";
      routeGuidanceToggle.textContent = "−";
      routeGuidanceToggle.title = "경로 안내 접기";
      routeGuidanceToggle.setAttribute("aria-label", "경로 안내 접기");

      guides.forEach((guide) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "guidance-item";
        item.setAttribute("role", "option");

        const sequence = document.createElement("span");
        sequence.className = "guidance-sequence";
        sequence.textContent = String(guide.sequence);

        const icon = document.createElement("span");
        icon.className = `guidance-icon ${guide.category || "other"}`;
        icon.textContent = guidanceIconText(guide.category);
        icon.setAttribute("aria-hidden", "true");

        const copy = document.createElement("span");
        copy.className = "guidance-copy";

        const title = document.createElement("span");
        title.className = "guidance-title";
        title.textContent = guide.guidance || guide.name || "경로 안내";

        const meta = document.createElement("span");
        meta.className = "guidance-meta";
        const metaParts = [
          formatGuidanceDistance(Number(guide.distance_m)),
          formatGuidanceDuration(Number(guide.duration_s))
        ].filter(Boolean);
        meta.textContent = metaParts.length ? metaParts.join(" · ") : "현재 위치";

        copy.append(title, meta);
        item.append(sequence, icon, copy);
        item.addEventListener("click", () => selectRouteGuidance(guide, item));
        routeGuidanceList.appendChild(item);
      });

      activateRoutePanelTab("guidance");
      updateRoutePanelVisibility();
    }
