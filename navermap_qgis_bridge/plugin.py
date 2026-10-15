# SPDX-License-Identifier: GPL-2.0-or-later
"""Plugin entry point, lifecycle, settings and viewer wiring."""

from qgis.core import QgsMessageLog, QgsProject
from qgis.PyQt.QtCore import QTimer, Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtNetwork import QNetworkAccessManager
from qgis.PyQt.QtWidgets import QInputDialog, QLineEdit, QMessageBox
from .compat import MSG_WARNING
from .dock_widget import NaverMapDockWidget
from .data_transforms import safe_float, safe_number
from .external_bridge import NaverExternalBridgeServer
from .viewer_messages import ViewerMessages
from .api_transport import ApiTransport
from .settings import (
    PLUGIN_DIR,
    environment_api_hub_client_id,
    environment_api_hub_client_secret,
    environment_javascript_key,
    environment_rest_api_key,
    naver_javascript_key_source,
    legacy_file_javascript_key,
    save_javascript_key,
    save_api_hub_client_id,
    save_api_hub_client_secret,
    save_rest_api_key,
    stored_api_hub_client_id,
    stored_api_hub_client_secret,
    stored_javascript_key,
    stored_rest_api_key,
)
from .constants import MENU_NAME, LOG_TAG
try:
    from qgis.PyQt.QtGui import QAction
except ImportError:
    from qgis.PyQt.QtWidgets import QAction
from .search_routes import SearchRouteMixin
from .route_history import RouteHistoryMixin
from .history_exports import HistoryExportMixin
from .map_layers import MapLayersMixin
from .canvas_sync import CanvasSyncMixin


