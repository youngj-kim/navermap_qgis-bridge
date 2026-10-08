# SPDX-License-Identifier: GPL-2.0-or-later
"""GPX 1.1 document construction from plain mappings and (lon, lat) tuples."""

import json
import math
from xml.etree import ElementTree as ET

from .data_transforms import safe_float, safe_number


GPX_NS = "http://www.topografix.com/GPX/1/1"
NAVER_NS = "https://yjkim.dev/naver-qgis-bridge"
ROUTE_FIELDS = (
    "history_id", "route_id", "searched_at", "distance_m", "duration_s",
    "guidance_count", "priority", "avoid", "car_type", "car_fuel", "car_hipass",
    "origin_lon", "origin_lat", "origin_name",
    "destination_lon", "destination_lat", "destination_name",
    "waypoints_json", "result_summary",
)
GUIDE_FIELDS = (
    "sequence", "longitude", "latitude", "guidance", "category", "name",
    "guide_type", "distance_m", "duration_s",
)


def build_gpx_document(records, timestamp):
    """Return (ElementTree, route count, guidance count); never access files.

    Each record is (route mapping, coordinate tuples, ordered guide mappings).
    Timestamp is supplied by the caller so exports can be tested deterministically.
    """
    ET.register_namespace("", GPX_NS)
    ET.register_namespace("naver", NAVER_NS)
    root = ET.Element(f"{{{GPX_NS}}}gpx", {
        "version": "1.1", "creator": "Naver Map QGIS Bridge",
    })
    metadata = ET.SubElement(root, f"{{{GPX_NS}}}metadata")
    gpx_text(metadata, "name", "Naver Map QGIS Bridge Route History")
    gpx_text(metadata, "time", timestamp)
    route_total = 0
    guidance_total = 0
    for route, points, guides in records:
        if len(points) < 2:
            continue
        route_total += 1
        guidance_total += len(guides)
        name = gpx_route_name(route)
        desc = str(route["result_summary"] or "")
        append_gpx_waypoints(root, route, guides)
        append_gpx_track(root, name, desc, route, points)
        append_gpx_route(root, name, desc, route, points)
    return ET.ElementTree(root), route_total, guidance_total


def append_gpx_waypoints(root, route_feature, guide_features):
    history_id = str(route_feature["history_id"] or "")
    append_gpx_wpt(
        root,
        safe_float(route_feature["origin_lon"]),
        safe_float(route_feature["origin_lat"]),
        str(route_feature["origin_name"] or "출발지"),
        "origin",
        history_id,
        "출발지",
    )

    for index, waypoint in enumerate(
        waypoints_from_history(route_feature),
        start=1,
    ):
        append_gpx_wpt(
            root,
            safe_float(waypoint.get("lon")),
            safe_float(waypoint.get("lat")),
            str(waypoint.get("label") or f"경유지 {index}"),
            "waypoint",
            history_id,
            f"경유지 {index}",
        )

    append_gpx_wpt(
        root,
        safe_float(route_feature["destination_lon"]),
        safe_float(route_feature["destination_lat"]),
        str(route_feature["destination_name"] or "도착지"),
        "destination",
        history_id,
        "도착지",
    )

    for guide in guide_features:
        sequence = safe_number(guide["sequence"])
        append_gpx_wpt(
            root,
            safe_float(guide["longitude"]),
            safe_float(guide["latitude"]),
            f"{sequence}. {guide['guidance']}",
            f"guidance:{guide['category']}",
            history_id,
            str(guide["name"] or "경로 안내"),
            {
                "sequence": sequence,
                "guide_type": safe_number(guide["guide_type"]),
                "distance_m": safe_number(guide["distance_m"]),
                "duration_s": safe_number(guide["duration_s"]),
            },
        )

def append_gpx_track(root, name, desc, route_feature, points):
    track = ET.SubElement(root, "{http://www.topografix.com/GPX/1/1}trk")
    gpx_text(track, "name", name)
    if desc:
        gpx_text(track, "desc", desc)
    append_gpx_extensions(track, route_feature)
    segment = ET.SubElement(
        track,
        "{http://www.topografix.com/GPX/1/1}trkseg",
    )
    for point in points:
        ET.SubElement(
            segment,
            "{http://www.topografix.com/GPX/1/1}trkpt",
            {
                "lat": f"{point[1]:.8f}",
                "lon": f"{point[0]:.8f}",
            },
        )

def append_gpx_route(root, name, desc, route_feature, points):
    route = ET.SubElement(root, "{http://www.topografix.com/GPX/1/1}rte")
    gpx_text(route, "name", name)
    if desc:
        gpx_text(route, "desc", desc)
    append_gpx_extensions(route, route_feature)
    for point in points:
        ET.SubElement(
            route,
            "{http://www.topografix.com/GPX/1/1}rtept",
            {
                "lat": f"{point[1]:.8f}",
                "lon": f"{point[0]:.8f}",
            },
        )

def append_gpx_wpt(
    root,
    lon,
    lat,
    name,
    point_type,
    history_id,
    desc="",
    extra=None,
):
    if not math.isfinite(lon) or not math.isfinite(lat):
        return
    if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
        return

    waypoint = ET.SubElement(
        root,
        "{http://www.topografix.com/GPX/1/1}wpt",
        {
            "lat": f"{lat:.8f}",
            "lon": f"{lon:.8f}",
        },
    )
    gpx_text(waypoint, "name", name)
    if desc:
        gpx_text(waypoint, "desc", desc)
    gpx_text(waypoint, "type", point_type)

    extensions = ET.SubElement(
        waypoint,
        "{http://www.topografix.com/GPX/1/1}extensions",
    )
    gpx_naver_text(extensions, "history_id", history_id)
    if extra:
        for key, value in extra.items():
            gpx_naver_text(extensions, key, value)

def append_gpx_extensions(parent, route_feature):
    extensions = ET.SubElement(
        parent,
        "{http://www.topografix.com/GPX/1/1}extensions",
    )
    for key in (
        "history_id",
        "route_id",
        "searched_at",
        "distance_m",
        "duration_s",
        "guidance_count",
        "priority",
        "avoid",
        "car_type",
        "car_fuel",
        "car_hipass",
    ):
        gpx_naver_text(extensions, key, route_feature[key])

def gpx_text(parent, tag, value):
    element = ET.SubElement(
        parent,
        f"{{http://www.topografix.com/GPX/1/1}}{tag}",
    )
    element.text = str(value)
    return element

def gpx_naver_text(parent, tag, value):
    element = ET.SubElement(
        parent,
        f"{{https://yjkim.dev/naver-qgis-bridge}}{tag}",
    )
    element.text = str(value if value is not None else "")
    return element

def gpx_route_name(route_feature):
    origin = str(route_feature["origin_name"] or "출발지")
    destination = str(route_feature["destination_name"] or "도착지")
    return f"{origin} → {destination}"

def waypoints_from_history(route_feature):
    try:
        waypoints = json.loads(str(route_feature["waypoints_json"] or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return waypoints if isinstance(waypoints, list) else []
