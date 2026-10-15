# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure conversions with no QGIS, Qt, network or settings dependencies."""

import html
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
    return html.unescape(re.sub(r"<[^>]+>", "", value))


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
    # NAVER Directions 5: https://api.ncloud-docs.com/docs/application-maps-directions5
    # Known codes take precedence over localized instruction text.
    if guide_type == 88:
        return "destination"
    if guide_type == 87:
        return "waypoint"
    if 21 <= guide_type <= 34 or 91 <= guide_type <= 104:
        return "roundabout"
    if guide_type == 6:
        return "uturn"
    if guide_type in {2, 4, 8, 11, 12, 13}:
        return "left"
    if guide_type in {3, 5, 14, 15, 16}:
        return "right"
    if guide_type == 1:
        return "straight"
    if guide_type in {41, 42, 47, 48, 49, *range(50, 61), *range(62, 70), *range(71, 83), 121, 122, 123}:
        return "transition"
    guidance = str(guidance or "")
    if "회전 교차로" in guidance or "로터리" in guidance:
        return "roundabout"
    if "유턴" in guidance:
        return "uturn"
    if "좌회전" in guidance or "왼쪽" in guidance:
        return "left"
    if "우회전" in guidance or "오른쪽" in guidance:
        return "right"
    if "직진" in guidance:
        return "straight"
    return "other"
