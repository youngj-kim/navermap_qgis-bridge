# SPDX-License-Identifier: GPL-2.0-or-later
"""MapLayersMixin: behavior-preserving host methods; state is owned by the plugin."""

import math
from base64 import b64encode
from functools import lru_cache
from qgis.core import (
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
    QgsProperty,
    QgsRendererCategory,
    QgsSvgMarkerSymbolLayer,
    QgsVectorLayer,
)
from .compat import MSG_WARNING
from .data_transforms import guidance_category
from .settings import PLUGIN_DIR
from .constants import LOG_TAG, ROUTE_CAR_TYPES


class MapLayersMixin:
    def _update_roadview_layer(self, lon, lat, pan, tilt, zoom, pano_id):
        if self.project_transitioning:
            return
        values = (lon, lat, pan, tilt, zoom)
        if not all(math.isfinite(value) for value in values):
            return
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            return

        layer = self._ensure_roadview_layer()
        provider = layer.dataProvider()
        geometry = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
        attributes = [pano_id, lon, lat, pan, tilt, zoom]

        feature_valid = (
            self.roadview_feature_id is not None
            and layer.getFeature(self.roadview_feature_id).isValid()
        )
        if not feature_valid:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(geometry)
            feature.setAttributes(attributes)
            if provider.addFeature(feature):
                self.roadview_feature_id = feature.id()
        else:
            provider.changeGeometryValues(
                {self.roadview_feature_id: geometry}
            )
            provider.changeAttributeValues(
                {
                    self.roadview_feature_id: {
                        index: value
                        for index, value in enumerate(attributes)
                    }
                }
            )

        layer.updateExtents()
        layer.triggerRepaint()

    def _ensure_roadview_layer(self):
        project = QgsProject.instance()
        if self.roadview_layer is not None:
            try:
                if project.mapLayer(self.roadview_layer.id()) is not None:
                    return self.roadview_layer
            except RuntimeError:
                pass

        uri = (
            "Point?crs=EPSG:4326"
            "&field=pano_id:string(32)"
            "&field=longitude:double"
            "&field=latitude:double"
            "&field=pan:double"
            "&field=tilt:double"
            "&field=zoom:double"
        )
        layer = QgsVectorLayer(uri, "Naver Street View Position", "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)

        svg_path = PLUGIN_DIR / "web" / "roadview_radar.svg"
        symbol = QgsMarkerSymbol(
            [QgsSvgMarkerSymbolLayer(str(svg_path), 24.0)]
        )
        symbol.setDataDefinedAngle(QgsProperty.fromField("pan"))
        layer.renderer().setSymbol(symbol)

        project.addMapLayer(layer)
        self.roadview_layer = layer
        self.roadview_feature_id = None
        return layer

    def _remove_roadview_layer(self):
        if self.roadview_layer is None:
            return

        project = QgsProject.instance()
        try:
            layer_id = self.roadview_layer.id()
            if project.mapLayer(layer_id) is not None:
                project.removeMapLayer(layer_id)
        except RuntimeError:
            pass
        self.roadview_layer = None
        self.roadview_feature_id = None

    @staticmethod
    def _guidance_category(guide_type, guidance):
        return guidance_category(guide_type, guidance)

    @staticmethod
    def _route_result_summary(
        distance,
        duration,
        car_type,
        guidance_count,
    ):
        duration_minutes = max(1, round(duration / 60))
        distance_km = distance / 1000
        car_label = ROUTE_CAR_TYPES.get(car_type, str(car_type))
        return (
            f"{duration_minutes}분 · {distance_km:.1f} km · "
            f"{car_label} · 안내 {guidance_count}개"
        )

    def _create_route_layer(
        self,
        points,
        distance,
        duration,
        guidance_count,
        result_summary,
        priority,
        waypoint_count,
        avoid_options,
        vehicle_options,
    ):
        self._remove_route_layer()

        uri = (
            "LineString?crs=EPSG:4326"
            "&field=distance_m:integer"
            "&field=duration_s:integer"
            "&field=guidance_count:integer"
            "&field=result_summary:string(255)"
            "&field=priority:string(16)"
            "&field=waypoint_count:integer"
            "&field=avoid:string(128)"
            "&field=car_type:integer"
            "&field=car_fuel:string(16)"
            "&field=car_hipass:integer"
        )
        layer = QgsVectorLayer(uri, "Naver Directions Route", "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)
        layer.renderer().setSymbol(self._route_line_symbol())

        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolylineXY(points))
        feature.setAttributes(
            [
                distance,
                duration,
                guidance_count,
                result_summary,
                priority,
                waypoint_count,
                "|".join(avoid_options),
                vehicle_options["car_type"],
                vehicle_options["car_fuel"],
                1 if vehicle_options["car_hipass"] else 0,
            ]
        )
        layer.dataProvider().addFeature(feature)
        layer.updateExtents()

        project = QgsProject.instance()
        project.addMapLayer(layer)
        self.route_layer = layer

        canvas = self.iface.mapCanvas()
        try:
            transform = QgsCoordinateTransform(
                layer.crs(),
                canvas.mapSettings().destinationCrs(),
                project,
            )
            extent = transform.transformBoundingBox(layer.extent())
            margin = max(extent.width(), extent.height()) * 0.08
            if margin > 0:
                extent.grow(margin)
            canvas.setExtent(extent)
        except Exception as exc:
            QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)
        canvas.refresh()

    def _remove_route_layer(self):
        if self.route_layer is None:
            return

        project = QgsProject.instance()
        try:
            layer_id = self.route_layer.id()
            if project.mapLayer(layer_id) is not None:
                project.removeMapLayer(layer_id)
        except RuntimeError:
            pass
        self.route_layer = None

    def _create_route_guidance_layer(self, guides):
        self._remove_route_guidance_layer()
        if not guides:
            return

        uri = (
            "Point?crs=EPSG:4326"
            "&field=route_id:string(64)"
            "&field=sequence:integer"
            "&field=section_no:integer"
            "&field=guide_type:integer"
            "&field=category:string(16)"
            "&field=guidance:string(255)"
            "&field=name:string(128)"
            "&field=distance_m:integer"
            "&field=duration_s:integer"
            "&field=cum_distance_m:integer"
            "&field=cum_duration_s:integer"
            "&field=road_index:integer"
            "&field=longitude:double"
            "&field=latitude:double"
        )
        layer = QgsVectorLayer(uri, "Naver Route Guidance", "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)
        layer.setRenderer(self._route_guidance_renderer())

        provider = layer.dataProvider()
        feature_ids = {}
        for guide in guides:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(
                QgsGeometry.fromPointXY(
                    QgsPointXY(guide["longitude"], guide["latitude"])
                )
            )
            feature.setAttributes(
                [
                    guide["route_id"],
                    guide["sequence"],
                    guide["section_no"],
                    guide["guide_type"],
                    guide["category"],
                    guide["guidance"],
                    guide["name"],
                    guide["distance_m"],
                    guide["duration_s"],
                    guide["cumulative_distance_m"],
                    guide["cumulative_duration_s"],
                    guide["road_index"],
                    guide["longitude"],
                    guide["latitude"],
                ]
            )
            if provider.addFeature(feature):
                feature_ids[guide["sequence"]] = feature.id()

        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)
        self.route_guidance_layer = layer
        self.route_guidance_feature_ids = feature_ids

    @staticmethod
    def _route_line_symbol():
        return QgsLineSymbol.createSimple(
            {
                "line_color": "#1976d2",
                "line_width": "1.4",
            }
        )

    def _route_guidance_renderer(self):
        return QgsCategorizedSymbolRenderer(
            "category",
            [
                QgsRendererCategory(
                    "start",
                    self._route_pin_symbol("route_origin_pin.svg", 7.5),
                    "출발",
                ),
                QgsRendererCategory(
                    "destination",
                    self._route_pin_symbol(
                        "route_destination_pin.svg",
                        7.5,
                    ),
                    "도착",
                ),
                QgsRendererCategory(
                    "waypoint",
                    self._route_pin_symbol("route_waypoint_pin.svg", 7.5),
                    "경유지",
                ),
                QgsRendererCategory(
                    "straight",
                    self._guidance_symbol("guidance_straight.svg"),
                    "직진",
                ),
                QgsRendererCategory(
                    "left",
                    self._guidance_symbol("guidance_left.svg"),
                    "좌회전",
                ),
                QgsRendererCategory(
                    "right",
                    self._guidance_symbol("guidance_right.svg"),
                    "우회전",
                ),
                QgsRendererCategory(
                    "uturn",
                    self._guidance_symbol("guidance_uturn.svg"),
                    "유턴",
                ),
                QgsRendererCategory(
                    "roundabout",
                    self._guidance_symbol("guidance_roundabout.svg"),
                    "회전교차로",
                ),
                QgsRendererCategory(
                    "transition",
                    self._guidance_symbol("guidance_transition.svg"),
                    "진출입",
                ),
                QgsRendererCategory(
                    "other",
                    self._guidance_symbol("guidance_other.svg"),
                    "기타 안내",
                ),
            ],
        )

    @staticmethod
    def _guidance_symbol(filename):
        return QgsMarkerSymbol(
            [
                QgsSvgMarkerSymbolLayer(
                    MapLayersMixin._embedded_svg_path(filename),
                    6.5,
                )
            ]
        )

    def _focus_route_guidance(self, sequence, lon, lat):
        if not math.isfinite(lon) or not math.isfinite(lat):
            return
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            return

        if self.route_guidance_layer is not None:
            try:
                feature_id = self.route_guidance_feature_ids.get(sequence)
                self.route_guidance_layer.removeSelection()
                if feature_id is not None:
                    self.route_guidance_layer.selectByIds([feature_id])
            except RuntimeError:
                self.route_guidance_layer = None
                self.route_guidance_feature_ids = {}

        self._handle_viewer_moved(lon, lat)

    def _remove_route_guidance_layer(self):
        if self.route_guidance_layer is None:
            self.route_guidance_feature_ids = {}
            return

        project = QgsProject.instance()
        try:
            layer_id = self.route_guidance_layer.id()
            if project.mapLayer(layer_id) is not None:
                project.removeMapLayer(layer_id)
        except RuntimeError:
            pass
        self.route_guidance_layer = None
        self.route_guidance_feature_ids = {}

    def _clear_current_route_display(self):
        self.active_route_history_id = None
        self._remove_route_layer()
        self._remove_route_guidance_layer()
        payload = {
            "history_id": "",
            "route_id": "",
            "summary": {},
            "path": [],
            "guides": [],
        }
        self.viewer_messages.publish("route_guidance", payload)

    def _set_route_point(self, point_id, lon, lat):
        if self.project_transitioning:
            return
        role = self._route_point_role(point_id)
        if role is None:
            return
        if not math.isfinite(lon) or not math.isfinite(lat):
            return
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            return

        layer = self._ensure_route_points_layer()
        provider = layer.dataProvider()
        geometry = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
        attributes = [point_id, role, lon, lat]
        feature_id = self.route_point_feature_ids.get(point_id)
        feature_valid = (
            feature_id is not None and layer.getFeature(feature_id).isValid()
        )

        if feature_valid:
            provider.changeGeometryValues({feature_id: geometry})
            provider.changeAttributeValues(
                {
                    feature_id: {
                        index: value
                        for index, value in enumerate(attributes)
                    }
                }
            )
        else:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(geometry)
            feature.setAttributes(attributes)
            if provider.addFeature(feature):
                self.route_point_feature_ids[point_id] = feature.id()

        layer.updateExtents()
        layer.triggerRepaint()

    def _ensure_route_points_layer(self):
        project = QgsProject.instance()
        if self.route_points_layer is not None:
            try:
                if project.mapLayer(self.route_points_layer.id()) is not None:
                    return self.route_points_layer
            except RuntimeError:
                pass

        uri = (
            "Point?crs=EPSG:4326"
            "&field=point_id:string(32)"
            "&field=role:string(16)"
            "&field=longitude:double"
            "&field=latitude:double"
        )
        layer = QgsVectorLayer(uri, "Naver Route Points", "memory")
        layer.setCustomProperty("skipMemoryLayersCheck", 1)

        origin_symbol = self._route_pin_symbol("route_origin_pin.svg")
        destination_symbol = self._route_pin_symbol(
            "route_destination_pin.svg"
        )
        waypoint_symbol = self._route_pin_symbol("route_waypoint_pin.svg")
        renderer = QgsCategorizedSymbolRenderer(
            "role",
            [
                QgsRendererCategory("origin", origin_symbol, "출발지"),
                QgsRendererCategory(
                    "destination",
                    destination_symbol,
                    "도착지",
                ),
                QgsRendererCategory(
                    "waypoint",
                    waypoint_symbol,
                    "경유지",
                ),
            ],
        )
        layer.setRenderer(renderer)

        project.addMapLayer(layer)
        self.route_points_layer = layer
        self.route_point_feature_ids = {}
        return layer

    @staticmethod
    def _route_pin_symbol(filename, size=9.0):
        symbol_layer = QgsSvgMarkerSymbolLayer(
            MapLayersMixin._embedded_svg_path(filename),
            size,
        )
        vertical_anchor = getattr(Qgis, "VerticalAnchorPoint", None)
        bottom_anchor = getattr(vertical_anchor, "Bottom", None)
        if bottom_anchor is None:
            bottom_anchor = getattr(symbol_layer, "Bottom", None)
        if bottom_anchor is not None:
            symbol_layer.setVerticalAnchorPoint(bottom_anchor)
        return QgsMarkerSymbol([symbol_layer])

    @staticmethod
    @lru_cache(maxsize=None)
    def _embedded_svg_path(filename):
        svg_path = PLUGIN_DIR / "web" / filename
        encoded = b64encode(svg_path.read_bytes()).decode("ascii")
        return f"base64:{encoded}"

    @staticmethod
    def _route_point_role(point_id):
        if point_id in ("origin", "destination"):
            return point_id
        if point_id.startswith("waypoint:"):
            return "waypoint"
        return None

    def _clear_route_point(self, point_id):
        if self._route_point_role(point_id) is None:
            return

        feature_id = self.route_point_feature_ids.pop(point_id, None)
        if feature_id is None or self.route_points_layer is None:
            return

        try:
            self.route_points_layer.dataProvider().deleteFeatures([feature_id])
            self.route_points_layer.updateExtents()
            self.route_points_layer.triggerRepaint()
        except RuntimeError:
            self.route_points_layer = None
            self.route_point_feature_ids = {}

    def _clear_route_points(self):
        feature_ids = list(self.route_point_feature_ids.values())
        self.route_point_feature_ids = {}
        if not feature_ids or self.route_points_layer is None:
            return

        try:
            self.route_points_layer.dataProvider().deleteFeatures(feature_ids)
            self.route_points_layer.updateExtents()
            self.route_points_layer.triggerRepaint()
        except RuntimeError:
            self.route_points_layer = None

    def _remove_route_points_layer(self):
        if self.route_points_layer is None:
            self.route_point_feature_ids = {}
            return

        project = QgsProject.instance()
        try:
            layer_id = self.route_points_layer.id()
            if project.mapLayer(layer_id) is not None:
                project.removeMapLayer(layer_id)
        except RuntimeError:
            pass
        self.route_points_layer = None
        self.route_point_feature_ids = {}
