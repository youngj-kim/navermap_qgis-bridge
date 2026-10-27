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
        return uiText`${Math.round(duration)}초`;
      }
      return uiText`${Math.max(1, Math.round(duration / 60))}분`;
    }

    function selectedRouteAvoidOptions() {
      return routeAvoidCheckboxes
        .filter((checkbox) => checkbox.checked)
        .map((checkbox) => checkbox.value);
    }

    function updateRouteAvoidSummary() {
      const selected = routeAvoidCheckboxes.filter((checkbox) => checkbox.checked);
      routeAvoidToggle.textContent = uiText`회피 ${selected.length}`;
      const labels = selected.map((checkbox) => checkbox.parentElement.textContent.trim());
      routeAvoidToggle.title = labels.length
        ? uiText`경로 회피: ${labels.join(", ")}`
        : uiText("경로 회피 옵션");
    }

    function selectedRouteVehicleOptions() {
      return {
        car_type: Number(routeCarType.value),
        car_fuel: routeCarFuel.value,
        car_hipass: false
      };
    }

    function updateRouteVehicleSummary() {
      const typeLabel = routeCarType.options[routeCarType.selectedIndex].text;
      const fuelLabel = routeCarFuel.options[routeCarFuel.selectedIndex].text;
      const hipassLabel = routeCarHipass.checked ? uiText(", 과거 하이패스 설정 (계산 미반영)") : "";
      routeVehicleToggle.title = uiText`차량: ${typeLabel}, ${fuelLabel}${hipassLabel}`;
    }

    function guidanceIconText(category) {
      const icons = {
        start: uiText("출"),
        destination: uiText("도"),
        waypoint: uiText("경"),
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

    function routePriorityLabel(priority, avoid = []) {
      const choices = Array.isArray(avoid) ? avoid : String(avoid).split("|").filter(Boolean);
      if (choices.length) {
        const label = choices.includes("toll") ? uiText("무료 우선") : uiText("자동차전용도로 회피");
        return label + (choices.length > 1 ? uiText(" (기존 복수 설정)") : "");
      }
      const labels = {
        RECOMMEND: uiText("실시간 최적"),
        TIME: uiText("실시간 빠른길"),
        DISTANCE: uiText("실시간 편한길")
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
      if (!routeGuidance.length && !routeGuidanceList.childElementCount) {
        const empty = document.createElement("div");
        empty.className = "history-empty";
        empty.textContent = uiText("표시할 경로 안내가 없습니다.");
        routeGuidanceList.appendChild(empty);
      }
      if (!routeGuidance.length && activeRoutePanelTab === "guidance") {
        routeGuidanceSummaryText.textContent = uiText("경로 안내 없음");
      }
      routeGuidancePanel.hidden =
        !routePanelOpened &&
        !routeGuidance.length &&
        !routeHistory.length;
    }

    function activateRoutePanelTab(tabName) {
      // Once opened, keep the tabs reachable even when either tab has no data.
      routePanelOpened = true;
      activeRoutePanelTab = tabName === "history" ? "history" : "guidance";
      const showingHistory = activeRoutePanelTab === "history";
      routeGuidanceTab.classList.toggle("is-active", !showingHistory);
      routeHistoryTab.classList.toggle("is-active", showingHistory);
      routeGuidanceTab.setAttribute("aria-selected", showingHistory ? "false" : "true");
      routeHistoryTab.setAttribute("aria-selected", showingHistory ? "true" : "false");
      routeGuidanceList.hidden = showingHistory;
      routeHistoryList.hidden = !showingHistory;
      routeGuidanceSummaryText.textContent = showingHistory
        ? uiText`경로 이력 ${routeHistory.length}건`
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
      setStatus(uiText`${history.origin_name || uiText("출발지")} → ${history.destination_name || uiText("도착지")}`);
    }

    const checkedRouteHistoryIds = new Set();

    function updateHistorySelectionControls() {
      const count = checkedRouteHistoryIds.size;
      const selectAll = routeHistoryList.querySelector(".history-select-all");
      if (selectAll) {
        selectAll.checked = routeHistory.length > 0 && count === routeHistory.length;
        selectAll.indeterminate = count > 0 && count < routeHistory.length;
        selectAll.disabled = routeBusy || !routeHistory.length;
      }
      const remove = routeHistoryList.querySelector(".history-delete-selected");
      if (remove) {
        remove.textContent = uiText`선택 삭제 (${count})`;
        remove.disabled = routeBusy || !qgisBridge || !count;
      }
      const importButton = routeHistoryList.querySelector(".history-import");
      if (importButton) importButton.disabled = routeBusy || !qgisBridge;
      routeHistoryList.querySelectorAll(".history-select").forEach((checkbox) => {
        checkbox.checked = checkedRouteHistoryIds.has(checkbox.value);
        checkbox.disabled = routeBusy;
      });
    }

    function renderHistoryToolbar() {
      const toolbar = document.createElement("div");
      toolbar.className = "history-toolbar history-actions";
      const importButton = document.createElement("button");
      importButton.type = "button";
      importButton.className = "history-import";
      importButton.textContent = uiText("파일 불러오기");
      importButton.addEventListener("click", () => {
        if (qgisBridge && !routeBusy) qgisBridge.importRouteHistory();
      });
      const label = document.createElement("label");
      const selectAll = document.createElement("input");
      selectAll.type = "checkbox";
      selectAll.className = "history-select-all";
      selectAll.addEventListener("change", () => {
        checkedRouteHistoryIds.clear();
        if (selectAll.checked) routeHistory.forEach((history) => checkedRouteHistoryIds.add(history.history_id));
        updateHistorySelectionControls();
      });
      label.append(selectAll, document.createTextNode(uiText("전체 선택")));
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "history-delete-selected";
      remove.addEventListener("click", () => {
        if (qgisBridge && !routeBusy && checkedRouteHistoryIds.size) {
          qgisBridge.deleteRouteHistories(JSON.stringify([...checkedRouteHistoryIds]));
        }
      });
      toolbar.append(importButton, label, remove);
      routeHistoryList.appendChild(toolbar);
    }

    function renderRouteHistory(payload) {
      const items = Array.isArray(payload.items) ? payload.items : [];
      const previousHistoryId = activeRouteHistoryId;
      routeHistory = items;
      const selectedHistoryId = payload.selected_history_id || activeRouteHistoryId || "";
      const selectedExists = items.some((history) => history.history_id === selectedHistoryId);
      activeRouteHistoryId = selectedExists ? selectedHistoryId : "";
      routeHistoryList.textContent = "";
      const availableIds = new Set(items.map((history) => history.history_id));
      checkedRouteHistoryIds.forEach((id) => {
        if (!availableIds.has(id)) checkedRouteHistoryIds.delete(id);
      });
      renderHistoryToolbar();

      if (previousHistoryId && !activeRouteHistoryId) {
        renderRouteGuidance({ history_id: "", summary: {}, path: [], guides: [] });
      }

      if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "history-empty";
        empty.textContent = uiText("아직 경로 이력이 없습니다.");
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

        const selection = document.createElement("label");
        selection.className = "history-selection";
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "history-select";
        checkbox.value = history.history_id;
        checkbox.setAttribute("aria-label", uiText("선택"));
        checkbox.addEventListener("change", () => {
          if (checkbox.checked) checkedRouteHistoryIds.add(history.history_id);
          else checkedRouteHistoryIds.delete(history.history_id);
          updateHistorySelectionControls();
        });
        selection.addEventListener("click", (event) => event.stopPropagation());
        selection.append(checkbox);
        item.appendChild(selection);

        const title = document.createElement("span");
        title.className = "history-title";
        title.textContent = uiText`${history.origin_name || uiText("출발지")} → ${history.destination_name || uiText("도착지")}`;

        const summary = document.createElement("span");
        summary.className = "history-meta";
        summary.textContent = history.result_summary || [
          formatGuidanceDuration(Number(history.duration_s)),
          formatGuidanceDistance(Number(history.distance_m)),
          uiText`안내 ${Number(history.guidance_count) || 0}개`
        ].filter(Boolean).join(" · ");

        const options = document.createElement("span");
        options.className = "history-meta";
        const optionParts = [
          routePriorityLabel(history.priority, history.avoid),
          formatHistoryTime(history.searched_at)
        ].filter(Boolean);
        options.textContent = optionParts.join(" · ");

        const actions = document.createElement("span");
        actions.className = "history-actions";
        [
          [uiText("불러오기"), "loadRouteHistory"],
          [uiText("삭제"), "deleteRouteHistory"],
          [uiText("내보내기"), "exportRouteHistory"]
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
              setStatus(uiText("이력 입력 정보를 찾지 못했습니다."));
            }
            if (qgisBridge && history.history_id) {
              qgisBridge[bridgeMethod](history.history_id);
            } else {
              setStatus(uiText("QGIS 경로 이력 연결이 준비되지 않았습니다."));
            }
          });
          actions.appendChild(button);
        });

        item.append(title, summary, options, actions);
        item.addEventListener("click", () => selectRouteHistory(history, item));
        item.addEventListener("keydown", (event) => {
          if (event.target === item && (event.key === "Enter" || event.key === " ")) {
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
      updateHistorySelectionControls();
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
      setStatus(`${guide.sequence}. ${localizedGuidance(guide)}`);
    }

    function clearRoutePath() {
      displayedRoutePayload = null;
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
      displayedRoutePayload = payload;

      if (!guides.length) {
        routeGuidanceSummaryText.dataset.guidanceSummary = "";
        updateRoutePanelVisibility();
        return;
      }

      const summary = payload.summary || {};
      const vehicle = summary.vehicle || {};
      const vehicleTypeLabels = {
        1: uiText("소형"),
        2: uiText("중형"),
        3: uiText("대형"),
        4: uiText("대형 화물"),
        5: uiText("특수 화물"),
        6: uiText("경차"),
        7: uiText("이륜차")
      };
      const summaryParts = [
        formatGuidanceDuration(Number(summary.duration_s)),
        formatGuidanceDistance(Number(summary.distance_m)),
        routePriorityLabel(summary.priority, summary.avoid),
        vehicleTypeLabels[vehicle.car_type] || "",
        uiText`안내 ${guides.length}개`
      ].filter(Boolean);
      routeGuidanceSummaryText.dataset.guidanceSummary = summaryParts.join(" · ");
      routeGuidancePanel.dataset.collapsed = "false";
      routeGuidanceToggle.textContent = "−";
      routeGuidanceToggle.title = uiText("경로 안내 접기");
      routeGuidanceToggle.setAttribute("aria-label", uiText("경로 안내 접기"));

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
        title.textContent = localizedGuidance(guide);
        title.title = guide.guidance || guide.name || "";

        const meta = document.createElement("span");
        meta.className = "guidance-meta";
        const metaParts = [
          formatGuidanceDistance(Number(guide.distance_m)),
          formatGuidanceDuration(Number(guide.duration_s))
        ].filter(Boolean);
        meta.textContent = metaParts.length ? metaParts.join(" · ") : uiText("현재 위치");

        copy.append(title, meta);
        item.append(sequence, icon, copy);
        item.addEventListener("click", () => selectRouteGuidance(guide, item));
        routeGuidanceList.appendChild(item);
      });

      activateRoutePanelTab("guidance");
      updateRoutePanelVisibility();
    }
