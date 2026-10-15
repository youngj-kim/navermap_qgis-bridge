# SPDX-License-Identifier: GPL-2.0-or-later
"""SearchRouteMixin: behavior-preserving host methods; state is owned by the plugin."""

import math
from datetime import datetime
from uuid import uuid4
from qgis.core import QgsMessageLog, QgsPointXY
from qgis.PyQt.QtNetwork import QNetworkReply
from .compat import MSG_CRITICAL, MSG_WARNING
from .data_transforms import (
    local_search_coordinate,
    normalize_local_search_items,
    strip_html,
)
from .api_protocol import (
    decode_payload,
    local_search_error,
    local_search_items,
    route_error,
    route_option,
)
from .api_requests import local_search_request, read_reply, route_request
from .fare_values import route_fares
from .route_inputs import normalize_route_request
from .settings import (
    naver_client_id,
    naver_client_secret,
    naver_api_hub_client_id,
    naver_api_hub_client_secret,
)
from .constants import (
    LOG_TAG,
    ROUTE_PRIORITIES,
    ROUTE_AVOID_OPTIONS,
    ROUTE_CAR_TYPES,
    ROUTE_CAR_FUELS,
)


class SearchRouteMixin:
    def _request_local_search(self, request_id, query):
        if self.project_transitioning:
            return
        epoch = self.project_epoch
        request_id = str(request_id or "").strip()
        query = str(query or "").strip()
        if not request_id:
            return
        if not query:
            self._emit_local_search_results(
                request_id,
                False,
                "검색어를 입력하세요.",
                [],
            )
            return

        client_id = naver_api_hub_client_id()
        client_secret = naver_api_hub_client_secret()
        if not client_id:
            if not self._prompt_and_save_api_hub_client_id():
                self._emit_local_search_results(
                    request_id,
                    False,
                    "Naver API HUB Client ID가 필요합니다.",
                    [],
                )
                return
            client_id = naver_api_hub_client_id()
        if not client_secret:
            if not self._prompt_and_save_api_hub_client_secret():
                self._emit_local_search_results(
                    request_id,
                    False,
                    "Naver API HUB Client Secret이 필요합니다.",
                    [],
                )
                return
            client_secret = naver_api_hub_client_secret()

        if self.project_transitioning or epoch != self.project_epoch:
            return
        try:
            request = local_search_request(query, client_id, client_secret)
        except ValueError as exc:
            self._emit_local_search_results(request_id, False, str(exc), [])
            return

        self.api_transport.start_search(
            request, request_id, self._handle_local_search_reply,
            self._handle_local_search_timeout,
        )

    def _handle_local_search_reply(self, reply):
        request_id = self.local_search_replies.get(reply, "")
        try:
            self._process_local_search_reply(reply)
        except Exception as exc:
            self.local_search_replies.pop(reply, None)
            try:
                reply.deleteLater()
            except RuntimeError:
                pass
            QgsMessageLog.logMessage(
                f"POI 검색 응답 처리 실패: {exc}",
                LOG_TAG,
                MSG_CRITICAL,
            )
            if request_id:
                self._emit_local_search_results(
                    request_id,
                    False,
                    f"POI 검색 응답 처리 실패: {exc}",
                    [],
                )

    def _process_local_search_reply(self, reply):
        request_id = self.local_search_replies.pop(reply, "")
        if not request_id:
            reply.deleteLater()
            return

        status_code, raw_data, network_error, network_error_message = read_reply(reply)
        payload = decode_payload(raw_data)

        if (
            network_error != QNetworkReply.NetworkError.NoError
            or status_code != 200
        ):
            message = local_search_error(payload, network_error_message, status_code)
            QgsMessageLog.logMessage(
                f"POI 검색 실패: HTTP {status_code}, {message}",
                LOG_TAG,
                MSG_WARNING,
            )
            self._emit_local_search_results(
                request_id,
                False,
                f"POI 검색 실패: {message}",
                [],
            )
            return

        items = local_search_items(payload)
        results = self._normalize_local_search_items(items)
        if not results and items:
            QgsMessageLog.logMessage(
                "POI 검색 응답에 사용할 수 있는 좌표가 없습니다.",
                LOG_TAG,
                MSG_WARNING,
            )
        self._emit_local_search_results(
            request_id,
            True,
            f"POI 검색 결과: {len(results)}건",
            results,
        )

    def _handle_local_search_timeout(self, reply):
        request_id = self.local_search_replies.pop(reply, "")
        if not request_id:
            return
        try:
            reply.abort()
            reply.deleteLater()
        except RuntimeError:
            pass
        QgsMessageLog.logMessage(
            "POI 검색 요청 시간이 초과되었습니다.",
            LOG_TAG,
            MSG_WARNING,
        )
        self._emit_local_search_results(
            request_id,
            False,
            "POI 검색 요청 시간이 초과되었습니다.",
            [],
        )

    def _emit_local_search_results(self, request_id, success, message, results):
        payload = {
            "request_id": request_id,
            "success": bool(success),
            "message": str(message),
            "results": results,
        }
        self.viewer_messages.publish("local_search_results", payload)

    def _normalize_local_search_items(self, items):
        return normalize_local_search_items(items)

    @staticmethod
    def _local_search_coordinate(value):
        return local_search_coordinate(value)

    @staticmethod
    def _strip_html(value):
        return strip_html(value)

    def _request_route(
        self,
        origin_lon,
        origin_lat,
        destination_lon,
        destination_lat,
        priority,
        waypoints_json,
        avoid_json,
        vehicle_json,
        origin_label,
        destination_label,
    ):
        if self.project_transitioning:
            return
        epoch = self.project_epoch
        try:
            inputs = normalize_route_request(
                origin_lon, origin_lat, destination_lon, destination_lat, priority,
                waypoints_json, avoid_json, vehicle_json, origin_label, destination_label,
            )
        except ValueError as exc:
            self._set_route_status(False, str(exc))
            return
        priority = inputs["priority"]
        waypoints = inputs["waypoints"]
        avoid_options = inputs["avoid_options"]
        vehicle_options = inputs["vehicle_options"]
        car_type, car_fuel = vehicle_options["car_type"], vehicle_options["car_fuel"]

        self._set_route_point("origin", origin_lon, origin_lat)
        self._set_route_point("destination", destination_lon, destination_lat)
        active_waypoint_ids = {waypoint["id"] for waypoint in waypoints}
        for point_id in list(self.route_point_feature_ids):
            if (
                point_id.startswith("waypoint:")
                and point_id not in active_waypoint_ids
            ):
                self._clear_route_point(point_id)
        for waypoint in waypoints:
            self._set_route_point(
                waypoint["id"],
                waypoint["lon"],
                waypoint["lat"],
            )

        client_id = naver_client_id()
        client_secret = naver_client_secret()
        if not client_secret:
            if not self._prompt_and_save_rest_api_key():
                self._set_route_status(False, "Naver Client Secret이 필요합니다.")
                return
            client_secret = naver_client_secret()

        if self.project_transitioning or epoch != self.project_epoch:
            return
        self.api_transport.cancel_route()

        try:
            request = route_request(
                (origin_lon, origin_lat), (destination_lon, destination_lat),
                priority, waypoints, avoid_options, car_type, car_fuel,
                client_id, client_secret,
            )
        except ValueError as exc:
            self._set_route_status(False, str(exc))
            return

        self.api_transport.start_route(
            request,
            lambda current_reply: self._handle_route_reply(
                current_reply,
                priority,
                waypoints,
                avoid_options,
                vehicle_options,
                (origin_lon, origin_lat),
                (destination_lon, destination_lat),
                str(origin_label).strip()[:255],
                str(destination_label).strip()[:255],
            ),
            lambda: self._set_route_status(False, "경로 응답 시간이 초과되었습니다. 다시 조회하세요."),
        )

    def _cancel_route(self):
        self.api_transport.cancel_route()
        self._set_route_status(False, "경로 탐색을 취소했습니다.")

    def _handle_route_reply(
        self,
        reply,
        priority,
        waypoints,
        avoid_options,
        vehicle_options,
        origin,
        destination,
        origin_label,
        destination_label,
    ):
        try:
            self._process_route_reply(reply, priority, waypoints, avoid_options, vehicle_options,
                                      origin, destination, origin_label, destination_label)
        except Exception:
            self._set_route_status(False, "경로 응답 처리 또는 이력 저장에 실패했습니다.")
            QgsMessageLog.logMessage("경로 응답 처리 또는 이력 저장 실패", LOG_TAG, MSG_CRITICAL)

    def _process_route_reply(self, reply, priority, waypoints, avoid_options, vehicle_options,
                             origin, destination, origin_label, destination_label):
        if reply is not self.route_reply:
            reply.deleteLater()
            return

        self.route_reply = None
        status_code, raw_data, network_error, network_error_message = read_reply(reply)
        payload = decode_payload(raw_data)

        if (
            network_error != QNetworkReply.NetworkError.NoError
            or status_code != 200
        ):
            message = route_error(payload, network_error_message, status_code)
            self._set_route_status(False, f"경로 탐색 실패: {message}")
            return

        if int(payload.get("code") or 0) != 0:
            self._set_route_status(
                False,
                payload.get("message") or "경로를 찾지 못했습니다.",
            )
            return

        points = []
        route_key = route_option(priority, avoid_options)
        route = ((payload.get("route") or {}).get(route_key) or [None])[0]
        if route is None:
            self._set_route_status(False, "경로 탐색 결과가 없습니다.")
            return

        for coordinate in route.get("path") or []:
            if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
                continue
            try:
                point = QgsPointXY(float(coordinate[0]), float(coordinate[1]))
            except (TypeError, ValueError, OverflowError):
                continue
            if not all(math.isfinite(value) for value in (point.x(), point.y())) or not -180 <= point.x() <= 180 or not -90 <= point.y() <= 90:
                continue
            if not points or point != points[-1]:
                points.append(point)

        if len(points) < 2:
            self._set_route_status(False, "경로 선형 좌표를 찾지 못했습니다.")
            return

        summary = route.get("summary") or {}
        fares = route_fares(summary)
        distance = int(summary.get("distance") or 0)
        duration = int(round(int(summary.get("duration") or 0) / 1000))
        if distance < 0 or duration < 0:
            raise ValueError("Negative route distance or duration")
        waypoint_count = len(waypoints)
        route_id = str(payload.get("currentDateTime") or uuid4())
        history_id = str(uuid4())
        searched_at = datetime.now().astimezone().isoformat(timespec="seconds")
        guides = self._extract_route_guides(route, route_id)
        guidance_count = len(guides)
        result_summary = self._route_result_summary(
            distance,
            duration,
            vehicle_options["car_type"],
            guidance_count,
        )
        self._create_route_layer(
            points,
            distance,
            duration,
            guidance_count,
            result_summary,
            priority,
            waypoint_count,
            avoid_options,
            vehicle_options,
        )
        guidance_payload = {
            "history_id": history_id,
            "route_id": route_id,
            "summary": {
                "distance_m": distance,
                "duration_s": duration,
                **fares,
                "guidance_count": guidance_count,
                "result_summary": result_summary,
                "priority": priority,
                "waypoint_count": waypoint_count,
                "avoid": avoid_options,
                "vehicle": vehicle_options,
            },
            "path": self._route_path_payload(points),
            "guides": guides,
        }
        self._create_route_guidance_layer(guides)
        self._append_route_history(
            history_id=history_id,
            route_id=route_id,
            searched_at=searched_at,
            points=points,
            origin=origin,
            destination=destination,
            origin_label=origin_label,
            destination_label=destination_label,
            waypoints=waypoints,
            distance=distance,
            duration=duration,
            guidance_count=guidance_count,
            result_summary=result_summary,
            priority=priority,
            avoid_options=avoid_options,
            vehicle_options=vehicle_options,
            guides=guides,
            **fares,
        )
        self.active_route_history_id = history_id
        self.viewer_messages.publish("route_guidance", guidance_payload)

        distance_text = f"{distance / 1000:.1f} km"
        duration_text = f"{max(1, round(duration / 60))}분"
        priority_text = (ROUTE_AVOID_OPTIONS[avoid_options[0]] if avoid_options
                         else ROUTE_PRIORITIES.get(priority, ROUTE_PRIORITIES["RECOMMEND"]))
        waypoint_text = f", 경유지 {waypoint_count}개" if waypoint_count else ""
        avoid_text = ""
        if avoid_options:
            labels = [ROUTE_AVOID_OPTIONS[value] for value in avoid_options]
            avoid_text = f", 회피: {', '.join(labels)}"
        vehicle_text = (
            f", 차량: {ROUTE_CAR_TYPES[vehicle_options['car_type']]}/"
            f"{ROUTE_CAR_FUELS[vehicle_options['car_fuel']]}"
        )
        message = (
            f"{priority_text} 경로 생성 완료: {distance_text}, "
            f"예상 {duration_text}{waypoint_text}{avoid_text}{vehicle_text}"
        )
        self._set_route_status(True, message)
        self.iface.messageBar().pushSuccess("Naver Map QGIS Bridge", message)

    def _extract_route_guides(self, route, route_id):
        guides = []
        cumulative_distance = 0
        cumulative_duration = 0
        path = route.get("path") or []

        for guide in route.get("guide") or []:
            try:
                point_index = int(guide.get("pointIndex") or 0)
                if not 0 <= point_index < len(path):
                    continue
                coordinate = path[point_index]
                lon = float(coordinate[0])
                lat = float(coordinate[1])
                guide_type = int(guide.get("type") or 0)
                distance = max(0, int(guide.get("distance") or 0))
                duration = max(0, int(round(int(guide.get("duration") or 0) / 1000)))
            except (AttributeError, IndexError, TypeError, ValueError, OverflowError):
                continue
            if not math.isfinite(lon) or not math.isfinite(lat):
                continue
            if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
                continue

            cumulative_distance += distance
            cumulative_duration += duration
            guidance = str(guide.get("instructions") or "").strip()
            guides.append(
                {
                    "route_id": route_id,
                    "sequence": len(guides) + 1,
                    "section_no": 1,
                    "guide_type": guide_type,
                    "category": self._guidance_category(
                        guide_type,
                        guidance,
                    ),
                    "guidance": guidance or "경로 안내",
                    "name": guidance,
                    "distance_m": distance,
                    "duration_s": duration,
                    "cumulative_distance_m": cumulative_distance,
                    "cumulative_duration_s": cumulative_duration,
                    "road_index": point_index,
                    "longitude": lon,
                    "latitude": lat,
                }
            )

        return guides
