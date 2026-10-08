// SPDX-License-Identifier: GPL-2.0-or-later
    function savedViewerLayout() {
      try {
        return window.localStorage.getItem(viewerLayoutStorageKey) || "map-top";
      } catch (_error) {
        return "map-top";
      }
    }

    function relayoutNaverViews() {
      const mapElement = document.getElementById("map");
      const roadviewElement = document.getElementById("roadview");

      if (map && mapElement.clientWidth > 0 && mapElement.clientHeight > 0) {
        suppressBridgeSync(300);
        const mapCenter = map.getCenter();
        if (typeof map.setSize === "function") {
          map.setSize(new naver.maps.Size(mapElement.clientWidth, mapElement.clientHeight));
        }
        if (typeof map.refresh === "function") {
          map.refresh(true);
        }
        if (mapCenter) {
          map.setCenter(mapCenter);
        }
      }
      if (roadview && typeof roadview.setSize === "function") {
        if (
          roadviewElement.clientWidth > 0 &&
          roadviewElement.clientHeight > 0
        ) {
          roadview.setSize(
            new naver.maps.Size(
              roadviewElement.clientWidth,
              roadviewElement.clientHeight
            )
          );
        }
      }
    }

    function scheduleStableRelayout() {
      stableRelayoutTimers.forEach((timer) => window.clearTimeout(timer));
      stableRelayoutTimers = [0, 80, 220, 480].map((delay) => {
        return window.setTimeout(relayoutNaverViews, delay);
      });
    }

    function isHorizontalSplitLayout(layout = viewerLayoutSelect.value) {
      if (window.matchMedia("(max-width: 980px)").matches) {
        return true;
      }
      return layout === "map-top" || layout === "roadview-top";
    }

    function savedViewerSplit() {
      try {
        const value = Number(window.localStorage.getItem(viewerSplitStorageKey));
        return Number.isFinite(value) ? Math.min(70, Math.max(30, value)) : 50;
      } catch (_error) {
        return 50;
      }
    }

    function applyViewerSplit(percent) {
      const nextPercent = Math.min(70, Math.max(30, Number(percent) || 50));
      viewer.style.setProperty("--split-primary-size", `${nextPercent}fr`);
      viewer.style.setProperty("--split-secondary-size", `${100 - nextPercent}fr`);
      try {
        window.localStorage.setItem(viewerSplitStorageKey, String(nextPercent));
      } catch (_error) {
        // Ignore private browsing or locked storage.
      }
      scheduleStableRelayout();
    }

    function updateSplitterState(layout = viewerLayoutSelect.value) {
      const horizontal = isHorizontalSplitLayout(layout);
      viewSplitter.setAttribute(
        "aria-orientation",
        horizontal ? "horizontal" : "vertical"
      );
      splitToggle.textContent = horizontal ? "⇅" : "⇄";
    }

    function swappedViewerLayout(layout = viewerLayoutSelect.value) {
      const swaps = {
        "map-top": "roadview-top",
        "roadview-top": "map-top",
        "map-left": "roadview-left",
        "roadview-left": "map-left"
      };
      return swaps[layout] || "map-top";
    }

    async function toggleBrowserFullScreen() {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else if (viewer.requestFullscreen) {
        await viewer.requestFullscreen();
      }
      scheduleStableRelayout();
    }

    function applyViewerLayout(layout) {
      const allowedLayouts = new Set([
        "map-top",
        "roadview-top",
        "map-left",
        "roadview-left"
      ]);
      const nextLayout = allowedLayouts.has(layout) ? layout : "map-top";
      viewer.classList.remove(
        "layout-map-top",
        "layout-roadview-top",
        "layout-map-left",
        "layout-roadview-left"
      );
      viewer.classList.add(`layout-${nextLayout}`);
      viewerLayoutSelect.value = nextLayout;
      updateSplitterState(nextLayout);
      try {
        window.localStorage.setItem(viewerLayoutStorageKey, nextLayout);
      } catch (_error) {
        // Ignore private browsing or locked storage.
      }
      scheduleStableRelayout();
    }
