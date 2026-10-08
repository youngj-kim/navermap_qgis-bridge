# SPDX-License-Identifier: GPL-2.0-or-later
MENU_NAME = "&Naver Map QGIS Bridge"
LOG_TAG = "Naver Map QGIS Bridge"
ROUTE_PRIORITIES = {
    "RECOMMEND": "실시간 최적",
    "TIME": "실시간 빠른길",
    "DISTANCE": "실시간 편한길",
}
ROUTE_AVOID_OPTIONS = {
    "toll": "무료 우선",
    "motorway": "자동차전용도로 회피",
}
ROUTE_CAR_TYPES = {
    1: "소형",
    2: "중형",
    3: "대형",
    4: "대형 화물",
    5: "특수 화물",
    6: "경차",
}
ROUTE_CAR_FUELS = {
    "gasoline": "휘발유",
    "highgradegasoline": "고급 휘발유",
    "diesel": "경유",
    "lpg": "LPG",
    "GASOLINE": "휘발유",
    "DIESEL": "경유",
    "LPG": "LPG",
}
MAX_ROUTE_WAYPOINTS = 5
HISTORY_SCHEMA_VERSION = 2
ROUTE_HISTORY_LAYER_NAME = "naver_route_history"
GUIDANCE_HISTORY_LAYER_NAME = "naver_guidance_history"
