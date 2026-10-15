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
from .view_scale import ground_distance


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
        if self.project_transitioning:
            return
        if self.dock is None or not self.dock.isVisible():
            return
        if self.reverse_sync_guard_timer.isActive():
            self.canvas_sync_timer.start(self.reverse_sync_guard_timer.remainingTime() + 1)
            return
        self.canvas_sync_timer.setInterval(350)
        self.canvas_sync_timer.start()

    def _sync_canvas_center(self):
        if self.project_transitioning:
            return
        if self.dock is None or not self.dock.isVisible():
            return

        canvas = self.iface.mapCanvas()
        try:
            lon, lat = self._to_epsg_4326(canvas.center())
            resolution = self._canvas_ground_resolution()
        except Exception as exc:
            QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)
            if not getattr(self, "_canvas_transform_warning", False):
                self.iface.messageBar().pushWarning(
                    "Naver Map QGIS Bridge",
                    "QGIS 지도 중심 좌표를 EPSG:4326으로 변환하지 못했습니다.",
                )
            self._canvas_transform_warning = True
            return

        self._canvas_transform_warning = False

        view = (lon, lat, abs(canvas.mapUnitsPerPixel()), canvas.mapSettings().destinationCrs().authid())
        previous = self.last_canvas_view
        if previous == view:
            return
        preserve = previous is not None and (previous[3] != view[3] or not math.isclose(previous[2], view[2], rel_tol=1e-7))
        self.last_canvas_view = view
        self.dock.set_view(lon, lat, resolution, preserve)
        if self.external_bridge_server is not None:
            self.external_bridge_server.set_view(lon, lat, resolution, preserve)

    def _canvas_ground_resolution(self, center=None):
        canvas = self.iface.mapCanvas()
        center = canvas.center() if center is None else center
        span = abs(canvas.mapUnitsPerPixel()) * 64
        first = self._to_epsg_4326(QgsPointXY(center.x() - span, center.y()))
        second = self._to_epsg_4326(QgsPointXY(center.x() + span, center.y()))
        resolution = ground_distance(first, second) / 128
        if not math.isfinite(resolution) or resolution <= 0:
            raise ValueError("지도 축척을 계산하지 못했습니다.")
        return resolution

    def _handle_viewer_zoomed(self, lon, lat, meters_per_pixel):
        if self.project_transitioning:
            return
        if (not all(math.isfinite(value) for value in (lon, lat, meters_per_pixel))
                or not -180 <= lon <= 180 or not -90 <= lat <= 90
                or not 0.001 <= meters_per_pixel <= 1000000):
            return
        canvas = self.iface.mapCanvas()
        try:
            target_crs = canvas.mapSettings().destinationCrs()
            transform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), target_crs, QgsProject.instance())
            center = transform.transform(QgsPointXY(lon, lat))
            resolution = self._canvas_ground_resolution(center)
            self.canvas_sync_timer.stop()
            self.reverse_sync_guard_timer.start()
            canvas.zoomByFactor(meters_per_pixel / resolution, center)
            canvas.refresh()
            actual_lon, actual_lat = self._to_epsg_4326(canvas.center())
            self.last_canvas_view = (actual_lon, actual_lat, abs(canvas.mapUnitsPerPixel()), target_crs.authid())
        except Exception as exc:
            QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)

    def _handle_viewer_moved(self, lon, lat):
        if self.project_transitioning:
            return
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
        actual_lon, actual_lat = self._to_epsg_4326(canvas.center())
        self.last_canvas_view = (actual_lon, actual_lat, abs(canvas.mapUnitsPerPixel()), target_crs.authid())
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
