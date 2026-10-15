// SPDX-License-Identifier: GPL-2.0-or-later
    function syncNaverMapToQgis(force = false, dragFinished = false) {
      if (!force && isBridgeSyncSuppressed()) {
        window.setReverseSyncDiagnostic("JS 보류: QGIS 동기화 중");
        return;
      }
      window.setReverseSyncDiagnostic("JS 이벤트 수신");
      let position;
      let lat;
      let lon;
      try {
        position = map.getCenter();
        lat = position.lat();
        lon = position.lng();
      } catch (error) {
        window.setReverseSyncDiagnostic(`JS 좌표 오류: ${error.message}`);
        return;
      }

      if (!qgisBridge) {
        window.setReverseSyncDiagnostic("JS 실패: QGIS bridge 없음");
        setStatus("Naver Map moved, but the QGIS bridge is not ready.");
        return;
      }

      const zoom = typeof map.getZoom === "function" ? map.getZoom() : null;
      const previous = mapViewSnapshot;
      if (!dragFinished && previous && previous.zoom === zoom && Math.abs(previous.lon - lon) < 1e-9 && Math.abs(previous.lat - lat) < 1e-9) return;
      if (!dragFinished && previous && previous.zoom !== zoom && typeof qgisBridge.zoomQgisView === "function") {
        try {
          qgisBridge.zoomQgisView(lon, lat, naverGroundResolution());
          mapViewSnapshot = {lon, lat, zoom};
        } catch (_error) { setStatus("지도 확대 비율을 전달하지 못했습니다."); }
        return;
      }
      marker.setPosition(position);

      window.setReverseSyncDiagnostic(
        `JS 호출: ${lat.toFixed(6)}, ${lon.toFixed(6)}`
      );
      try {
        // Use the same two-argument call as the working panorama -> QGIS path.
        qgisBridge.moveQgisCenter(lon, lat);
        mapViewSnapshot = {lon, lat, zoom};
        if (dragFinished || !mapDragActive) {
          moveViewer(lon, lat, {suppressBridge:true});
        }
      } catch (_error) {
        window.setReverseSyncDiagnostic("JS 실패: 지도 위치 전달 오류");
        setStatus("지도 위치를 전달하지 못했습니다. 다시 이동해 주세요.");
        return;
      }
      setStatus(`Naver Map -> QGIS EPSG:4326 ${lat.toFixed(6)}, ${lon.toFixed(6)}.`);
    }

    function naverGroundResolution() {
      const projection = map.getProjection();
      const center = projection.fromCoordToOffset(map.getCenter());
      const first = projection.fromOffsetToCoord(new naver.maps.Point(center.x - 64, center.y));
      const second = projection.fromOffsetToCoord(new naver.maps.Point(center.x + 64, center.y));
      const resolution = projection.getDistance(first, second) / 128;
      if (!Number.isFinite(resolution) || resolution <= 0) throw new Error("Invalid map resolution");
      return resolution;
    }

    function scheduleNaverMapSync() {
      if (isBridgeSyncSuppressed()) {
        return;
      }
      if (mapSyncTimer !== null) {
        return;
      }

      mapSyncTimer = window.setTimeout(() => {
        mapSyncTimer = null;
        syncNaverMapToQgis();
      }, 120);
    }

    function syncRoadviewStateToQgis() {
      if (!qgisBridge || !roadview) {
        return;
      }

      const position = currentRoadviewCoordinate();
      const viewpoint = roadview.getPov();
      if (!position || !viewpoint) {
        return;
      }

      const lon = position.lng();
      const lat = position.lat();
      const pan = Number(viewpoint.pan);
      const tilt = Number(viewpoint.tilt);
      const zoom = Number(viewpoint.fov);
      if (![lon, lat, pan, tilt, zoom].every(Number.isFinite)) {
        return;
      }

      const panoId = roadview.getPanoId();
      qgisBridge.updateRoadviewState(
        lon,
        lat,
        pan,
        tilt,
        zoom,
        panoId === null || panoId === undefined ? "" : String(panoId)
      );
    }

    function scheduleRoadviewStateSync() {
      if (roadviewStateTimer !== null) {
        return;
      }

      roadviewStateTimer = window.setTimeout(() => {
        roadviewStateTimer = null;
        syncRoadviewStateToQgis();
      }, 100);
    }
