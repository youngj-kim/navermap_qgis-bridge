# SPDX-License-Identifier: GPL-2.0-or-later
"""Validate route input without QGIS, credentials, requests or UI side effects."""
import json
import math
from .constants import (
    ROUTE_PRIORITIES, ROUTE_AVOID_OPTIONS, ROUTE_CAR_TYPES,
    ROUTE_CAR_FUELS, MAX_ROUTE_WAYPOINTS,
)


def normalize_route_request(origin_lon, origin_lat, destination_lon, destination_lat,
                            priority, waypoints_json, avoid_json, vehicle_json,
                            origin_label, destination_label):
    coordinates = (origin_lon, origin_lat, destination_lon, destination_lat)
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool)
               and math.isfinite(value) for value in coordinates):
        raise ValueError('출발지 또는 도착지 좌표가 올바르지 않습니다.')
    if (not -180.0 <= origin_lon <= 180.0 or not -90.0 <= origin_lat <= 90.0
            or not -180.0 <= destination_lon <= 180.0 or not -90.0 <= destination_lat <= 90.0):
        raise ValueError('출발지 또는 도착지 좌표가 범위를 벗어났습니다.')
    if not isinstance(priority, str) or priority not in ROUTE_PRIORITIES:
        priority = 'RECOMMEND'
    try:
        waypoint_data = json.loads(waypoints_json) if waypoints_json else []
    except json.JSONDecodeError:
        raise ValueError('경유지 정보를 해석하지 못했습니다.')
    if not isinstance(waypoint_data, list):
        raise ValueError('경유지 정보 형식이 올바르지 않습니다.')
    if len(waypoint_data) > MAX_ROUTE_WAYPOINTS:
        raise ValueError(f'경유지는 최대 {MAX_ROUTE_WAYPOINTS}개까지 사용할 수 있습니다.')
    try:
        avoid_data = json.loads(avoid_json) if avoid_json else []
    except json.JSONDecodeError:
        raise ValueError('경로 회피 옵션을 해석하지 못했습니다.')
    if not isinstance(avoid_data, list):
        raise ValueError('경로 회피 옵션 형식이 올바르지 않습니다.')
    avoid_options = []
    for value in avoid_data:
        if not isinstance(value, str):
            raise ValueError('경로 회피 옵션 형식이 올바르지 않습니다.')
        if value in ROUTE_AVOID_OPTIONS and value not in avoid_options:
            avoid_options.append(value)
    if len(avoid_options) > 1:
        raise ValueError('경로 회피 옵션은 하나만 선택할 수 있습니다.')
    try:
        vehicle_data = json.loads(vehicle_json) if vehicle_json else {}
    except json.JSONDecodeError:
        raise ValueError('차량 설정을 해석하지 못했습니다.')
    if not isinstance(vehicle_data, dict):
        raise ValueError('차량 설정 형식이 올바르지 않습니다.')
    try:
        car_type = int(vehicle_data.get('car_type', 1))
    except (TypeError, ValueError, OverflowError):
        car_type = 1
    if car_type not in ROUTE_CAR_TYPES:
        car_type = 1
    fuel_map = {'GASOLINE': 'gasoline', 'DIESEL': 'diesel', 'LPG': 'lpg'}
    car_fuel = str(vehicle_data.get('car_fuel', 'gasoline'))
    car_fuel = fuel_map.get(car_fuel, car_fuel)
    if car_fuel not in ROUTE_CAR_FUELS:
        car_fuel = 'gasoline'
    car_hipass = False
    vehicle_options = {'car_type': car_type, 'car_fuel': car_fuel, 'car_hipass': car_hipass}
    # The existing JSON settings envelope carries request language without
    # changing the Qt/HTTP bridge signature or saved vehicle settings.
    language = 'en' if vehicle_data.get('language') == 'en' else 'ko'
    waypoints = []
    point_ids = set()
    for index, item in enumerate(waypoint_data):
        if not isinstance(item, dict):
            raise ValueError('경유지 정보 형식이 올바르지 않습니다.')
        try:
            lon = float(item['lon'])
            lat = float(item['lat'])
        except (KeyError, TypeError, ValueError):
            raise ValueError('경유지 좌표가 올바르지 않습니다.')
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise ValueError('경유지 좌표가 올바르지 않습니다.')
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            raise ValueError('경유지 좌표가 범위를 벗어났습니다.')
        point_id = str(item.get('id') or f'waypoint:{index + 1}')
        if not point_id.startswith('waypoint:'):
            point_id = f'waypoint:{index + 1}'
        if point_id in point_ids:
            raise ValueError('경유지 ID가 중복되었습니다.')
        point_ids.add(point_id)
        waypoints.append({'id': point_id, 'label': str(item.get('label') or '').strip()[:255],
                          'lon': lon, 'lat': lat})
    return dict(priority=priority, waypoints=waypoints, avoid_options=avoid_options,
                vehicle_options=vehicle_options, language=language)
