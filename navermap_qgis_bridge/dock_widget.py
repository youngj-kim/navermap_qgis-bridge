import json

import math

from qgis.PyQt.QtCore import Qt, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QKeySequence
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    from qgis.PyQt.QtGui import QShortcut
except ImportError:
    from qgis.PyQt.QtWidgets import QShortcut


WEB_RUNTIME_IMPORT_ERRORS = []


def _record_import_error(component, error):
    WEB_RUNTIME_IMPORT_ERRORS.append(
        {
            "component": component,
            "primary_error": str(error),
        }
    )


try:
    from qgis.PyQt.QtWebChannel import QWebChannel
except ImportError as primary_error:
    QWebChannel = None
    _record_import_error("Qt WebChannel", primary_error)

try:
    from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
except ImportError as primary_error:
    QWebEngineView = None
    _record_import_error("Qt WebEngine", primary_error)

from .settings import naver_javascript_key, naver_map_base_url
from .viewer_document import build_viewer_html
from .web_bridge import NaverWebBridge


def web_runtime_diagnostic():
    if QWebEngineView is not None and QWebChannel is not None:
        return ""

    lines = [
        "Qt WebEngine 또는 WebChannel을 사용할 수 없어 외부 브라우저 연동 모드를 사용합니다.",
        "아래의 외부 연동 창 열기 버튼을 누르면 Naver Map/거리뷰가 기본 브라우저에서 열리고 QGIS와 위치가 동기화됩니다.",
        "QGIS 캔버스를 이동하면 외부 Naver 지도와 거리뷰가 따라 이동하며, 외부 Naver 지도나 거리뷰에서 이동한 위치도 QGIS에 반영됩니다.",
    ]

    lines.extend(f"{item['component']}: {item['primary_error']}" for item in WEB_RUNTIME_IMPORT_ERRORS)
    return "\n".join(lines)




