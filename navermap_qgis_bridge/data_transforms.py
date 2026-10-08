# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure conversions with no QGIS, Qt, network or settings dependencies."""

import math
import re


def normalize_local_search_items(items):
    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        lon = local_search_coordinate(
            item.get("mapx")
            or item.get("longitude")
            or item.get("lon")
            or item.get("x")
        )
        lat = local_search_coordinate(
            item.get("mapy")
            or item.get("latitude")
            or item.get("lat")
            or item.get("y")
        )
        if lon is None or lat is None:
            continue
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            continue

        title = strip_html(str(item.get("title") or "")).strip()
        road_address = str(item.get("roadAddress") or "").strip()
        address = str(item.get("address") or "").strip()
        category = str(item.get("category") or "").strip()
        description = strip_html(
            str(item.get("description") or "")
        ).strip()
        subtitle = road_address or address or category or description
        results.append(
            {
                "title": title or subtitle or "POI 검색 결과",
                "address": subtitle,
                "roadAddress": road_address,
                "jibunAddress": address,
                "category": category,
                "description": description,
                "lon": lon,
                "lat": lat,
                "source": "local",
            }
        )
    return results


def local_search_coordinate(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if abs(number) > 1000:
        number = number / 10000000.0
    return number if math.isfinite(number) else None


def strip_html(value):
    return re.sub(r"<[^>]+>", "", value)


def safe_number(value):
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def safe_float(value):
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def guidance_category(guide_type, guidance):
    if guide_type == 100:
        return "start"
    if guide_type == 101:
        return "destination"
    if guide_type == 1000:
        return "waypoint"
    if guide_type == 3 or "유턴" in guidance:
        return "uturn"
    if 30 <= guide_type <= 41 or 70 <= guide_type <= 81:
        return "roundabout"
    if guide_type in {
        1, 5, 8, 11, 24, 25, 26, 27, 28,
        43, 46, 48, 76, 77, 78, 79, 80, 82,
    } or "좌회전" in guidance or "왼쪽" in guidance:
        return "left"
    if guide_type in {
        2, 6, 9, 12, 18, 19, 20, 21, 22,
        44, 47, 49, 70, 71, 72, 73, 74, 83,
    } or "우회전" in guidance or "오른쪽" in guidance:
        return "right"
    if guide_type in {0, 29} or "직진" in guidance:
        return "straight"
    if guide_type in {
        7, 8, 9, 10, 11, 12, 14, 15, 16, 17,
        42, 43, 44, 45, 46, 47, 48, 49,
        61, 62, 84, 85, 86, 300, 301,
    }:
        return "transition"
    return "other"
