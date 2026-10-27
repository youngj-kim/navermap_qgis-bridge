# SPDX-License-Identifier: GPL-2.0-or-later
"""NAVER request parameters and JSON response interpretation, without Qt."""

import json


ROUTE_ENDPOINT = "https://maps.apigw.ntruss.com/map-direction/v1/driving"
LOCAL_SEARCH_ENDPOINT = "https://naverapihub.apigw.ntruss.com/search/v1/local"
NAVER_ROUTE_OPTIONS = {
    "RECOMMEND": "traoptimal",
    "TIME": "trafast",
    "DISTANCE": "tracomfort",
}


def route_option(priority, avoid_options):
    # Preserve existing precedence when both avoid options are selected.
    if "toll" in avoid_options:
        return "traavoidtoll"
    if "motorway" in avoid_options:
        return "traavoidcaronly"
    return NAVER_ROUTE_OPTIONS.get(priority, "traoptimal")


def local_search_parameters(query):
    return [("query", query), ("display", "5"), ("start", "1"),
            ("sort", "random"), ("format", "json")]


def route_parameters(origin, destination, priority, waypoints, avoid_options,
                     car_type, car_fuel, language="ko"):
    parameters = [
        ("start", f"{origin[0]:.8f},{origin[1]:.8f}"),
        ("goal", f"{destination[0]:.8f},{destination[1]:.8f}"),
    ]
    if waypoints:
        parameters.append(("waypoints", "|".join(
            f'{point["lon"]:.8f},{point["lat"]:.8f}' for point in waypoints)))
    parameters.extend([
        ("option", route_option(priority, avoid_options)),
        ("cartype", str(car_type)), ("fueltype", car_fuel),
        ("lang", "en" if language == "en" else "ko"),
    ])
    return parameters


def decode_payload(raw_data):
    try:
        payload = json.loads(raw_data.decode("utf-8")) if raw_data else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def local_search_error(payload, network_message, status_code):
    nested = payload.get("error")
    if not isinstance(nested, dict):
        nested = {}
    return (payload.get("errorMessage") or nested.get("message")
            or nested.get("details") or payload.get("message")
            or payload.get("errMsg") or network_message or f"HTTP {status_code}")


def route_error(payload, network_message, status_code):
    return (payload.get("msg") or payload.get("message")
            or network_message or f"HTTP {status_code}")


def local_search_items(payload):
    items = payload.get("items") or []
    data = payload.get("data")
    if not items and isinstance(data, dict):
        items = data.get("items") or []
    return items
