// SPDX-License-Identifier: GPL-2.0-or-later
    function setStatus(message) {
      document.getElementById("status").textContent = translateViewerStatus(message);
    }

    window.setReverseSyncDiagnostic = function(message) {
      reverseSyncDiagnostic.textContent = String(message || "");
    };

    function suppressBridgeSync(duration = 700) {
      bridgeSyncSuppressedUntil = Date.now() + duration;
    }

    function isBridgeSyncSuppressed() {
      return Date.now() < bridgeSyncSuppressedUntil;
    }

    function elementSize(element) {
      return new naver.maps.Size(
        Math.max(1, element.clientWidth),
        Math.max(1, element.clientHeight)
      );
    }

    function currentRoadviewCoordinate() {
      if (!roadview || typeof roadview.getLocation !== "function") {
        return null;
      }
      const location = roadview.getLocation();
      return location && location.coord ? location.coord : null;
    }

    function updateRoadviewPhotoDate() {
      const label = document.getElementById("roadview-photo-date");
      let photoDate = "";
      try {
        const location = roadview && typeof roadview.getLocation === "function"
          ? roadview.getLocation()
          : null;
        // NAVER documents photodate as a string, without a fixed date format.
        // Preserve its precision rather than guessing a date or timezone.
        if (location && typeof location.photodate === "string") {
          photoDate = location.photodate.trim();
        }
      } catch (_) {
        // Missing metadata must not interrupt map/roadview synchronization.
      }
      label.textContent = photoDate ? uiText`촬영일: ${photoDate}` : uiText("촬영일 정보 없음");
    }