class NaverMapDockWidget(QDockWidget):
    centerRequested = pyqtSignal(float, float)
    zoomRequested = pyqtSignal(float, float, float)
    roadviewStateChanged = pyqtSignal(float, float, float, float, float, str)
    routeRequested = pyqtSignal(
        float, float, float, float, str, str, str, str, str, str
    )
    routePointChanged = pyqtSignal(str, float, float)
    routePointCleared = pyqtSignal(str)
    routePointsCleared = pyqtSignal()
    routeGuidanceSelected = pyqtSignal(int, float, float)
    routeHistorySelected = pyqtSignal(str)
    routeHistoryLoadRequested = pyqtSignal(str)
    routeHistoryDeleteRequested = pyqtSignal(str)
    routeHistoryImportRequested = pyqtSignal()
    routeHistoryBatchDeleteRequested = pyqtSignal(str)
    routeHistoryExportRequested = pyqtSignal(str)
    routeHistoryRefreshRequested = pyqtSignal()
    localSearchRequested = pyqtSignal(str, str)
    externalViewerRequested = pyqtSignal()
    routeCancelRequested = pyqtSignal()

    def reset_project(self, epoch):
        if self.web_bridge is not None:
            self.web_bridge.projectReset.emit(epoch)

    def __init__(self, parent=None):
        super().__init__("Naver Map / Street View", parent)
        self.web_view = None
        self.web_bridge = None
        self.web_channel = None
        self.web_runtime_diagnostic = web_runtime_diagnostic()
        self.full_screen_restore_floating = None
        self.fallback_lon = None
        self.fallback_lat = None
        self.fallback_coordinate_label = None
        self.fallback_external_button = None
        self.fallback_map_button = None
        self.fallback_roadview_button = None

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.web_runtime_diagnostic:
            self._configure_external_browser_fallback(layout, container)
        else:
            self.web_view = QWebEngineView(container)
            layout.addWidget(self.web_view)
            self._configure_web_channel()
            self._load_viewer()

        self.setWidget(container)
        self._initial_float_sized = False
        self.topLevelChanged.connect(self._dock_mode_changed)
        escape_key = getattr(Qt, "Key_Escape", None)
        if escape_key is None:
            escape_key = Qt.Key.Key_Escape
        self._escape_shortcut = QShortcut(QKeySequence(escape_key), self)
        self._escape_shortcut.activated.connect(self.exit_full_screen)

    def _dock_mode_changed(self, floating):
        if floating and not self._initial_float_sized:
            self._initial_float_sized = True
            screen = self.screen()
            if screen is not None:
                available = screen.availableGeometry()
                self.resize(min(1100, available.width()), min(850, available.height()))
                position = self.pos()
                self.move(max(available.left(), min(position.x(), available.right() - self.width() + 1)),
                          max(available.top(), min(position.y(), available.bottom() - self.height() + 1)))
        if self.web_view is not None:
            self.web_view.page().runJavaScript("if (typeof scheduleStableRelayout === 'function') scheduleStableRelayout();")

    def set_center(self, lon, lat):
        if self.web_view is None:
            self._set_fallback_center(lon, lat)
            return

        script = "window.centerNaverMap({lon}, {lat});".format(
            lon=json.dumps(float(lon)),
            lat=json.dumps(float(lat)),
        )
        self.web_view.page().runJavaScript(script)

    def set_view(self, lon, lat, meters_per_pixel, preserve_roadview=False):
        if self.web_view is None:
            self._set_fallback_center(lon, lat)
            return
        payload = json.dumps([lon, lat, meters_per_pixel, bool(preserve_roadview)])
        self.web_view.page().runJavaScript(f"window.syncNaverView(...{payload});")

    def set_reverse_sync_status(self, message):
        if self.web_bridge is not None:
            self.web_bridge.reverseSyncStatusChanged.emit(str(message))
        if self.web_view is not None:
            script = (
                "if (window.setReverseSyncDiagnostic) {"
                " window.setReverseSyncDiagnostic("
                + json.dumps(str(message))
                + "); }"
            )
            self.web_view.page().runJavaScript(script)

    def reload_viewer(self):
        if self.web_view is not None:
            self._load_viewer()

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.exit_full_screen()
        else:
            self.enter_full_screen()

    def enter_full_screen(self):
        self.full_screen_restore_floating = self.isFloating()
        if not self.isFloating():
            self.setFloating(True)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def exit_full_screen(self):
        if not self.isFullScreen():
            return

        restore_floating = self.full_screen_restore_floating
        self.showNormal()
        if restore_floating is False:
            self.setFloating(False)
        self.full_screen_restore_floating = None

    def set_route_status(self, success, message):
        if self.web_bridge is not None:
            self.web_bridge.routeStatusChanged.emit(bool(success), str(message))

    def set_route_guidance(self, payload):
        if self.web_bridge is not None:
            self.web_bridge.routeGuidanceChanged.emit(
                json.dumps(payload, ensure_ascii=False)
            )

    def set_route_history(self, payload):
        if self.web_bridge is not None:
            self.web_bridge.routeHistoryChanged.emit(
                json.dumps(payload, ensure_ascii=False)
            )

    def set_route_history_input(self, payload):
        if self.web_bridge is not None:
            self.web_bridge.loadRouteHistoryInput.emit(
                json.dumps(payload, ensure_ascii=False)
            )

    def set_local_search_results(self, payload):
        payload_json = json.dumps(payload, ensure_ascii=False)
        if self.web_bridge is not None:
            self.web_bridge.localSearchResultsChanged.emit(payload_json)
        if self.web_view is not None:
            script = (
                "if (window.receiveLocalSearchResults) {"
                " window.receiveLocalSearchResults("
                + json.dumps(payload_json)
                + "); }"
            )
            self.web_view.page().runJavaScript(script)

    def load_route_history_input(self, payload):
        # Keep both existing delivery paths until runtime tests prove one redundant.
        self.set_route_history_input(payload)
        script = "window.loadRouteHistoryInput({payload});".format(
            payload=json.dumps(payload, ensure_ascii=False)
        )
        self.web_view.page().runJavaScript(script)

    def _configure_web_channel(self):
        self.web_bridge = NaverWebBridge(self)
        self.web_bridge.centerRequested.connect(self.centerRequested.emit)
        self.web_bridge.zoomRequested.connect(self.zoomRequested.emit)
        self.web_bridge.roadviewStateChanged.connect(
            self.roadviewStateChanged.emit
        )
        self.web_bridge.routeRequested.connect(self.routeRequested.emit)
        self.web_bridge.routeCancelRequested.connect(self.routeCancelRequested.emit)
        self.web_bridge.routePointChanged.connect(self.routePointChanged.emit)
        self.web_bridge.routePointCleared.connect(self.routePointCleared.emit)
        self.web_bridge.routePointsCleared.connect(self.routePointsCleared.emit)
        self.web_bridge.routeGuidanceSelected.connect(
            self.routeGuidanceSelected.emit
        )
        self.web_bridge.routeHistorySelected.connect(
            self.routeHistorySelected.emit
        )
        self.web_bridge.routeHistoryLoadRequested.connect(
            self.routeHistoryLoadRequested.emit
        )
        self.web_bridge.routeHistoryImportRequested.connect(self.routeHistoryImportRequested.emit)
        self.web_bridge.routeHistoryBatchDeleteRequested.connect(self.routeHistoryBatchDeleteRequested.emit)
        self.web_bridge.routeHistoryDeleteRequested.connect(
            self.routeHistoryDeleteRequested.emit
        )
        self.web_bridge.routeHistoryExportRequested.connect(
            self.routeHistoryExportRequested.emit
        )
        self.web_bridge.routeHistoryRefreshRequested.connect(
            self.routeHistoryRefreshRequested.emit
        )
        self.web_bridge.localSearchRequested.connect(
            self.localSearchRequested.emit
        )
        self.web_bridge.fullScreenRequested.connect(self.toggle_full_screen)
        self.web_bridge.viewerReloadRequested.connect(self.reload_viewer)

        self.web_channel = QWebChannel(self.web_view.page())
        self.web_channel.registerObject("qgisBridge", self.web_bridge)
        self.web_view.page().setWebChannel(self.web_channel)

    def _configure_external_browser_fallback(self, layout, container):
        message = QLabel(self.web_runtime_diagnostic, container)
        message.setWordWrap(True)
        layout.addWidget(message)

        self.fallback_coordinate_label = QLabel(
            "QGIS 캔버스 중심 좌표를 기다리는 중입니다.",
            container,
        )
        self.fallback_coordinate_label.setWordWrap(True)
        layout.addWidget(self.fallback_coordinate_label)

        button_row = QHBoxLayout()
        self.fallback_external_button = QPushButton("외부 연동 창 열기", container)
        self.fallback_external_button.clicked.connect(
            self.externalViewerRequested.emit
        )
        button_row.addWidget(self.fallback_external_button)

        self.fallback_map_button = QPushButton("네이버 지도 열기", container)
        self.fallback_map_button.setEnabled(False)
        self.fallback_map_button.clicked.connect(self.open_external_map)
        button_row.addWidget(self.fallback_map_button)

        self.fallback_roadview_button = QPushButton("로드뷰 열기", container)
        self.fallback_roadview_button.setEnabled(False)
        self.fallback_roadview_button.clicked.connect(
            self.open_external_roadview
        )
        button_row.addWidget(self.fallback_roadview_button)
        layout.addLayout(button_row)

        layout.addStretch(1)

    def _set_fallback_center(self, lon, lat):
        try:
            lon = float(lon)
            lat = float(lat)
        except (TypeError, ValueError):
            return

        if not math.isfinite(lon) or not math.isfinite(lat):
            return
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            return

        self.fallback_lon = lon
        self.fallback_lat = lat
        if self.fallback_coordinate_label is not None:
            self.fallback_coordinate_label.setText(
                "현재 QGIS 중심 좌표: "
                f"EPSG:4326 {lat:.8f}, {lon:.8f}"
            )
        for button in (self.fallback_map_button, self.fallback_roadview_button):
            if button is not None:
                button.setEnabled(True)

    def open_external_map(self):
        if self.fallback_lon is None or self.fallback_lat is None:
            return

        url = QUrl(
            "https://map.naver.com/link/map/"
            f"Naver%20QGIS%20Bridge,{self.fallback_lat:.8f},"
            f"{self.fallback_lon:.8f}"
        )
        QDesktopServices.openUrl(url)

    def open_external_roadview(self):
        if self.fallback_lon is None or self.fallback_lat is None:
            return

        url = QUrl(
            "https://map.naver.com/link/roadview/"
            f"{self.fallback_lat:.8f},{self.fallback_lon:.8f}"
        )
        QDesktopServices.openUrl(url)

    def _load_viewer(self):
        html = build_viewer_html(naver_javascript_key())

        self.web_view.setHtml(html, QUrl(naver_map_base_url()))

