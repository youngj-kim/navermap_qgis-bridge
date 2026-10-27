# SPDX-License-Identifier: GPL-2.0-or-later
"""Native WebChannel signal/slot contract, separate from dock presentation."""

import math
from qgis.PyQt.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QDesktopServices


class NaverWebBridge(QObject):
    centerRequested = pyqtSignal(float, float)
    zoomRequested = pyqtSignal(float, float, float)

    @pyqtSlot(float, float, float)
    def zoomQgisView(self, lon, lat, meters_per_pixel):
        self.zoomRequested.emit(lon, lat, meters_per_pixel)
    reverseSyncStatusChanged = pyqtSignal(str)
    roadviewStateChanged = pyqtSignal(float, float, float, float, float, str)
    routeRequested = pyqtSignal(
        float, float, float, float, str, str, str, str, str, str
    )
    routePointChanged = pyqtSignal(str, float, float)
    routePointCleared = pyqtSignal(str)
    routePointsCleared = pyqtSignal()
    routeStatusChanged = pyqtSignal(bool, str)
    routeGuidanceChanged = pyqtSignal(str)
    localSearchResultsChanged = pyqtSignal(str)
    routeGuidanceSelected = pyqtSignal(int, float, float)
    routeHistoryChanged = pyqtSignal(str)
    loadRouteHistoryInput = pyqtSignal(str)
    routeHistorySelected = pyqtSignal(str)
    routeHistoryLoadRequested = pyqtSignal(str)
    routeHistoryDeleteRequested = pyqtSignal(str)
    routeHistoryImportRequested = pyqtSignal()
    routeHistoryBatchDeleteRequested = pyqtSignal(str)
    routeHistoryExportRequested = pyqtSignal(str)
    routeHistoryRefreshRequested = pyqtSignal()
    localSearchRequested = pyqtSignal(str, str)
    fullScreenRequested = pyqtSignal()
    viewerReloadRequested = pyqtSignal()
    routeCancelRequested = pyqtSignal()
    projectReset = pyqtSignal(int)

    @pyqtSlot()
    def reloadViewer(self):
        self.viewerReloadRequested.emit()

    @pyqtSlot()
    def cancelRoute(self):
        self.routeCancelRequested.emit()

    @pyqtSlot(float, float, result=str)
    def moveQgisCenter(self, lon, lat):
        self.reverseSyncStatusChanged.emit(
            f"Python 수신: {lat:.6f}, {lon:.6f}"
        )
        self.centerRequested.emit(lon, lat)
        return "Python 호출 완료"

    @pyqtSlot(float, float)
    def openNaverRoadview(self, lon, lat):
        if not math.isfinite(lon) or not math.isfinite(lat):
            return
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            return

        url = QUrl(
            "https://map.naver.com/link/roadview/"
            f"{lat:.8f},{lon:.8f}"
        )
        QDesktopServices.openUrl(url)

    @pyqtSlot(float, float, float, float, float, str)
    def updateRoadviewState(self, lon, lat, pan, tilt, zoom, pano_id):
        self.roadviewStateChanged.emit(
            lon,
            lat,
            pan,
            tilt,
            zoom,
            pano_id,
        )

    @pyqtSlot(float, float, float, float, str, str, str, str, str, str)
    def requestRoute(
        self,
        origin_lon,
        origin_lat,
        destination_lon,
        destination_lat,
        priority,
        waypoints_json,
        avoid_json,
        vehicle_json,
        origin_label,
        destination_label,
    ):
        self.routeRequested.emit(
            origin_lon,
            origin_lat,
            destination_lon,
            destination_lat,
            priority,
            waypoints_json,
            avoid_json,
            vehicle_json,
            origin_label,
            destination_label,
        )

    @pyqtSlot(str, float, float)
    def setRoutePoint(self, role, lon, lat):
        self.routePointChanged.emit(role, lon, lat)

    @pyqtSlot(str)
    def clearRoutePoint(self, role):
        self.routePointCleared.emit(role)

    @pyqtSlot()
    def clearRoutePoints(self):
        self.routePointsCleared.emit()

    @pyqtSlot(int, float, float)
    def selectRouteGuidance(self, sequence, lon, lat):
        self.routeGuidanceSelected.emit(sequence, lon, lat)

    @pyqtSlot(str)
    def selectRouteHistory(self, history_id):
        self.routeHistorySelected.emit(history_id)

    @pyqtSlot(str)
    def loadRouteHistory(self, history_id):
        self.routeHistoryLoadRequested.emit(history_id)

    @pyqtSlot()
    def importRouteHistory(self):
        self.routeHistoryImportRequested.emit()

    @pyqtSlot(str)
    def deleteRouteHistories(self, history_ids_json):
        self.routeHistoryBatchDeleteRequested.emit(history_ids_json)

    @pyqtSlot(str)
    def deleteRouteHistory(self, history_id):
        self.routeHistoryDeleteRequested.emit(history_id)

    @pyqtSlot(str)
    def exportRouteHistory(self, history_id):
        self.routeHistoryExportRequested.emit(history_id)

    @pyqtSlot()
    def refreshRouteHistory(self):
        self.routeHistoryRefreshRequested.emit()

    @pyqtSlot(str, str)
    def requestLocalSearch(self, request_id, query):
        self.localSearchRequested.emit(request_id, query)

    @pyqtSlot()
    def toggleFullScreen(self):
        self.fullScreenRequested.emit()
