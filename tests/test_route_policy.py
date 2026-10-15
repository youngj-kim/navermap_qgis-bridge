# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the real request boundary with synthetic credentials and Qt-free fakes."""
import ast
import json
import math
import unittest
from unittest.mock import Mock

from host_methods import find_method
from navermap_qgis_bridge import constants
from navermap_qgis_bridge.route_inputs import normalize_route_request


class RoutePolicyTests(unittest.TestCase):
    def setUp(self):
        self.request = Mock()
        namespace = {"math": math, "json": json,
                     "normalize_route_request": normalize_route_request,
                     "route_request": self.request,
                     "naver_client_id": lambda: "PLACEHOLDER_ID",
                     "naver_client_secret": lambda: "PLACEHOLDER_SECRET"}
        namespace.update(vars(constants))
        exec(compile(ast.Module(body=[find_method("_request_route")], type_ignores=[]),
                     "search_routes.py", "exec"), namespace)
        self.run_request = namespace["_request_route"]
        self.host = Mock(route_point_feature_ids={}, project_transitioning=False, project_epoch=0)

    def submit(self, avoid, hipass=True):
        self.run_request(self.host, 127, 37, 128, 38, "TIME", "[]",
                         json.dumps(avoid), json.dumps({"car_hipass": hipass}), "A", "B")

    def test_conflicting_avoid_choices_do_not_send_paid_request(self):
        self.submit(["toll", "motorway"])
        self.request.assert_not_called()
        self.host.api_transport.start_route.assert_not_called()
        self.host._set_route_status.assert_called_once()

    def test_unsupported_hipass_never_claimed_on_new_result(self):
        self.submit(["toll"])
        callback = self.host.api_transport.start_route.call_args.args[1]
        callback(Mock())
        self.assertFalse(self.host._handle_route_reply.call_args.args[4]["car_hipass"])
        self.assertEqual(self.request.call_args.args[4], ["toll"])

    def test_transition_during_credential_prompt_cannot_submit(self):
        namespace = self.run_request.__globals__
        namespace["naver_client_secret"] = lambda: ""
        def prompt():
            self.host.project_epoch += 1
            return True
        self.host._prompt_and_save_rest_api_key.side_effect = prompt
        self.submit([])
        self.request.assert_not_called()


class RouteValidationTests(unittest.TestCase):
    def request(self, **changes):
        args = dict(origin_lon=127, origin_lat=37, destination_lon=128, destination_lat=38,
                    priority="TIME", waypoints_json="[]", avoid_json="[]", vehicle_json="{}",
                    origin_label="A", destination_label="B")
        args.update(changes)
        return normalize_route_request(**args)

    def test_bad_coordinate_and_json_shapes(self):
        for changes in ({"origin_lon": float("nan")}, {"origin_lat": 91},
                        {"origin_lon": "127"}, {"avoid_json": '[{}]'},
                        {"waypoints_json": '{}'}, {"vehicle_json": '[]'},
                        {"waypoints_json": '[{"lon":"bad","lat":37}]'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.request(**changes)

    def test_legacy_fuel_and_duplicate_ids(self):
        result = self.request(vehicle_json='{"car_type":7,"car_fuel":"LPG","car_hipass":true}')
        self.assertEqual(result["vehicle_options"], {"car_type":1,"car_fuel":"lpg","car_hipass":False})
        points = [{"id":"waypoint:1","lon":127,"lat":37}] * 2
        with self.assertRaisesRegex(ValueError, "중복"):
            self.request(waypoints_json=json.dumps(points))
