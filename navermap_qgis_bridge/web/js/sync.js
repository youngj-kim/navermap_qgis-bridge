// SPDX-License-Identifier: GPL-2.0-or-later
    function syncNaverMapToQgis(force = false) {
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
        marker.setPosition(position);
      } catch (error) {
        window.setReverseSyncDiagnostic(`JS 좌표 오류: ${error.message}`);
        return;
      }

      if (!qgisBridge) {
        window.setReverseSyncDiagnostic("JS 실패: QGIS bridge 없음");
        setStatus("Naver Map moved, but the QGIS bridge is not ready.");
        return;
      }

      window.setReverseSyncDiagnostic(
        `JS 호출: ${lat.toFixed(6)}, ${lon.toFixed(6)}`
      );
      qgisBridge.moveQgisCenter(lon, lat, (result) => {
        window.setReverseSyncDiagnostic(result || "Python 응답 완료");
      });
      setStatus(`Naver Map -> QGIS EPSG:4326 ${lat.toFixed(6)}, ${lon.toFixed(6)}.`);
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
