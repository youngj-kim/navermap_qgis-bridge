# SPDX-License-Identifier: GPL-2.0-or-later
"""Checked memory-provider mutations and validation of imported history pairs."""
from contextlib import contextmanager
from functools import wraps
import json
import math

from qgis.core import QgsFeature, QgsCoordinateReferenceSystem, QgsWkbTypes
from .data_transforms import guidance_category
from .compat import WKB_LINESTRING, WKB_POINT


def checked_add(layer, features):
    if features and not layer.dataProvider().addFeatures(features)[0]:
        raise RuntimeError("이력 피처를 저장하지 못했습니다.")
    layer.updateExtents()


@contextmanager
def history_transaction(*layers):
    snapshots = [(layer, [QgsFeature(f) for f in layer.getFeatures()]) for layer in layers]
    try:
        yield
    except Exception as original:
        try:
            for layer, features in snapshots:
                ids = [f.id() for f in layer.getFeatures()]
                if ids and not layer.dataProvider().deleteFeatures(ids):
                    raise RuntimeError("이력 복구 중 삭제 실패")
                checked_add(layer, features)
        except Exception as rollback:
            raise RuntimeError("이력 작업과 복구가 실패했습니다. 세션 이력을 확인하세요.") from rollback
        raise RuntimeError(str(original)) from original


def normalize_guidance_feature(feature):
    feature["category"] = guidance_category(int(feature["guide_type"]), str(feature["guidance"] or ""))


def validate_import_pair(routes, guidance, value):
    """Validate the complete source before mutating either destination layer."""
    for layer, geometry in ((routes, WKB_LINESTRING), (guidance, WKB_POINT)):
        if layer.crs() != QgsCoordinateReferenceSystem("EPSG:4326"):
            raise RuntimeError("이력 좌표계는 EPSG:4326이어야 합니다.")
        if QgsWkbTypes.flatType(layer.wkbType()) != geometry:
            raise RuntimeError("이력 지오메트리 타입이 올바르지 않습니다.")
        for feature in layer.getFeatures():
            shape = feature.geometry()
            if shape.isNull() or shape.isEmpty() or not shape.isGeosValid():
                raise RuntimeError("빈 이력 지오메트리입니다.")
            for point in shape.vertices():
                if not valid_coordinate(point.x(), point.y()):
                    raise RuntimeError("이력 좌표 범위가 올바르지 않습니다.")
    route_ids, expected, counts, sequences = set(), {}, {}, set()
    try:
        for feature in routes.getFeatures():
            def get(name, short):
                return value(feature, set(routes.fields().names()), name, short)
            identifier = str(get("history_id", "hist_id") or "")
            if not identifier or identifier in route_ids:
                raise ValueError("경로 이력 ID 누락 또는 중복")
            route_ids.add(identifier)
            expected[identifier] = int(get("guidance_count", "guide_cnt"))
            if expected[identifier] < 0:
                raise ValueError("안내 개수 오류")
            for prefix, short in (("origin", "org"), ("destination", "dst")):
                if not valid_coordinate(get(prefix + "_lon", short + "_lon"), get(prefix + "_lat", short + "_lat")):
                    raise ValueError("출발·도착 좌표 범위 오류")
            waypoints = json.loads(str(get("waypoints_json", "waypts") or "[]"))
            if not isinstance(waypoints, list) or len(waypoints) > 5:
                raise ValueError("경유지 형식 오류")
            for point in waypoints:
                if not isinstance(point, dict) or not valid_coordinate(point.get("lon"), point.get("lat")):
                    raise ValueError("경유지 좌표 범위 오류")
            for name, short in (("distance_m", "dist_m"), ("duration_s", "dur_s")):
                if int(get(name, short)) < 0:
                    raise ValueError("거리·시간 범위 오류")
        for feature in guidance.getFeatures():
            def get(name, short):
                return value(feature, set(guidance.fields().names()), name, short)
            identifier = str(get("history_id", "hist_id") or "")
            sequence = int(get("sequence", "seq"))
            if identifier not in route_ids or sequence < 1 or (identifier, sequence) in sequences:
                raise ValueError("안내 이력 ID 또는 순서 오류")
            sequences.add((identifier, sequence))
            int(get("guide_type", "g_type"))
            lon, lat = get("longitude", "lon"), get("latitude", "lat")
            if not valid_coordinate(lon, lat):
                raise ValueError("안내 좌표 범위 오류")
            point = feature.geometry().asPoint()
            # Older memory double fields rounded attributes to five decimals,
            # while the geometry retained the original API coordinates.
            # Allow half that decimal unit, with a small floating-point margin.
            if not math.isclose(float(lon), point.x(), rel_tol=0, abs_tol=5.000001e-6) or not math.isclose(float(lat), point.y(), rel_tol=0, abs_tol=5.000001e-6):
                raise ValueError("안내 속성과 지오메트리 좌표 불일치")
            for name, short in (("distance_m", "dist_m"), ("duration_s", "dur_s"),
                                ("cum_distance_m", "cum_dist"), ("cum_duration_s", "cum_dur"), ("road_index", "road_idx")):
                if int(get(name, short)) < 0:
                    raise ValueError("안내 거리·시간·인덱스 범위 오류")
            counts[identifier] = counts.get(identifier, 0) + 1
        if any(counts.get(identifier, 0) != count or any((identifier, seq) not in sequences for seq in range(1, count + 1)) for identifier, count in expected.items()):
            raise ValueError("경로와 안내 개수 불일치")
    except (ValueError, TypeError, OverflowError) as exc:
        raise RuntimeError("가져올 이력이 올바르지 않습니다: " + str(exc)) from exc


def valid_coordinate(lon, lat):
    try:
        return math.isfinite(float(lon)) and math.isfinite(float(lat)) and -180 <= float(lon) <= 180 and -90 <= float(lat) <= 90
    except (ValueError, TypeError, OverflowError):
        return False


def history_dialog_operation(method):
    """Prevent nested file/delete dialogs while Qt processes modal events."""
    @wraps(method)
    def guarded(self, *args, **kwargs):
        if getattr(self, "_history_dialog_active", False) or self.project_transitioning:
            return
        self._history_dialog_active = True
        try:
            return method(self, *args, **kwargs)
        finally:
            self._history_dialog_active = False
    return guarded
