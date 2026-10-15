# SPDX-License-Identifier: GPL-2.0-or-later
"""HistoryExportMixin: behavior-preserving host methods; state is owned by the plugin."""

from datetime import datetime
from pathlib import Path
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsFeature,
    QgsMessageLog,
    QgsProject,
    QgsRendererCategory,
    QgsVectorFileWriter,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from .compat import (
    MSGBOX_NO,
    MSGBOX_YES,
    MSG_CRITICAL,
    WRITE_APPEND_ADD_FIELDS,
    WRITE_APPEND_NO_FIELDS,
    WRITE_OVERWRITE_FILE,
    WRITE_OVERWRITE_LAYER,
    save_style_to_database,
)
from .data_transforms import safe_number
from .history_schema import history_shapefile_fields
from .gpx_export import (
    GUIDE_FIELDS,
    ROUTE_FIELDS,
    build_gpx_document,
    waypoints_from_history,
)
from .constants import LOG_TAG, ROUTE_HISTORY_LAYER_NAME, GUIDANCE_HISTORY_LAYER_NAME


class HistoryExportMixin:
    def _repair_saved_guidance_categories(self, source_layer, output_path, layer_name):
        if "guide_type" not in source_layer.fields().names():
            return
        from .data_transforms import guidance_category
        target = QgsVectorLayer(f"{output_path}|layername={layer_name}", "Guidance repair", "ogr")
        if not target.isValid():
            raise RuntimeError("저장된 안내 이력을 열지 못했습니다.")
        identifiers = {str(feature["history_id"]) for feature in source_layer.getFeatures()}
        changes = {}
        for feature in target.getFeatures():
            if str(feature["history_id"]) in identifiers:
                category = guidance_category(int(feature["guide_type"]), str(feature["guidance"] or ""))
                if str(feature["category"]) != category:
                    changes[feature.id()] = {target.fields().indexOf("category"): category}
        if changes and not target.dataProvider().changeAttributeValues(changes):
            raise RuntimeError("저장된 안내 분류 보정에 실패했습니다.")

    def _validate_shapefile_pair(self, routes, guidance):
        self._shapefile_compatible_layer(routes, "LineString", self._route_shapefile_fields())
        self._shapefile_compatible_layer(guidance, "Point", self._guidance_shapefile_fields())

    def _normalized_export_layer(self, layer):
        if layer is not None and "guide_type" in layer.fields().names():
            from .history_operations import normalize_guidance_feature
            copy = self._single_history_layer(layer, list(layer.getFeatures()), "Point", layer.name())
            changes = {}
            for feature in copy.getFeatures():
                normalize_guidance_feature(feature)
                changes[feature.id()] = {copy.fields().indexOf("category"): feature["category"]}
            if changes and not copy.dataProvider().changeAttributeValues(changes):
                raise RuntimeError("안내 분류 정규화 실패")
            return copy
        return layer

    def _save_route_history_geopackage(self, _checked=False):
        if (
            self.route_history_layer is None
            or self.route_history_layer.featureCount() == 0
        ):
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "저장할 경로 검색 이력이 없습니다. 경로를 먼저 생성해 주세요.",
            )
            return

        project_home = QgsProject.instance().homePath()
        default_name = f"naver_route_history_{datetime.now():%Y%m%d}.gpkg"
        default_path = (
            str(Path(project_home) / default_name)
            if project_home
            else default_name
        )
        epoch = self.project_epoch
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "경로 이력 GeoPackage 저장",
            default_path,
            "GeoPackage (*.gpkg)",
        )
        if not filename or self.project_transitioning or epoch != self.project_epoch:
            return

        output_path = Path(filename)
        if output_path.suffix.lower() != ".gpkg":
            output_path = output_path.with_suffix(".gpkg")

        try:
            route_count = self._write_history_layer(
                self.route_history_layer,
                output_path,
                ROUTE_HISTORY_LAYER_NAME,
                "LineString",
            )
            guidance_count = self._write_history_layer(
                self.guidance_history_layer,
                output_path,
                GUIDANCE_HISTORY_LAYER_NAME,
                "Point",
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
                f"GeoPackage 저장에 실패했습니다.\n\n{exc}",
            )
            return

        if route_count == 0 and guidance_count == 0:
            message = "선택한 GeoPackage에 현재 세션 이력이 이미 저장되어 있습니다."
        else:
            message = (
                f"GeoPackage 저장 완료: 경로 {route_count}건, "
                f"안내 {guidance_count}건"
            )
        message = f"{message} ({output_path})"
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    def _export_route_history_geojson(self, _checked=False):
        if (
            self.route_history_layer is None
            or self.route_history_layer.featureCount() == 0
        ):
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "내보낼 경로 검색 이력이 없습니다. 경로를 먼저 생성해 주세요.",
            )
            return

        project_home = QgsProject.instance().homePath()
        default_name = f"naver_route_history_{datetime.now():%Y%m%d}.geojson"
        default_path = (
            str(Path(project_home) / default_name)
            if project_home
            else default_name
        )
        epoch = self.project_epoch
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "경로·안내 이력 GeoJSON 내보내기",
            default_path,
            "GeoJSON (*.geojson)",
        )
        if not filename or self.project_transitioning or epoch != self.project_epoch:
            return

        route_path, guidance_path = self._geojson_output_paths(filename)
        output_paths = [
            route_path,
            guidance_path,
            route_path.with_suffix(".qml"),
            guidance_path.with_suffix(".qml"),
        ]
        existing_paths = [path for path in output_paths if path.exists()]
        if existing_paths:
            filenames = "\n".join(path.name for path in existing_paths)
            answer = QMessageBox.question(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "다음 파일을 덮어쓸까요?\n\n" + filenames,
                MSGBOX_YES
                | MSGBOX_NO,
                MSGBOX_NO,
            )
            if answer != MSGBOX_YES:
                return

        try:
            route_count = self._write_geojson_history_layer(
                self.route_history_layer,
                route_path,
                "Naver Route History",
            )
            guidance_count = self._write_geojson_history_layer(
                self.guidance_history_layer,
                guidance_path,
                "Naver Guidance History",
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
                f"GeoJSON 내보내기에 실패했습니다.\n\n{exc}",
            )
            return

        message = (
            f"GeoJSON 내보내기 완료: 경로 {route_count}건, "
            f"안내 {guidance_count}건 ({route_path.parent})"
        )
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    def _export_route_history_shapefile(self, _checked=False):
        if (
            self.route_history_layer is None
            or self.route_history_layer.featureCount() == 0
        ):
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "내보낼 경로 검색 이력이 없습니다. 경로를 먼저 생성해 주세요.",
            )
            return

        project_home = QgsProject.instance().homePath()
        default_name = f"naver_route_history_{datetime.now():%Y%m%d}.shp"
        default_path = (
            str(Path(project_home) / default_name)
            if project_home
            else default_name
        )
        epoch = self.project_epoch
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "경로·안내 이력 Shapefile 내보내기",
            default_path,
            "Shapefile (*.shp)",
        )
        if not filename or self.project_transitioning or epoch != self.project_epoch:
            return

        route_path, guidance_path = self._paired_output_paths(
            filename,
            ".shp",
        )
        output_paths = self._shapefile_sidecar_paths(route_path)
        output_paths.extend(self._shapefile_sidecar_paths(guidance_path))
        existing_paths = [path for path in output_paths if path.exists()]
        if existing_paths:
            filenames = "\n".join(path.name for path in existing_paths)
            answer = QMessageBox.question(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "다음 파일을 덮어쓸까요?\n\n" + filenames,
                MSGBOX_YES
                | MSGBOX_NO,
                MSGBOX_NO,
            )
            if answer != MSGBOX_YES:
                return

        try:
            self._validate_shapefile_pair(self.route_history_layer, self.guidance_history_layer)
            route_count = self._write_shapefile_history_layer(
                self.route_history_layer,
                route_path,
                "LineString",
                "Naver Route History",
                self._route_shapefile_fields(),
            )
            guidance_count = self._write_shapefile_history_layer(
                self.guidance_history_layer,
                guidance_path,
                "Point",
                "Naver Guidance History",
                self._guidance_shapefile_fields(),
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
                f"Shapefile 내보내기에 실패했습니다.\n\n{exc}",
            )
            return

        message = (
            f"Shapefile 내보내기 완료: 경로 {route_count}건, "
            f"안내 {guidance_count}건 ({route_path.parent})"
        )
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    def _export_route_history_gpx(self, _checked=False):
        if (
            self.route_history_layer is None
            or self.route_history_layer.featureCount() == 0
        ):
            QMessageBox.information(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                "내보낼 경로 검색 이력이 없습니다. 경로를 먼저 생성해 주세요.",
            )
            return

        project_home = QgsProject.instance().homePath()
        default_name = f"naver_route_history_{datetime.now():%Y%m%d}.gpx"
        default_path = (
            str(Path(project_home) / default_name)
            if project_home
            else default_name
        )
        epoch = self.project_epoch
        filename, _selected_filter = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            "경로·안내 이력 GPX 내보내기",
            default_path,
            "GPX (*.gpx)",
        )
        if not filename or self.project_transitioning or epoch != self.project_epoch:
            return

        output_path = Path(filename)
        if output_path.suffix.lower() != ".gpx":
            output_path = output_path.with_suffix(".gpx")
        if output_path.exists():
            answer = QMessageBox.question(
                self.iface.mainWindow(),
                "Naver Map QGIS Bridge",
                f"{output_path.name} 파일을 덮어쓸까요?",
                MSGBOX_YES
                | MSGBOX_NO,
                MSGBOX_NO,
            )
            if answer != MSGBOX_YES:
                return

        try:
            route_count, guidance_count = self._write_gpx_history(
                self.route_history_layer,
                self.guidance_history_layer,
                output_path,
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
                f"GPX 내보내기에 실패했습니다.\n\n{exc}",
            )
            return

        message = (
            f"GPX 내보내기 완료: 경로 {route_count}건, "
            f"안내 {guidance_count}건 ({output_path.parent})"
        )
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    @staticmethod
    def _geojson_output_paths(filename):
        return HistoryExportMixin._paired_output_paths(filename, ".geojson")

    @staticmethod
    def _paired_output_paths(filename, extension):
        selected_path = Path(filename)
        if selected_path.suffix.lower() != extension:
            selected_path = selected_path.with_suffix(extension)

        base_stem = selected_path.stem
        for paired_suffix in ("_routes", "_guidance"):
            if base_stem.lower().endswith(paired_suffix):
                base_stem = base_stem[:-len(paired_suffix)]
                break

        route_path = selected_path.with_name(
            f"{base_stem}_routes{selected_path.suffix}"
        )
        guidance_path = selected_path.with_name(
            f"{base_stem}_guidance{selected_path.suffix}"
        )
        return route_path, guidance_path

    def _write_geojson_history_layer(
        self,
        source_layer,
        output_path,
        layer_name,
    ):
        source_layer = self._normalized_export_layer(source_layer)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GeoJSON"
        options.fileEncoding = "UTF-8"
        options.layerName = layer_name
        options.actionOnExistingFile = (
            WRITE_OVERWRITE_FILE
        )
        options.layerOptions = [
            "RFC7946=YES",
            "COORDINATE_PRECISION=8",
            "WRITE_BBOX=YES",
            "AUTODETECT_JSON_STRINGS=NO",
        ]

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            source_layer,
            str(output_path),
            QgsProject.instance().transformContext(),
            options,
        )
        error_code = result[0] if isinstance(result, tuple) else result
        error_value = getattr(error_code, "value", error_code)
        if int(error_value) != 0:
            error_message = ""
            if isinstance(result, tuple) and len(result) > 1:
                error_message = str(result[1] or "")
            detail = error_message or f"오류 코드 {error_value}"
            raise RuntimeError(
                f"{output_path.name} 저장 실패: {detail}"
            )

        self._save_sidecar_style(
            output_path,
            layer_name,
            source_layer,
        )
        return source_layer.featureCount()

    def _write_shapefile_history_layer(
        self,
        source_layer,
        output_path,
        geometry_name,
        layer_name,
        field_specs,
    ):
        source_layer = self._normalized_export_layer(source_layer)
        shapefile_layer = self._shapefile_compatible_layer(
            source_layer,
            geometry_name,
            field_specs,
        )

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        options.layerName = layer_name
        options.actionOnExistingFile = (
            WRITE_OVERWRITE_FILE
        )
        options.layerOptions = ["ENCODING=UTF-8"]

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            shapefile_layer,
            str(output_path),
            QgsProject.instance().transformContext(),
            options,
        )
        error_code = result[0] if isinstance(result, tuple) else result
        error_value = getattr(error_code, "value", error_code)
        if int(error_value) != 0:
            error_message = ""
            if isinstance(result, tuple) and len(result) > 1:
                error_message = str(result[1] or "")
            detail = error_message or f"오류 코드 {error_value}"
            raise RuntimeError(
                f"{output_path.name} 저장 실패: {detail}"
            )

        self._save_sidecar_style(
            output_path,
            layer_name,
            source_layer,
        )
        return shapefile_layer.featureCount()

    def _write_gpx_history(self, route_layer, guidance_layer, output_path):
        guidance_layer = self._normalized_export_layer(guidance_layer)
        route_features = list(route_layer.getFeatures())
        guidance_by_history = self._guidance_features_by_history(guidance_layer)

        def records():
            for feature in route_features:
                points = self._route_points_from_geometry(feature.geometry())
                if len(points) < 2:
                    continue
                history_id = str(feature["history_id"] or "")
                route = {key: feature[key] for key in ROUTE_FIELDS}
                guides = [
                    {key: guide[key] for key in GUIDE_FIELDS}
                    for guide in guidance_by_history.get(history_id, [])
                ]
                yield route, [(point.x(), point.y()) for point in points], guides

        tree, route_total, guidance_total = build_gpx_document(
            records(), datetime.now().astimezone().isoformat(timespec="seconds")
        )
        try:
            tree.write(
                str(output_path),
                encoding="utf-8",
                xml_declaration=True,
                short_empty_elements=True,
            )
        except OSError as exc:
            raise RuntimeError(f"{output_path.name} 저장 실패: {exc}") from exc

        self._save_gpx_sidecar_styles(output_path)
        return route_total, guidance_total

    def _save_gpx_sidecar_styles(self, output_path):
        tracks_layer = QgsVectorLayer(
            "LineString?crs=EPSG:4326&field=name:string(255)&field=type:string(32)",
            "Naver GPX Tracks",
            "memory",
        )
        tracks_layer.renderer().setSymbol(self._route_line_symbol())
        self._save_layer_style_to_path(
            tracks_layer,
            output_path.with_name(f"{output_path.stem}_tracks.qml"),
        )

        routes_layer = QgsVectorLayer(
            "LineString?crs=EPSG:4326&field=name:string(255)&field=type:string(32)",
            "Naver GPX Routes",
            "memory",
        )
        routes_layer.renderer().setSymbol(self._route_line_symbol())
        self._save_layer_style_to_path(
            routes_layer,
            output_path.with_name(f"{output_path.stem}_routes.qml"),
        )

        waypoints_layer = QgsVectorLayer(
            "Point?crs=EPSG:4326&field=name:string(255)&field=type:string(64)",
            "Naver GPX Waypoints",
            "memory",
        )
        waypoints_layer.setRenderer(self._gpx_waypoint_renderer())
        self._save_layer_style_to_path(
            waypoints_layer,
            output_path.with_name(f"{output_path.stem}_waypoints.qml"),
        )

    def _gpx_waypoint_renderer(self):
        return QgsCategorizedSymbolRenderer(
            "type",
            [
                QgsRendererCategory(
                    "origin",
                    self._route_pin_symbol("route_origin_pin.svg", 7.5),
                    "출발지",
                ),
                QgsRendererCategory(
                    "destination",
                    self._route_pin_symbol("route_destination_pin.svg", 7.5),
                    "도착지",
                ),
                QgsRendererCategory(
                    "waypoint",
                    self._route_pin_symbol("route_waypoint_pin.svg", 7.5),
                    "경유지",
                ),
                QgsRendererCategory(
                    "guidance:straight",
                    self._guidance_symbol("guidance_straight.svg"),
                    "직진",
                ),
                QgsRendererCategory(
                    "guidance:left",
                    self._guidance_symbol("guidance_left.svg"),
                    "좌회전",
                ),
                QgsRendererCategory(
                    "guidance:right",
                    self._guidance_symbol("guidance_right.svg"),
                    "우회전",
                ),
                QgsRendererCategory(
                    "guidance:uturn",
                    self._guidance_symbol("guidance_uturn.svg"),
                    "유턴",
                ),
                QgsRendererCategory(
                    "guidance:roundabout",
                    self._guidance_symbol("guidance_roundabout.svg"),
                    "회전교차로",
                ),
                QgsRendererCategory(
                    "guidance:transition",
                    self._guidance_symbol("guidance_transition.svg"),
                    "진출입",
                ),
                QgsRendererCategory(
                    "guidance:other",
                    self._guidance_symbol("guidance_other.svg"),
                    "기타 안내",
                ),
            ],
        )

    @staticmethod
    def _save_layer_style_to_path(layer, style_path):
        error_message, success = layer.saveNamedStyle(str(style_path))
        if not success:
            detail = error_message or "알 수 없는 오류"
            raise RuntimeError(
                f"{style_path.name} 스타일 저장 실패: {detail}"
            )

    @staticmethod
    def _guidance_features_by_history(guidance_layer):
        grouped = {}
        if guidance_layer is None:
            return grouped
        for feature in guidance_layer.getFeatures():
            history_id = str(feature["history_id"] or "")
            if not history_id:
                continue
            grouped.setdefault(history_id, []).append(QgsFeature(feature))
        for features in grouped.values():
            features.sort(
                key=lambda feature: safe_number(
                    feature["sequence"]
                )
            )
        return grouped

    @staticmethod
    def _waypoints_from_history(route_feature):
        return waypoints_from_history(route_feature)

    @staticmethod
    def _shapefile_compatible_layer(
        source_layer,
        geometry_name,
        field_specs,
    ):
        field_parts = []
        for spec in field_specs:
            field_type = spec["type"]
            if field_type == "string":
                field_parts.append(
                    f"&field={spec['name']}:string({spec['length']})"
                )
            elif field_type == "double":
                field_parts.append(f"&field={spec['name']}:double")
            else:
                field_parts.append(f"&field={spec['name']}:integer")

        uri = (
            f"{geometry_name}?crs={source_layer.crs().authid()}"
            + "".join(field_parts)
        )
        layer = QgsVectorLayer(uri, "Naver History Shapefile Export", "memory")
        provider = layer.dataProvider()
        source_field_names = set(source_layer.fields().names())

        features = []
        for source_feature in source_layer.getFeatures():
            feature = QgsFeature(layer.fields())
            feature.setGeometry(source_feature.geometry())
            attributes = []
            for spec in field_specs:
                source_name = spec["source"]
                value = (
                    source_feature[source_name]
                    if source_name in source_field_names
                    else None
                )
                if value is not None and spec["type"] == "string":
                    value = str(value)
                    max_length = spec["length"]
                    if len(value.encode("utf-8")) > max_length:
                        raise RuntimeError(f"SHP 필드 {source_name}의 UTF-8 폭이 {max_length}바이트를 초과합니다. GeoPackage 또는 GeoJSON으로 저장하세요.")
                attributes.append(value)
            feature.setAttributes(attributes)
            features.append(feature)

        if features:
            if not provider.addFeatures(features)[0]:
                raise RuntimeError("내보내기 피처 복사 실패")
            layer.updateExtents()
        return layer

    @staticmethod
    def _shapefile_sidecar_paths(path):
        return [
            path.with_suffix(extension)
            for extension in (
                ".shp",
                ".shx",
                ".dbf",
                ".prj",
                ".cpg",
                ".qix",
                ".qml",
            )
        ]

    @staticmethod
    def _route_shapefile_fields():
        return history_shapefile_fields("route")

    @staticmethod
    def _guidance_shapefile_fields():
        return history_shapefile_fields("guidance")

    @staticmethod
    def _save_sidecar_style(
        output_path,
        layer_name,
        source_layer,
    ):
        layer = QgsVectorLayer(str(output_path), layer_name, "ogr")
        if not layer.isValid():
            raise RuntimeError(
                f"{output_path.name}을 열어 QML 스타일을 저장하지 못했습니다."
            )

        layer.setRenderer(source_layer.renderer().clone())
        style_path = output_path.with_suffix(".qml")
        error_message, success = layer.saveNamedStyle(str(style_path))
        if not success:
            detail = error_message or "알 수 없는 오류"
            raise RuntimeError(
                f"{style_path.name} 스타일 저장 실패: {detail}"
            )

    def _write_history_layer(
        self,
        source_layer,
        output_path,
        layer_name,
        geometry_name,
    ):
        source_layer = self._normalized_export_layer(source_layer)
        (
            layer_exists,
            existing_ids,
            existing_fields,
        ) = self._existing_history_ids(output_path, layer_name)
        source_fields = {field.name() for field in source_layer.fields()}
        missing_fields = source_fields - existing_fields
        pending_layer = self._history_layer_subset(
            source_layer,
            existing_ids,
            geometry_name,
        )
        pending_count = pending_layer.featureCount()
        if pending_count == 0 and layer_exists and not missing_fields:
            self._repair_saved_guidance_categories(source_layer, output_path, layer_name)
            self._save_history_layer_style(
                output_path,
                layer_name,
                source_layer,
            )
            return 0

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.fileEncoding = "UTF-8"
        options.layerName = layer_name

        if layer_exists:
            options.actionOnExistingFile = (
                WRITE_APPEND_ADD_FIELDS
                if missing_fields
                else WRITE_APPEND_NO_FIELDS
            )
        elif output_path.exists():
            options.actionOnExistingFile = (
                WRITE_OVERWRITE_LAYER
            )
            options.layerOptions = ["SPATIAL_INDEX=YES"]
        else:
            options.actionOnExistingFile = (
                WRITE_OVERWRITE_FILE
            )
            options.layerOptions = ["SPATIAL_INDEX=YES"]

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            pending_layer,
            str(output_path),
            QgsProject.instance().transformContext(),
            options,
        )
        error_code = result[0] if isinstance(result, tuple) else result
        error_value = getattr(error_code, "value", error_code)
        if int(error_value) != 0:
            error_message = ""
            if isinstance(result, tuple) and len(result) > 1:
                error_message = str(result[1] or "")
            detail = error_message or f"오류 코드 {error_value}"
            raise RuntimeError(f"{layer_name} 레이어 저장 실패: {detail}")

        self._repair_saved_guidance_categories(source_layer, output_path, layer_name)
        self._save_history_layer_style(
            output_path,
            layer_name,
            source_layer,
        )

        return pending_count

    @staticmethod
    def _save_history_layer_style(output_path, layer_name, source_layer):
        layer = QgsVectorLayer(
            f"{output_path}|layername={layer_name}",
            layer_name,
            "ogr",
        )
        if not layer.isValid():
            raise RuntimeError(
                f"{layer_name} 레이어를 열어 기본 스타일을 저장하지 못했습니다."
            )

        layer.setRenderer(source_layer.renderer().clone())
        success, error_message = save_style_to_database(
            layer,
            "Naver Map QGIS Bridge",
            "Naver Map QGIS Bridge route history default style",
            True,
        )
        if not success:
            detail = error_message or "알 수 없는 오류"
            raise RuntimeError(
                f"{layer_name} 기본 스타일 저장 실패: {detail}"
            )

    @staticmethod
    def _existing_history_ids(output_path, layer_name):
        if not output_path.exists():
            return False, set(), set()

        layer = QgsVectorLayer(
            f"{output_path}|layername={layer_name}",
            layer_name,
            "ogr",
        )
        if not layer.isValid():
            return False, set(), set()

        history_index = layer.fields().indexOf("history_id")
        if history_index < 0:
            raise RuntimeError(
                f"기존 {layer_name} 레이어에 history_id 필드가 없습니다."
            )
        history_ids = {
            str(feature[history_index])
            for feature in layer.getFeatures()
            if feature[history_index]
        }
        field_names = {field.name() for field in layer.fields()}
        return True, history_ids, field_names

    @staticmethod
    def _history_layer_subset(source_layer, existing_ids, geometry_name):
        subset = QgsVectorLayer(
            f"{geometry_name}?crs={source_layer.crs().authid()}",
            "Naver History Export",
            "memory",
        )
        provider = subset.dataProvider()
        provider.addAttributes(list(source_layer.fields()))
        subset.updateFields()

        features = []
        for source_feature in source_layer.getFeatures():
            if str(source_feature["history_id"]) in existing_ids:
                continue
            feature = QgsFeature(subset.fields())
            feature.setGeometry(source_feature.geometry())
            feature.setAttributes(source_feature.attributes())
            features.append(feature)

        if features:
            if not provider.addFeatures(features)[0]:
                raise RuntimeError("내보내기 피처 복사 실패")
            subset.updateExtents()
        return subset
