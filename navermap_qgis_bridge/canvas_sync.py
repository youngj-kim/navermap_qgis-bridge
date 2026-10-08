# SPDX-License-Identifier: GPL-2.0-or-later
"""CanvasSyncMixin: behavior-preserving host methods; state is owned by the plugin."""

import math
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
)
from .compat import MSG_WARNING
from .constants import LOG_TAG


class CanvasSyncMixin:
    def _activate_canvas_sync(self):
        canvas = self.iface.mapCanvas()

        if not self.canvas_sync_connected:
            canvas.extentsChanged.connect(self._schedule_canvas_sync)
            canvas.destinationCrsChanged.connect(self._schedule_canvas_sync)
            self.canvas_sync_connected = True
            if self.dock is not None and self.dock.web_view is None:
                self.iface.messageBar().pushInfo(
                    "Naver Map QGIS Bridge",
                    "외부 브라우저 모드입니다. QGIS 중심 좌표를 기준으로 Naver Map/거리뷰를 열 수 있습니다.",
                )
            else:
                self.iface.messageBar().pushInfo(
                    "Naver Map QGIS Bridge",
                    "QGIS 이동은 Naver에, 거리뷰 위치 이동은 QGIS에 양방향으로 반영됩니다.",
                )

        self._schedule_canvas_sync()

    def _deactivate_canvas_sync(self):
        canvas = self.iface.mapCanvas()

        self.canvas_sync_timer.stop()
        self.reverse_sync_guard_timer.stop()
        if self.canvas_sync_connected:
            for signal in (canvas.extentsChanged, canvas.destinationCrsChanged):
                try:
                    signal.disconnect(self._schedule_canvas_sync)
                except (RuntimeError, TypeError):
                    pass
            self.canvas_sync_connected = False

    def _schedule_canvas_sync(self, *_args):
        if self.dock is None or not self.dock.isVisible():
            return
        if self.reverse_sync_guard_timer.isActive():
            return
        self.canvas_sync_timer.start()

    def _sync_canvas_center(self):
        if self.dock is None or not self.dock.isVisible():
            return

        canvas = self.iface.mapCanvas()
        try:
            lon, lat = self._to_epsg_4326(canvas.center())
        except Exception as exc:
            QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)
            self.iface.messageBar().pushWarning(
                "Naver Map QGIS Bridge",
                "QGIS 지도 중심 좌표를 EPSG:4326으로 변환하지 못했습니다.",
            )
            return

        self.dock.set_center(lon, lat)
        if self.external_bridge_server is not None:
            self.external_bridge_server.set_center(lon, lat)

    def _handle_viewer_moved(self, lon, lat):
        if self.dock is not None:
            self.dock.set_reverse_sync_status(
                f"Python 처리 시작: {lat:.6f}, {lon:.6f}"
            )
        if not math.isfinite(lon) or not math.isfinite(lat):
            if self.dock is not None:
                self.dock.set_reverse_sync_status("Python 거부: 유효하지 않은 좌표")
            return
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            if self.dock is not None:
                self.dock.set_reverse_sync_status("Python 거부: 좌표 범위 오류")
            return

        canvas = self.iface.mapCanvas()
        source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        target_crs = canvas.mapSettings().destinationCrs()

        try:
            transform = QgsCoordinateTransform(
                source_crs,
                target_crs,
                QgsProject.instance(),
            )
            center = transform.transform(QgsPointXY(lon, lat))
        except Exception as exc:
            QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)
            self.iface.messageBar().pushWarning(
                "Naver Map QGIS Bridge",
                "Naver 지도/Roadview 좌표를 QGIS 프로젝트 좌표계로 변환하지 못했습니다.",
            )
            if self.dock is not None:
                self.dock.set_reverse_sync_status(
                    f"QGIS 적용 실패: {exc}"
                )
            return

        self.canvas_sync_timer.stop()
        self.reverse_sync_guard_timer.start()
        canvas.setCenter(center)
        canvas.refresh()
        if self.dock is not None:
            applied = canvas.center()
            self.dock.set_reverse_sync_status(
                "QGIS 적용 완료: "
                f"{applied.x():.3f}, {applied.y():.3f} ({target_crs.authid()})"
            )

    def _to_epsg_4326(self, point):
        canvas = self.iface.mapCanvas()
        source_crs = canvas.mapSettings().destinationCrs()
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
        transformed = transform.transform(point)
        return transformed.x(), transformed.y()
