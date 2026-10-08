# SPDX-License-Identifier: GPL-2.0-or-later
"""RouteHistoryMixin: behavior-preserving host methods; state is owned by the plugin."""

import json
from datetime import datetime
from pathlib import Path
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsMessageLog,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from .compat import MSGBOX_NO, MSGBOX_YES, MSG_CRITICAL, MSG_WARNING
from .constants import (
    LOG_TAG,
    MAX_ROUTE_WAYPOINTS,
    HISTORY_SCHEMA_VERSION,
    ROUTE_HISTORY_LAYER_NAME,
    GUIDANCE_HISTORY_LAYER_NAME,
)


class RouteHistoryMixin:
    def _append_route_history(
        self,
        history_id,
        route_id,
        searched_at,
        points,
        origin,
        destination,
        origin_label,
        destination_label,
        waypoints,
        distance,
        duration,
        guidance_count,
        result_summary,
        priority,
        avoid_options,
        vehicle_options,
        guides,
    ):
        route_layer, guidance_layer = self._ensure_route_history_layers()

        route_feature = QgsFeature(route_layer.fields())
        route_feature.setGeometry(QgsGeometry.fromPolylineXY(points))
        route_feature.setAttributes(
            [
                HISTORY_SCHEMA_VERSION,
                history_id,
                route_id,
                searched_at,
                origin[0],
                origin[1],
                origin_label,
                destination[0],
                destination[1],
                destination_label,
                json.dumps(
                    waypoints,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                distance,
                duration,
                guidance_count,
                result_summary,
                priority,
                "|".join(avoid_options),
                vehicle_options["car_type"],
                vehicle_options["car_fuel"],
                1 if vehicle_options["car_hipass"] else 0,
            ]
        )
        if not route_layer.dataProvider().addFeature(route_feature):
            QgsMessageLog.logMessage(
                "경로 검색 이력을 메모리 레이어에 추가하지 못했습니다.",
                LOG_TAG,
                MSG_WARNING,
            )
            return
        route_layer.updateExtents()

        guidance_features = []
        for guide in guides:
            feature = QgsFeature(guidance_layer.fields())
            feature.setGeometry(
                QgsGeometry.fromPointXY(
                    QgsPointXY(guide["longitude"], guide["latitude"])
                )
            )
            feature.setAttributes(
                [
                    HISTORY_SCHEMA_VERSION,
                    history_id,
                    guide["route_id"],
                    searched_at,
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
            guidance_features.append(feature)

        if guidance_features:
            guidance_layer.dataProvider().addFeatures(guidance_features)
            guidance_layer.updateExtents()

        if self.save_history_action is not None:
            self.save_history_action.setEnabled(True)
        if self.export_geojson_action is not None:
            self.export_geojson_action.setEnabled(True)
        if self.export_shapefile_action is not None:
            self.export_shapefile_action.setEnabled(True)
        if self.export_gpx_action is not None:
            self.export_gpx_action.setEnabled(True)
        self._sync_route_history_panel(history_id)

    def _ensure_route_history_layers(self):
        if self.route_history_layer is None:
            route_uri = (
                "LineString?crs=EPSG:4326"
                "&field=schema_ver:integer"
                "&field=history_id:string(36)"
                "&field=route_id:string(64)"
                "&field=searched_at:string(32)"
                "&field=origin_lon:double"
                "&field=origin_lat:double"
                "&field=origin_name:string(255)"
                "&field=destination_lon:double"
                "&field=destination_lat:double"
                "&field=destination_name:string(255)"
                "&field=waypoints_json:string(4096)"
                "&field=distance_m:integer"
                "&field=duration_s:integer"
                "&field=guidance_count:integer"
                "&field=result_summary:string(255)"
                "&field=priority:string(16)"
                "&field=avoid:string(128)"
                "&field=car_type:integer"
                "&field=car_fuel:string(16)"
                "&field=car_hipass:integer"
            )
            self.route_history_layer = QgsVectorLayer(
                route_uri,
                "Naver Route History",
                "memory",
            )
            self.route_history_layer.renderer().setSymbol(
                self._route_line_symbol()
            )

        if self.guidance_history_layer is None:
            guidance_uri = (
                "Point?crs=EPSG:4326"
                "&field=schema_ver:integer"
                "&field=history_id:string(36)"
                "&field=route_id:string(64)"
                "&field=searched_at:string(32)"
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
            self.guidance_history_layer = QgsVectorLayer(
                guidance_uri,
                "Naver Guidance History",
                "memory",
            )
            self.guidance_history_layer.setRenderer(
                self._route_guidance_renderer()
            )

        return self.route_history_layer, self.guidance_history_layer

    def _load_route_history_file(self, _checked=False):
        project_home = QgsProject.instance().homePath()
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            "경로 이력 불러오기",
            project_home or "",
            (
                "경로 이력 (*.gpkg *.geojson *.shp);;"
                "GeoPackage (*.gpkg);;"
                "GeoJSON (*.geojson);;"
                "Shapefile (*.shp)"
            ),
        )
        if not filename:
            return

        input_path = Path(filename)
        try:
            route_source, guidance_source = self._open_history_sources(
                input_path
            )
            route_count = self._append_imported_history(
                route_source,
                self.route_history_layer,
                "LineString",
                self._full_history_field_specs("route"),
            )
            guidance_count = self._append_imported_history(
                guidance_source,
                self.guidance_history_layer,
                "Point",
                self._full_history_field_specs("guidance"),
            )
        except RuntimeError as exc:
            QgsMessageLog.logMessage(
                str(exc),
                LOG_TAG,
                MSG_CRITICAL,
            )
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                f"경로 이력 불러오기에 실패했습니다.\n\n{exc}",
            )
            return

        self._update_history_action_state()
        self._sync_route_history_panel()
        if route_count == 0 and guidance_count == 0:
            message = "선택한 파일의 이력이 이미 현재 세션에 있습니다."
        else:
            message = (
                f"경로 이력 불러오기 완료: 경로 {route_count}건, "
                f"안내 {guidance_count}건"
        )
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    def _load_styled_gpx(self, _checked=False):
        project_home = QgsProject.instance().homePath()
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            "GPX 스타일 적용해서 불러오기",
            project_home or "",
            "GPX (*.gpx)",
        )
        if not filename:
            return

        gpx_path = Path(filename)
        if gpx_path.suffix.lower() != ".gpx":
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "GPX 파일을 선택해 주세요.",
            )
            return

        loaded_layers = []
        missing_styles = []
        try:
            for layer_name, suffix in (
                ("tracks", "_tracks.qml"),
                ("routes", "_routes.qml"),
                ("waypoints", "_waypoints.qml"),
            ):
                layer = QgsVectorLayer(
                    f"{gpx_path}|layername={layer_name}",
                    f"{gpx_path.stem}_{layer_name}",
                    "ogr",
                )
                if not layer.isValid() or layer.featureCount() == 0:
                    continue

                style_path = gpx_path.with_name(f"{gpx_path.stem}{suffix}")
                if style_path.exists():
                    error_message, success = layer.loadNamedStyle(str(style_path))
                    if not success:
                        raise RuntimeError(
                            f"{style_path.name} 스타일 적용 실패: "
                            f"{error_message or '알 수 없는 오류'}"
                        )
                else:
                    missing_styles.append(style_path.name)

                QgsProject.instance().addMapLayer(layer)
                loaded_layers.append(layer)
        except RuntimeError as exc:
            QgsMessageLog.logMessage(
                str(exc),
                LOG_TAG,
                MSG_CRITICAL,
            )
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                f"GPX 불러오기에 실패했습니다.\n\n{exc}",
            )
            return

        if not loaded_layers:
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "불러올 GPX tracks/routes/waypoints 레이어가 없습니다.",
            )
            return

        self._zoom_to_layers(loaded_layers)
        message = f"GPX 레이어 {len(loaded_layers)}개를 스타일과 함께 불러왔습니다."
        if missing_styles:
            message += f" 누락된 QML: {', '.join(missing_styles)}"
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    def _open_history_sources(self, input_path):
        suffix = input_path.suffix.lower()
        if suffix == ".gpkg":
            route_source = QgsVectorLayer(
                f"{input_path}|layername={ROUTE_HISTORY_LAYER_NAME}",
                ROUTE_HISTORY_LAYER_NAME,
                "ogr",
            )
            guidance_source = QgsVectorLayer(
                f"{input_path}|layername={GUIDANCE_HISTORY_LAYER_NAME}",
                GUIDANCE_HISTORY_LAYER_NAME,
                "ogr",
            )
        elif suffix == ".geojson":
            route_path, guidance_path = self._geojson_output_paths(input_path)
            route_source = QgsVectorLayer(
                str(route_path),
                "Naver Route History",
                "ogr",
            )
            guidance_source = QgsVectorLayer(
                str(guidance_path),
                "Naver Guidance History",
                "ogr",
            )
        elif suffix == ".shp":
            route_path, guidance_path = self._paired_output_paths(
                input_path,
                ".shp",
            )
            route_source = QgsVectorLayer(
                str(route_path),
                "Naver Route History",
                "ogr",
            )
            guidance_source = QgsVectorLayer(
                str(guidance_path),
                "Naver Guidance History",
                "ogr",
            )
        else:
            raise RuntimeError("지원하지 않는 이력 파일 형식입니다.")

        if not route_source.isValid():
            raise RuntimeError("경로 이력 레이어를 열지 못했습니다.")
        if not guidance_source.isValid():
            raise RuntimeError("안내 이력 레이어를 열지 못했습니다.")

        self._ensure_route_history_layers()
        return route_source, guidance_source

    def _append_imported_history(
        self,
        source_layer,
        target_layer,
        geometry_name,
        field_specs,
    ):
        existing_ids = self._memory_history_ids(target_layer)
        pending_layer = QgsVectorLayer(
            f"{geometry_name}?crs=EPSG:4326",
            "Imported Naver Route History",
            "memory",
        )
        provider = pending_layer.dataProvider()
        provider.addAttributes(list(target_layer.fields()))
        pending_layer.updateFields()

        source_fields = set(source_layer.fields().names())
        features = []
        for source_feature in source_layer.getFeatures():
            history_id = self._history_value(
                source_feature,
                source_fields,
                "history_id",
                "hist_id",
            )
            if not history_id or str(history_id) in existing_ids:
                continue

            feature = QgsFeature(pending_layer.fields())
            feature.setGeometry(source_feature.geometry())
            feature.setAttributes(
                [
                    self._history_value(
                        source_feature,
                        source_fields,
                        spec["source"],
                        spec["name"],
                    )
                    for spec in field_specs
                ]
            )
            features.append(feature)

        if features:
            provider.addFeatures(features)
            pending_layer.updateExtents()
            target_layer.dataProvider().addFeatures(features)
            target_layer.updateExtents()

        return len(features)

    @staticmethod
    def _memory_history_ids(layer):
        history_index = layer.fields().indexOf("history_id")
        if history_index < 0:
            return set()
        return {
            str(feature[history_index])
            for feature in layer.getFeatures()
            if feature[history_index]
        }

    @staticmethod
    def _history_value(feature, source_fields, full_name, short_name):
        if full_name in source_fields:
            return feature[full_name]
        if short_name in source_fields:
            return feature[short_name]
        return None

    def _full_history_field_specs(self, layer_type):
        if layer_type == "route":
            return [
                {"source": "schema_ver", "name": "schema_v"},
                {"source": "history_id", "name": "hist_id"},
                {"source": "route_id", "name": "route_id"},
                {"source": "searched_at", "name": "searched"},
                {"source": "origin_lon", "name": "org_lon"},
                {"source": "origin_lat", "name": "org_lat"},
                {"source": "origin_name", "name": "org_name"},
                {"source": "destination_lon", "name": "dst_lon"},
                {"source": "destination_lat", "name": "dst_lat"},
                {"source": "destination_name", "name": "dst_name"},
                {"source": "waypoints_json", "name": "waypts"},
                {"source": "distance_m", "name": "dist_m"},
                {"source": "duration_s", "name": "dur_s"},
                {"source": "guidance_count", "name": "guide_cnt"},
                {"source": "result_summary", "name": "summary"},
                {"source": "priority", "name": "priority"},
                {"source": "avoid", "name": "avoid"},
                {"source": "car_type", "name": "car_type"},
                {"source": "car_fuel", "name": "car_fuel"},
                {"source": "car_hipass", "name": "car_hipass"},
            ]
        return [
            {"source": "schema_ver", "name": "schema_v"},
            {"source": "history_id", "name": "hist_id"},
            {"source": "route_id", "name": "route_id"},
            {"source": "searched_at", "name": "searched"},
            {"source": "sequence", "name": "seq"},
            {"source": "section_no", "name": "sect_no"},
            {"source": "guide_type", "name": "g_type"},
            {"source": "category", "name": "category"},
            {"source": "guidance", "name": "guidance"},
            {"source": "name", "name": "name"},
            {"source": "distance_m", "name": "dist_m"},
            {"source": "duration_s", "name": "dur_s"},
            {"source": "cum_distance_m", "name": "cum_dist"},
            {"source": "cum_duration_s", "name": "cum_dur"},
            {"source": "road_index", "name": "road_idx"},
            {"source": "longitude", "name": "lon"},
            {"source": "latitude", "name": "lat"},
        ]

    def _sync_route_history_panel(self, selected_history_id=None):
        payload = self._route_history_payload(selected_history_id)
        self.viewer_messages.publish("route_history", payload)

    def _refresh_route_history_panel(self):
        self._sync_route_history_panel(self.active_route_history_id)

    def _route_history_payload(self, selected_history_id=None):
        if self.route_history_layer is None:
            return {
                "selected_history_id": selected_history_id or "",
                "items": [],
            }

        history_index = self.route_history_layer.fields().indexOf("history_id")
        items = []
        for feature in self.route_history_layer.getFeatures():
            history_id = str(feature[history_index] or "")
            if not history_id:
                continue
            items.append(
                {
                    "history_id": history_id,
                    "searched_at": str(feature["searched_at"] or ""),
                    "origin_name": str(feature["origin_name"] or "출발지"),
                    "destination_name": str(
                        feature["destination_name"] or "도착지"
                    ),
                    "distance_m": self._safe_number(feature["distance_m"]),
                    "duration_s": self._safe_number(feature["duration_s"]),
                    "guidance_count": self._safe_number(
                        feature["guidance_count"]
                    ),
                    "result_summary": str(feature["result_summary"] or ""),
                    "priority": str(feature["priority"] or ""),
                    "avoid": str(feature["avoid"] or ""),
                    "car_type": self._safe_number(feature["car_type"]),
                    "car_fuel": str(feature["car_fuel"] or ""),
                    "car_hipass": bool(self._safe_number(feature["car_hipass"])),
                    "input": self._route_input_payload_from_history(feature),
                }
            )

        items.sort(key=lambda item: item["searched_at"], reverse=True)
        return {
            "selected_history_id": selected_history_id or "",
            "items": items,
        }

    def _focus_route_history(self, history_id):
        if not history_id or self.route_history_layer is None:
            return

        route_feature = self._route_feature_for_history(history_id)
        if route_feature is None:
            return

        self.route_history_layer.removeSelection()
        self.route_history_layer.selectByIds([route_feature.id()])

        guide_features = self._guidance_features_for_history(history_id)
        if self.guidance_history_layer is not None:
            self.guidance_history_layer.removeSelection()
            self.guidance_history_layer.selectByIds(
                [feature.id() for feature in guide_features]
            )

        guidance_payload = self._route_guidance_payload_from_history(
            route_feature,
            guide_features,
        )
        self.active_route_history_id = history_id
        points = self._route_points_from_geometry(route_feature.geometry())
        if len(points) >= 2:
            vehicle_options = guidance_payload["summary"]["vehicle"]
            avoid_options = guidance_payload["summary"]["avoid"]
            self._create_route_layer(
                points,
                self._safe_number(route_feature["distance_m"]),
                self._safe_number(route_feature["duration_s"]),
                self._safe_number(route_feature["guidance_count"]),
                str(route_feature["result_summary"] or ""),
                str(route_feature["priority"] or ""),
                self._waypoint_count_from_history(route_feature),
                avoid_options,
                vehicle_options,
            )
        else:
            self._zoom_to_geometry(route_feature.geometry())
        self._create_route_guidance_layer(guidance_payload["guides"])

        center = route_feature.geometry().centroid().asPoint()
        self.viewer_messages.publish(
            "route_guidance", guidance_payload, center=(center.x(), center.y())
        )
        self._sync_route_history_panel(history_id)
        self.iface.messageBar().pushInfo(
            "Naver Map QGIS Bridge",
            f"경로 이력 선택: {route_feature['result_summary']}",
        )

    def _load_route_history(self, history_id):
        route_feature = self._route_feature_for_history(history_id)
        if route_feature is None:
            return

        payload = self._route_input_payload_from_history(route_feature)
        self.viewer_messages.route_history_input(payload)
        self.iface.messageBar().pushInfo(
            "Naver Map QGIS Bridge",
            "선택한 이력을 경로 입력창으로 불러왔습니다.",
        )

    def _delete_route_history(self, history_id):
        route_feature = self._route_feature_for_history(history_id)
        if route_feature is None:
            return

        answer = QMessageBox.question(
            self.iface.mainWindow(),
            "Naver Map QGIS Bridge",
            (
                "선택한 경로 이력을 삭제할까요?\n\n"
                f"{route_feature['origin_name']} → "
                f"{route_feature['destination_name']}"
            ),
            MSGBOX_YES | MSGBOX_NO,
            MSGBOX_NO,
        )
        if answer != MSGBOX_YES:
            return

        was_active_history = history_id == self.active_route_history_id

        if self.route_history_layer is not None:
            self.route_history_layer.dataProvider().deleteFeatures(
                [route_feature.id()]
            )
            self.route_history_layer.updateExtents()

        if self.guidance_history_layer is not None:
            guidance_ids = [
                feature.id()
                for feature in self._guidance_features_for_history(history_id)
            ]
            if guidance_ids:
                self.guidance_history_layer.dataProvider().deleteFeatures(
                    guidance_ids
                )
                self.guidance_history_layer.updateExtents()

        if was_active_history:
            self._clear_current_route_display()

        self._sync_route_history_panel()
        self._update_history_action_state()
        self.iface.messageBar().pushInfo(
            "Naver Map QGIS Bridge",
            "선택한 경로 이력을 삭제했습니다.",
        )

    def _export_single_route_history(self, history_id):
        route_feature = self._route_feature_for_history(history_id)
        if route_feature is None:
            return

        formats = [
            "GeoPackage (*.gpkg)",
            "GeoJSON (*.geojson)",
            "Shapefile (*.shp)",
            "GPX (*.gpx)",
        ]
        selected_format, accepted = QInputDialog.getItem(
            self.iface.mainWindow(),
            "Naver Map QGIS Bridge",
            "선택한 경로 이력을 내보낼 형식",
            formats,
            0,
            False,
        )
        if not accepted:
            return

        base_name = self._history_export_basename(route_feature)
        project_home = QgsProject.instance().homePath()
        extension = {
            formats[0]: ".gpkg",
            formats[1]: ".geojson",
            formats[2]: ".shp",
            formats[3]: ".gpx",
        }[selected_format]
        default_name = f"{base_name}{extension}"
        default_path = (
            str(Path(project_home) / default_name)
            if project_home
            else default_name
        )
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "선택 경로 이력 내보내기",
            default_path,
            selected_format,
        )
        if not filename:
            return

        route_layer = self._single_history_layer(
            self.route_history_layer,
            [route_feature],
            "LineString",
            "Selected Naver Route History",
        )
        guidance_features = self._guidance_features_for_history(history_id)
        guidance_layer = self._single_history_layer(
            self.guidance_history_layer,
            guidance_features,
            "Point",
            "Selected Naver Guidance History",
        )

        try:
            if selected_format == formats[0]:
                output_path = Path(filename)
                if output_path.suffix.lower() != ".gpkg":
                    output_path = output_path.with_suffix(".gpkg")
                route_count = self._write_history_layer(
                    route_layer,
                    output_path,
                    ROUTE_HISTORY_LAYER_NAME,
                    "LineString",
                )
                guidance_count = self._write_history_layer(
                    guidance_layer,
                    output_path,
                    GUIDANCE_HISTORY_LAYER_NAME,
                    "Point",
                )
                output_parent = output_path.parent
            elif selected_format == formats[1]:
                route_path, guidance_path = self._geojson_output_paths(filename)
                route_count = self._write_geojson_history_layer(
                    route_layer,
                    route_path,
                    "Naver Route History",
                )
                guidance_count = self._write_geojson_history_layer(
                    guidance_layer,
                    guidance_path,
                    "Naver Guidance History",
                )
                output_parent = route_path.parent
            elif selected_format == formats[2]:
                route_path, guidance_path = self._paired_output_paths(
                    filename,
                    ".shp",
                )
                route_count = self._write_shapefile_history_layer(
                    route_layer,
                    route_path,
                    "LineString",
                    "Naver Route History",
                    self._route_shapefile_fields(),
                )
                guidance_count = self._write_shapefile_history_layer(
                    guidance_layer,
                    guidance_path,
                    "Point",
                    "Naver Guidance History",
                    self._guidance_shapefile_fields(),
                )
                output_parent = route_path.parent
            else:
                output_path = Path(filename)
                if output_path.suffix.lower() != ".gpx":
                    output_path = output_path.with_suffix(".gpx")
                route_count, guidance_count = self._write_gpx_history(
                    route_layer,
                    guidance_layer,
                    output_path,
                )
                output_parent = output_path.parent
        except RuntimeError as exc:
            QgsMessageLog.logMessage(
                str(exc),
                LOG_TAG,
                MSG_CRITICAL,
            )
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                f"선택 경로 이력 내보내기에 실패했습니다.\n\n{exc}",
            )
            return

        self.iface.messageBar().pushSuccess(
            "Naver Map QGIS Bridge",
            (
                f"선택 이력 내보내기 완료: 경로 {route_count}건, "
                f"안내 {guidance_count}건 ({output_parent})"
            ),
        )

    def _update_history_action_state(self):
        has_history = (
            self.route_history_layer is not None
            and self.route_history_layer.featureCount() > 0
        )
        if self.save_history_action is not None:
            self.save_history_action.setEnabled(has_history)
        if self.export_geojson_action is not None:
            self.export_geojson_action.setEnabled(has_history)
        if self.export_shapefile_action is not None:
            self.export_shapefile_action.setEnabled(has_history)
        if self.export_gpx_action is not None:
            self.export_gpx_action.setEnabled(has_history)

    def _route_feature_for_history(self, history_id):
        if self.route_history_layer is None:
            return None
        for feature in self.route_history_layer.getFeatures():
            if str(feature["history_id"]) == history_id:
                return QgsFeature(feature)
        return None

    def _guidance_features_for_history(self, history_id):
        if self.guidance_history_layer is None:
            return []
        features = [
            feature
            for feature in self.guidance_history_layer.getFeatures()
            if str(feature["history_id"]) == history_id
        ]
        features.sort(key=lambda feature: self._safe_number(feature["sequence"]))
        return [QgsFeature(feature) for feature in features]

    def _route_input_payload_from_history(self, route_feature):
        waypoints = []
        try:
            parsed = json.loads(str(route_feature["waypoints_json"] or "[]"))
            if isinstance(parsed, list):
                waypoints = parsed[:MAX_ROUTE_WAYPOINTS]
        except (TypeError, ValueError, json.JSONDecodeError):
            waypoints = []

        return {
            "origin": {
                "label": str(route_feature["origin_name"] or ""),
                "lon": self._safe_float(route_feature["origin_lon"]),
                "lat": self._safe_float(route_feature["origin_lat"]),
            },
            "destination": {
                "label": str(route_feature["destination_name"] or ""),
                "lon": self._safe_float(route_feature["destination_lon"]),
                "lat": self._safe_float(route_feature["destination_lat"]),
            },
            "waypoints": [
                {
                    "label": str(item.get("label") or ""),
                    "lon": self._safe_float(item.get("lon")),
                    "lat": self._safe_float(item.get("lat")),
                }
                for item in waypoints
                if isinstance(item, dict)
            ],
            "priority": str(route_feature["priority"] or "RECOMMEND"),
            "avoid": [
                value
                for value in str(route_feature["avoid"] or "").split("|")
                if value
            ],
            "vehicle": {
                "car_type": self._safe_number(route_feature["car_type"]) or 1,
                "car_fuel": str(route_feature["car_fuel"] or "GASOLINE"),
                "car_hipass": bool(self._safe_number(route_feature["car_hipass"])),
            },
        }

    @staticmethod
    def _single_history_layer(source_layer, features, geometry_name, layer_name):
        layer = QgsVectorLayer(
            f"{geometry_name}?crs={source_layer.crs().authid()}",
            layer_name,
            "memory",
        )
        provider = layer.dataProvider()
        provider.addAttributes(list(source_layer.fields()))
        layer.updateFields()
        copied_features = []
        for source_feature in features:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(source_feature.geometry())
            feature.setAttributes(source_feature.attributes())
            copied_features.append(feature)
        if copied_features:
            provider.addFeatures(copied_features)
            layer.updateExtents()
        layer.setRenderer(source_layer.renderer().clone())
        return layer

    @staticmethod
    def _history_export_basename(route_feature):
        searched = str(route_feature["searched_at"] or "")
        date_part = searched[:10].replace("-", "") or datetime.now().strftime("%Y%m%d")
        origin = str(route_feature["origin_name"] or "origin").strip()
        destination = str(route_feature["destination_name"] or "destination").strip()
        raw_name = f"naver_route_{date_part}_{origin}_to_{destination}"
        safe = "".join(
            character if character.isalnum() or character in ("-", "_") else "_"
            for character in raw_name
        )
        while "__" in safe:
            safe = safe.replace("__", "_")
        return safe[:120].strip("_") or f"naver_route_{date_part}"

    def _route_guidance_payload_from_history(self, route_feature, guide_features):
        vehicle = {
            "car_type": self._safe_number(route_feature["car_type"]),
            "car_fuel": str(route_feature["car_fuel"] or ""),
            "car_hipass": bool(self._safe_number(route_feature["car_hipass"])),
        }
        avoid = [
            value
            for value in str(route_feature["avoid"] or "").split("|")
            if value
        ]
        return {
            "history_id": str(route_feature["history_id"] or ""),
            "route_id": str(route_feature["route_id"] or ""),
            "summary": {
                "distance_m": self._safe_number(route_feature["distance_m"]),
                "duration_s": self._safe_number(route_feature["duration_s"]),
                "guidance_count": self._safe_number(
                    route_feature["guidance_count"]
                ),
                "result_summary": str(route_feature["result_summary"] or ""),
                "priority": str(route_feature["priority"] or ""),
                "avoid": avoid,
                "vehicle": vehicle,
            },
            "path": self._route_path_payload(
                self._route_points_from_geometry(route_feature.geometry())
            ),
            "guides": [
                {
                    "route_id": str(feature["route_id"] or ""),
                    "sequence": self._safe_number(feature["sequence"]),
                    "section_no": self._safe_number(feature["section_no"]),
                    "guide_type": self._safe_number(feature["guide_type"]),
                    "category": str(feature["category"] or "other"),
                    "guidance": str(feature["guidance"] or "경로 안내"),
                    "name": str(feature["name"] or ""),
                    "distance_m": self._safe_number(feature["distance_m"]),
                    "duration_s": self._safe_number(feature["duration_s"]),
                    "cumulative_distance_m": self._safe_number(
                        feature["cum_distance_m"]
                    ),
                    "cumulative_duration_s": self._safe_number(
                        feature["cum_duration_s"]
                    ),
                    "road_index": self._safe_number(feature["road_index"]),
                    "longitude": self._safe_float(feature["longitude"]),
                    "latitude": self._safe_float(feature["latitude"]),
                }
                for feature in guide_features
            ],
        }

    @staticmethod
    def _route_points_from_geometry(geometry):
        if geometry is None or geometry.isEmpty():
            return []
        if geometry.isMultipart():
            parts = geometry.asMultiPolyline()
            return parts[0] if parts else []
        return geometry.asPolyline()

    @staticmethod
    def _route_path_payload(points):
        return [
            {
                "lon": point.x(),
                "lat": point.y(),
            }
            for point in points
        ]

    @staticmethod
    def _waypoint_count_from_history(route_feature):
        try:
            waypoints = json.loads(str(route_feature["waypoints_json"] or "[]"))
            return len(waypoints) if isinstance(waypoints, list) else 0
        except (TypeError, ValueError, json.JSONDecodeError):
            return 0

    def _zoom_to_geometry(self, geometry):
        if geometry is None or geometry.isEmpty():
            return

        canvas = self.iface.mapCanvas()
        project = QgsProject.instance()
        try:
            transform = QgsCoordinateTransform(
                QgsCoordinateReferenceSystem("EPSG:4326"),
                canvas.mapSettings().destinationCrs(),
                project,
            )
            extent = transform.transformBoundingBox(geometry.boundingBox())
            margin = max(extent.width(), extent.height()) * 0.08
            if margin > 0:
                extent.grow(margin)
            canvas.setExtent(extent)
            canvas.refresh()
        except Exception as exc:
            QgsMessageLog.logMessage(str(exc), LOG_TAG, MSG_WARNING)

    def _zoom_to_layers(self, layers):
        canvas = self.iface.mapCanvas()
        project = QgsProject.instance()
        combined_extent = None

        for layer in layers:
            if layer is None or not layer.isValid() or layer.featureCount() == 0:
                continue
            try:
                transform = QgsCoordinateTransform(
                    layer.crs(),
                    canvas.mapSettings().destinationCrs(),
                    project,
                )
                extent = transform.transformBoundingBox(layer.extent())
            except Exception as exc:
                QgsMessageLog.logMessage(
                    str(exc),
                    LOG_TAG,
                    MSG_WARNING,
                )
                continue

            if combined_extent is None:
                combined_extent = extent
            else:
                combined_extent.combineExtentWith(extent)

        if combined_extent is None:
            return

        margin = max(combined_extent.width(), combined_extent.height()) * 0.08
        if margin > 0:
            combined_extent.grow(margin)
        canvas.setExtent(combined_extent)
        canvas.refresh()