class NaverMapQgisBridgePlugin(
    SearchRouteMixin,
    RouteHistoryMixin,
    HistoryExportMixin,
    MapLayersMixin,
    CanvasSyncMixin,
):
    def __init__(self, iface):
        self.iface = iface
        self.project_epoch = 0
        self.project_transitioning = False
        self.action = None
        self.settings_action = None
        self.rest_settings_action = None
        self.api_hub_client_id_action = None
        self.api_hub_client_secret_action = None
        self.load_history_action = None
        self.load_gpx_action = None
        self.save_history_action = None
        self.export_geojson_action = None
        self.export_shapefile_action = None
        self.export_gpx_action = None
        self.dock = None
        self.roadview_layer = None
        self.roadview_feature_id = None
        self.route_layer = None
        self.route_guidance_layer = None
        self.route_guidance_feature_ids = {}
        self.route_points_layer = None
        self.route_point_feature_ids = {}
        self.route_history_layer = None
        self.guidance_history_layer = None
        self.active_route_history_id = None
        self.network_manager = QNetworkAccessManager()
        self.api_transport = ApiTransport(self.network_manager, QTimer.singleShot)
        self.canvas_sync_connected = False
        self.last_canvas_view = None
        self.canvas_sync_timer = QTimer()
        self.canvas_sync_timer.setSingleShot(True)
        self.canvas_sync_timer.setInterval(350)
        self.canvas_sync_timer.timeout.connect(self._sync_canvas_center)
        self.reverse_sync_guard_timer = QTimer()
        self.reverse_sync_guard_timer.setSingleShot(True)
        self.reverse_sync_guard_timer.setInterval(600)
        self.external_bridge_server = None
        self.viewer_messages = ViewerMessages(
            lambda: self.dock, lambda: self.external_bridge_server
        )
        self.external_bridge_timer = QTimer()
        self.external_bridge_timer.setInterval(120)
        self.external_bridge_timer.timeout.connect(
            self._process_external_bridge_events
        )

    @property
    def route_reply(self):
        return self.api_transport.route_reply

    @route_reply.setter
    def route_reply(self, value):
        self.api_transport.route_reply = value

    @property
    def local_search_replies(self):
        return self.api_transport.search_replies

    def initGui(self):
        project = QgsProject.instance()
        project.aboutToBeCleared.connect(self._begin_project_transition)
        project.cleared.connect(self._finish_project_transition)
        self.action = QAction(
            QIcon(str(PLUGIN_DIR / "icon.png")),
            "Naver Map / Street View",
            self.iface.mainWindow(),
        )
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle_dock)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(MENU_NAME, self.action)

        self.settings_action = QAction(
            QIcon.fromTheme("configure"),
            "Naver Maps Client ID 설정...",
            self.iface.mainWindow(),
        )
        self.settings_action.triggered.connect(self._configure_api_key)
        self.iface.addPluginToMenu(MENU_NAME, self.settings_action)

        self.rest_settings_action = QAction(
            QIcon.fromTheme("dialog-password"),
            "Naver Maps Client Secret 설정...",
            self.iface.mainWindow(),
        )
        self.rest_settings_action.triggered.connect(self._configure_rest_api_key)
        self.iface.addPluginToMenu(MENU_NAME, self.rest_settings_action)

        self.api_hub_client_id_action = QAction(
            QIcon.fromTheme("configure"),
            "Naver API HUB Client ID 설정...",
            self.iface.mainWindow(),
        )
        self.api_hub_client_id_action.triggered.connect(
            self._configure_api_hub_client_id
        )
        self.iface.addPluginToMenu(MENU_NAME, self.api_hub_client_id_action)

        self.api_hub_client_secret_action = QAction(
            QIcon.fromTheme("dialog-password"),
            "Naver API HUB Client Secret 설정...",
            self.iface.mainWindow(),
        )
        self.api_hub_client_secret_action.triggered.connect(
            self._configure_api_hub_client_secret
        )
        self.iface.addPluginToMenu(MENU_NAME, self.api_hub_client_secret_action)

        self.load_history_action = QAction(
            QIcon.fromTheme("document-open"),
            "경로 이력 불러오기...",
            self.iface.mainWindow(),
        )
        self.load_history_action.triggered.connect(self._load_route_history_file)
        self.iface.addPluginToMenu(MENU_NAME, self.load_history_action)

        self.load_gpx_action = QAction(
            QIcon.fromTheme("document-open"),
            "GPX 스타일 적용해서 불러오기...",
            self.iface.mainWindow(),
        )
        self.load_gpx_action.triggered.connect(self._load_styled_gpx)
        self.iface.addPluginToMenu(MENU_NAME, self.load_gpx_action)

        self.save_history_action = QAction(
            QIcon.fromTheme("document-save-as"),
            "경로 이력 GeoPackage 저장...",
            self.iface.mainWindow(),
        )
        self.save_history_action.setEnabled(False)
        self.save_history_action.triggered.connect(
            self._save_route_history_geopackage
        )
        self.iface.addPluginToMenu(MENU_NAME, self.save_history_action)

        self.export_geojson_action = QAction(
            QIcon.fromTheme("document-export"),
            "경로·안내 이력 GeoJSON 내보내기...",
            self.iface.mainWindow(),
        )
        self.export_geojson_action.setEnabled(False)
        self.export_geojson_action.triggered.connect(
            self._export_route_history_geojson
        )
        self.iface.addPluginToMenu(MENU_NAME, self.export_geojson_action)

        self.export_shapefile_action = QAction(
            QIcon.fromTheme("document-export"),
            "경로·안내 이력 Shapefile 내보내기...",
            self.iface.mainWindow(),
        )
        self.export_shapefile_action.setEnabled(False)
        self.export_shapefile_action.triggered.connect(
            self._export_route_history_shapefile
        )
        self.iface.addPluginToMenu(MENU_NAME, self.export_shapefile_action)

        self.export_gpx_action = QAction(
            QIcon.fromTheme("document-export"),
            "경로·안내 이력 GPX 내보내기...",
            self.iface.mainWindow(),
        )
        self.export_gpx_action.setEnabled(False)
        self.export_gpx_action.triggered.connect(
            self._export_route_history_gpx
        )
        self.iface.addPluginToMenu(MENU_NAME, self.export_gpx_action)

    def unload(self):
        project = QgsProject.instance()
        project.aboutToBeCleared.disconnect(self._begin_project_transition)
        project.cleared.disconnect(self._finish_project_transition)
        self.project_epoch += 1
        self.project_transitioning = True
        self._deactivate_canvas_sync()

        if self.action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

        if self.settings_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.settings_action)
            self.settings_action = None

        if self.rest_settings_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.rest_settings_action)
            self.rest_settings_action = None

        if self.api_hub_client_id_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.api_hub_client_id_action)
            self.api_hub_client_id_action = None

        if self.api_hub_client_secret_action is not None:
            self.iface.removePluginMenu(
                MENU_NAME,
                self.api_hub_client_secret_action,
            )
            self.api_hub_client_secret_action = None

        if self.load_history_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.load_history_action)
            self.load_history_action = None

        if self.load_gpx_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.load_gpx_action)
            self.load_gpx_action = None

        if self.save_history_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.save_history_action)
            self.save_history_action = None

        if self.export_geojson_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.export_geojson_action)
            self.export_geojson_action = None

        if self.export_shapefile_action is not None:
            self.iface.removePluginMenu(
                MENU_NAME,
                self.export_shapefile_action,
            )
            self.export_shapefile_action = None

        if self.export_gpx_action is not None:
            self.iface.removePluginMenu(MENU_NAME, self.export_gpx_action)
            self.export_gpx_action = None

        self.api_transport.close()

        self._stop_external_bridge()

        if self.dock is not None:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None

        self._remove_roadview_layer()
        self._remove_route_layer()
        self._remove_route_guidance_layer()
        self._remove_route_points_layer()
        self.route_history_layer = None
        self.guidance_history_layer = None

    def toggle_dock(self, checked):
        if checked:
            self._show_dock()
        else:
            self._hide_dock()

    def _begin_project_transition(self):
        self.project_epoch += 1
        self.project_transitioning = True
        self.api_transport.close()
        self.canvas_sync_timer.stop()
        self.reverse_sync_guard_timer.stop()
        if self.external_bridge_server is not None:
            self.external_bridge_server.reset_project(self.project_epoch, accepting=False)

    def _finish_project_transition(self):
        self.last_canvas_view = None
        # Project-owned layers have been deleted; session history layers are unregistered.
        self.roadview_layer = self.route_layer = self.route_guidance_layer = None
        self.route_points_layer = None
        self.roadview_feature_id = None
        self.route_guidance_feature_ids = {}
        self.route_point_feature_ids = {}
        self.active_route_history_id = None
        if self.dock is not None:
            self.dock.reset_project(self.project_epoch)
        if self.external_bridge_server is not None:
            self.external_bridge_server.reset_project(self.project_epoch, accepting=True)
        self.project_transitioning = False
        self._sync_route_history_panel()
        self._schedule_canvas_sync()

    def _show_dock(self):
        if not self._ensure_api_key():
            if self.action is not None:
                self.action.setChecked(False)
            return

        self._ensure_dock()
        self.dock.show()
        self.dock.raise_()
        self._activate_canvas_sync()

    def _ensure_api_key(self):
        source = naver_javascript_key_source()
        if source in ("environment", "qgis"):
            return True

        # Offer the old settings.json value as a one-time migration path.
        initial_value = legacy_file_javascript_key() if source == "file" else ""
        return self._prompt_and_save_api_key(initial_value)

    def _configure_api_key(self, _checked=False):
        if environment_javascript_key():
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "현재 환경변수 NAVER_MAP_CLIENT_ID가 우선 적용되고 있습니다. "
                "환경변수를 변경한 뒤 QGIS를 다시 시작해 주세요.",
            )
            return

        initial_value = stored_javascript_key() or legacy_file_javascript_key()
        if self._prompt_and_save_api_key(initial_value):
            if self.dock is not None:
                self.dock.reload_viewer()
            self.iface.messageBar().pushSuccess(
                "Naver Map QGIS Bridge",
                "Naver Maps Client ID를 저장하고 뷰어를 다시 불러왔습니다.",
            )

    def _prompt_and_save_api_key(self, initial_value=""):
        value, accepted = QInputDialog.getText(
            self.iface.mainWindow(),
            "Naver Maps Client ID",
            "NAVER Cloud Platform에서 발급한 Client ID를 입력하세요:",
            QLineEdit.EchoMode.Password,
            initial_value,
        )
        if not accepted:
            return False

        value = value.strip()
        if not value:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "Client ID를 입력해야 지도를 불러올 수 있습니다.",
            )
            return False

        try:
            save_javascript_key(value)
        except ValueError as exc:
            QMessageBox.warning(self.iface.mainWindow(), "Naver Map QGIS Bridge", str(exc))
            return False
        return True

    def _configure_rest_api_key(self, _checked=False):
        if environment_rest_api_key():
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "현재 환경변수 NAVER_MAP_CLIENT_SECRET이 우선 적용되고 있습니다. "
                "환경변수를 변경한 뒤 QGIS를 다시 시작해 주세요.",
            )
            return

        if self._prompt_and_save_rest_api_key(stored_rest_api_key()):
            self.iface.messageBar().pushSuccess(
                "Naver Map QGIS Bridge",
                "Naver Maps Client Secret을 저장했습니다.",
            )

    def _prompt_and_save_rest_api_key(self, initial_value=""):
        value, accepted = QInputDialog.getText(
            self.iface.mainWindow(),
            "Naver Maps Client Secret",
            "NAVER Cloud Platform에서 발급한 Client Secret을 입력하세요:",
            QLineEdit.EchoMode.Password,
            initial_value,
        )
        if not accepted:
            return False

        value = value.strip()
        if not value:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "Client Secret을 입력해야 경로를 탐색할 수 있습니다.",
            )
            return False

        try:
            save_rest_api_key(value)
        except ValueError as exc:
            QMessageBox.warning(self.iface.mainWindow(), "Naver Map QGIS Bridge", str(exc))
            return False
        return True

    def _configure_api_hub_client_id(self, _checked=False):
        if environment_api_hub_client_id():
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "현재 환경변수 NAVER_API_HUB_CLIENT_ID가 우선 적용되고 있습니다. "
                "환경변수를 변경한 뒤 QGIS를 다시 시작해 주세요.",
            )
            return

        if self._prompt_and_save_api_hub_client_id(stored_api_hub_client_id()):
            self.iface.messageBar().pushSuccess(
                "Naver Map QGIS Bridge",
                "Naver API HUB Client ID를 저장했습니다.",
            )

    def _prompt_and_save_api_hub_client_id(self, initial_value=""):
        value, accepted = QInputDialog.getText(
            self.iface.mainWindow(),
            "Naver API HUB Client ID",
            "NAVER API HUB에서 발급한 Client ID를 입력하세요:",
            QLineEdit.EchoMode.Password,
            initial_value,
        )
        if not accepted:
            return False

        value = value.strip()
        if not value:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "API HUB Client ID를 입력해야 POI 검색을 사용할 수 있습니다.",
            )
            return False

        try:
            save_api_hub_client_id(value)
        except ValueError as exc:
            QMessageBox.warning(self.iface.mainWindow(), "Naver Map QGIS Bridge", str(exc))
            return False
        return True

    def _configure_api_hub_client_secret(self, _checked=False):
        if environment_api_hub_client_secret():
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "현재 환경변수 NAVER_API_HUB_CLIENT_SECRET이 우선 적용되고 있습니다. "
                "환경변수를 변경한 뒤 QGIS를 다시 시작해 주세요.",
            )
            return

        if self._prompt_and_save_api_hub_client_secret(
            stored_api_hub_client_secret()
        ):
            self.iface.messageBar().pushSuccess(
                "Naver Map QGIS Bridge",
                "Naver API HUB Client Secret을 저장했습니다.",
            )

    def _prompt_and_save_api_hub_client_secret(self, initial_value=""):
        value, accepted = QInputDialog.getText(
            self.iface.mainWindow(),
            "Naver API HUB Client Secret",
            "NAVER API HUB에서 발급한 Client Secret을 입력하세요:",
            QLineEdit.EchoMode.Password,
            initial_value,
        )
        if not accepted:
            return False

        value = value.strip()
        if not value:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "API HUB Client Secret을 입력해야 POI 검색을 사용할 수 있습니다.",
            )
            return False

        try:
            save_api_hub_client_secret(value)
        except ValueError as exc:
            QMessageBox.warning(self.iface.mainWindow(), "Naver Map QGIS Bridge", str(exc))
            return False
        return True

    def _hide_dock(self):
        if self.dock is not None:
            self.dock.hide()
        self._deactivate_canvas_sync()

    def _ensure_dock(self):
        if self.dock is not None:
            return

        self.dock = NaverMapDockWidget(self.iface.mainWindow())
        self.dock.centerRequested.connect(self._handle_viewer_moved)
        self.dock.zoomRequested.connect(self._handle_viewer_zoomed)
        self.dock.roadviewStateChanged.connect(self._update_roadview_layer)
        self.dock.routeRequested.connect(self._request_route)
        self.dock.routeCancelRequested.connect(self._cancel_route)
        self.dock.routePointChanged.connect(self._set_route_point)
        self.dock.routePointCleared.connect(self._clear_route_point)
        self.dock.routePointsCleared.connect(self._clear_route_points)
        self.dock.routeGuidanceSelected.connect(self._focus_route_guidance)
        self.dock.routeHistorySelected.connect(self._focus_route_history)
        self.dock.routeHistoryLoadRequested.connect(self._load_route_history)
        self.dock.routeHistoryDeleteRequested.connect(self._delete_route_history)
        self.dock.routeHistoryExportRequested.connect(self._export_single_route_history)
        self.dock.routeHistoryRefreshRequested.connect(
            self._refresh_route_history_panel
        )
        self.dock.localSearchRequested.connect(self._request_local_search)
        self.dock.externalViewerRequested.connect(self._open_external_viewer)
        self.dock.visibilityChanged.connect(self._sync_action_state)
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        if self.dock.web_runtime_diagnostic:
            self._ensure_external_bridge()
            QgsMessageLog.logMessage(
                self.dock.web_runtime_diagnostic,
                LOG_TAG,
                MSG_WARNING,
            )
        QTimer.singleShot(800, self._sync_route_history_panel)

    def _ensure_external_bridge(self):
        if self.external_bridge_server is None:
            self.external_bridge_server = NaverExternalBridgeServer()
            try:
                self.external_bridge_server.start()
                self.external_bridge_server.reset_project(self.project_epoch)
            except OSError as exc:
                QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)
                # Keep each QGIS instance on its own loopback socket.
                self.external_bridge_server = NaverExternalBridgeServer(port=0)
                try:
                    self.external_bridge_server.start()
                    self.external_bridge_server.reset_project(self.project_epoch)
                except OSError:
                    self.iface.messageBar().pushWarning(
                        "Naver Map QGIS Bridge",
                        "외부 브라우저 연동 서버를 시작하지 못했습니다. 로컬 포트 접근 권한을 확인하세요.",
                    )
                    self.external_bridge_server = None
                    return None
                self.iface.messageBar().pushInfo(
                    "Naver Map QGIS Bridge", "기본 포트를 사용할 수 없어 외부 연동에 별도 포트를 사용합니다."
                )

        if not self.external_bridge_timer.isActive():
            self.external_bridge_timer.start()
        return self.external_bridge_server

    def _stop_external_bridge(self):
        self.external_bridge_timer.stop()
        if self.external_bridge_server is not None:
            self.external_bridge_server.stop()
            self.external_bridge_server = None

    def _open_external_viewer(self):
        server = self._ensure_external_bridge()
        if server is None:
            return

        self.last_canvas_view = None
        self._schedule_canvas_sync()
        QDesktopServices.openUrl(QUrl(server.url))

    def _process_external_bridge_events(self):
        if self.external_bridge_server is None or getattr(self, "_processing_external_events", False):
            return

        self._processing_external_events = True
        try:
            for _ in range(32):
                if self.external_bridge_server is None:
                    break
                event = self.external_bridge_server.next_event()
                if event is None:
                    break
                if self.project_transitioning or event.get("epoch") != self.project_epoch:
                    continue
                payload = event.get("payload", {})
                event_type = event.get("type")
                try:
                    if event_type == "move_center":
                        self._handle_viewer_moved(
                            float(payload.get("lon")),
                            float(payload.get("lat")),
                        )
                    elif event_type == "zoom_view":
                        self._handle_viewer_zoomed(float(payload.get("lon")), float(payload.get("lat")),
                                                  float(payload.get("meters_per_pixel")))
                    elif event_type == "roadview_state":
                        self._update_roadview_layer(
                            float(payload.get("lon")),
                            float(payload.get("lat")),
                            float(payload.get("pan")),
                            float(payload.get("tilt")),
                            float(payload.get("zoom")),
                            str(payload.get("pano_id", "")),
                        )
                    elif event_type == "request_route":
                        self._request_route(
                            float(payload.get("origin_lon")),
                            float(payload.get("origin_lat")),
                            float(payload.get("destination_lon")),
                            float(payload.get("destination_lat")),
                            str(payload.get("priority", "")),
                            str(payload.get("waypoints_json", "")),
                            str(payload.get("avoid_json", "")),
                            str(payload.get("vehicle_json", "")),
                            str(payload.get("origin_label", "")),
                            str(payload.get("destination_label", "")),
                        )
                    elif event_type == "cancel_route":
                        self._cancel_route()
                    elif event_type == "route_point":
                        self._set_route_point(
                            str(payload.get("role", "")),
                            float(payload.get("lon")),
                            float(payload.get("lat")),
                        )
                    elif event_type == "clear_route_point":
                        self._clear_route_point(str(payload.get("role", "")))
                    elif event_type == "clear_route_points":
                        self._clear_route_points()
                    elif event_type == "request_local_search":
                        self._request_local_search(
                            str(payload.get("request_id", "")),
                            str(payload.get("query", "")),
                        )
                    elif event_type == "select_route_guidance":
                        self._focus_route_guidance(
                            int(payload.get("sequence")),
                            float(payload.get("lon")),
                            float(payload.get("lat")),
                        )
                    elif event_type == "select_route_history":
                        self._focus_route_history(str(payload.get("history_id", "")))
                    elif event_type == "load_route_history":
                        self._load_route_history(str(payload.get("history_id", "")))
                    elif event_type == "delete_route_history":
                        self._delete_route_history(str(payload.get("history_id", "")))
                    elif event_type == "export_route_history":
                        self._export_single_route_history(
                            str(payload.get("history_id", ""))
                        )
                    elif event_type == "refresh_route_history":
                        self._refresh_route_history_panel()
                except Exception as exc:
                    QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)
                    if event_type == "request_route":
                        self._set_route_status(
                            False,
                            "외부 브라우저의 경로 요청을 처리하지 못했습니다.",
                        )

        finally:
            self._processing_external_events = False

    def _sync_action_state(self, visible):
        if self.action is not None:
            self.action.setChecked(visible)

        if visible:
            self._activate_canvas_sync()
        else:
            self._deactivate_canvas_sync()

    @staticmethod
    def _safe_number(value):
        return safe_number(value)

    @staticmethod
    def _safe_float(value):
        return safe_float(value)

    def _set_route_status(self, success, message):
        self.viewer_messages.route_status(success, message)
