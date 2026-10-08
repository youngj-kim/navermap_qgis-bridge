// SPDX-License-Identifier: GPL-2.0-or-later
    function connectQgisBridgeSignals() {
      if (!qgisBridge) {
        return;
      }

      if (qgisBridge.routeStatusChanged) {
        qgisBridge.routeStatusChanged.connect((success, message) => {
          routeBusy = false;
          updateRouteControls();
          setStatus(message);
        });
      }
      if (qgisBridge.localSearchResultsChanged) {
        qgisBridge.localSearchResultsChanged.connect(
          window.receiveLocalSearchResults
        );
      }
      if (qgisBridge.reverseSyncStatusChanged) {
        qgisBridge.reverseSyncStatusChanged.connect((message) => {
          window.setReverseSyncDiagnostic(message);
        });
      }
      if (qgisBridge.routeGuidanceChanged) {
        qgisBridge.routeGuidanceChanged.connect((payloadJson) => {
          try {
            renderRouteGuidance(JSON.parse(payloadJson));
          } catch (error) {
            routeGuidance = [];
            clearRoutePath();
            updateRoutePanelVisibility();
            setStatus("경로 안내 목록을 표시하지 못했습니다.");
          }
        });
      }
      if (qgisBridge.routeHistoryChanged) {
        qgisBridge.routeHistoryChanged.connect((payloadJson) => {
          try {
            renderRouteHistory(JSON.parse(payloadJson));
          } catch (error) {
            routeHistory = [];
            updateRoutePanelVisibility();
            setStatus("경로 이력 목록을 표시하지 못했습니다.");
          }
        });
      }
      if (qgisBridge.loadRouteHistoryInput) {
        qgisBridge.loadRouteHistoryInput.connect((payloadJson) => {
          try {
            window.loadRouteHistoryInput(JSON.parse(payloadJson));
          } catch (error) {
            setStatus("경로 이력을 입력창으로 불러오지 못했습니다.");
          }
        });
      }
    }

    window.receiveLocalSearchResults = function receiveLocalSearchResults(payloadJson) {
      let payload = {};
      try {
        payload = typeof payloadJson === "string"
          ? JSON.parse(payloadJson)
          : (payloadJson || {});
      } catch (_error) {
        setStatus("POI 검색 응답을 해석하지 못했습니다.");
        return;
      }
      const requestId = String(payload.request_id || "");
      const pending = localSearchRequests.get(requestId);
      if (!pending) {
        return;
      }
      localSearchRequests.delete(requestId);
      if (payload.success) {
        pending.resolve(Array.isArray(payload.results) ? payload.results : []);
      } else {
        pending.reject(new Error(payload.message || "POI 검색에 실패했습니다."));
      }
    };

    function initQgisBridge() {
      if (window.naverExternalBridge) {
        window.clearTimeout(qgisBridgeRetryTimer);
        qgisBridgeRetryTimer = null;
        qgisBridge = window.naverExternalBridge;
        bridgeDiagnostic.hidden = true;
        connectQgisBridgeSignals();
        updateRouteControls();
        setStatus("외부 브라우저 연동 모드로 QGIS와 연결했습니다.");
        return;
      }

      if (qgisBridge || qgisBridgeInitializing) {
        return;
      }

      if (!window.qt || !window.qt.webChannelTransport || !window.QWebChannel) {
        const missing = [];
        if (!window.qt) missing.push("window.qt");
        if (window.qt && !window.qt.webChannelTransport) missing.push("webChannelTransport");
        if (!window.QWebChannel) missing.push("QWebChannel");
        bridgeDiagnostic.textContent = `QGIS bridge 준비 중: ${missing.join(", ")}`;
        bridgeDiagnostic.hidden = false;
        window.clearTimeout(qgisBridgeRetryTimer);
        qgisBridgeRetryTimer = window.setTimeout(initQgisBridge, 100);
        return;
      }

      qgisBridgeInitializing = true;
      bridgeDiagnostic.textContent = "QGIS bridge 연결 중...";
      bridgeDiagnostic.hidden = false;
      window.clearTimeout(qgisBridgeRetryTimer);
      qgisBridgeRetryTimer = window.setTimeout(() => {
        if (qgisBridge) {
          return;
        }
        qgisBridgeInitializing = false;
        bridgeDiagnostic.textContent = "QGIS bridge 연결을 다시 시도하고 있습니다...";
        initQgisBridge();
      }, 1500);
      new QWebChannel(window.qt.webChannelTransport, (channel) => {
        if (qgisBridge) {
          return;
        }
        qgisBridgeInitializing = false;
        window.clearTimeout(qgisBridgeRetryTimer);
        qgisBridgeRetryTimer = null;
        qgisBridge = channel.objects.qgisBridge;
        bridgeDiagnostic.hidden = true;
        connectQgisBridgeSignals();
        updateRouteControls();
        setStatus("QGIS bridge connected.");
      });
    }
