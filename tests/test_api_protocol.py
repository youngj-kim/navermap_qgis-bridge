# SPDX-License-Identifier: GPL-2.0-or-later
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from navermap_qgis_bridge import api_protocol as api
from navermap_qgis_bridge.data_transforms import normalize_local_search_items
from host_methods import find_method


class ApiProtocolTests(unittest.TestCase):
    def test_poi_parameters(self):
        self.assertEqual(api.local_search_parameters("예시 장소 & A+B"), [
            ("query", "예시 장소 & A+B"), ("display", "5"), ("start", "1"),
            ("sort", "random"), ("format", "json")])

    def test_priority_and_avoid_precedence(self):
        for priority, expected in [("RECOMMEND", "traoptimal"), ("TIME", "trafast"),
                                   ("DISTANCE", "tracomfort"), ("unknown", "traoptimal")]:
            self.assertEqual(api.route_option(priority, []), expected)
            self.assertEqual(api.route_option(priority, ["motorway"]), "traavoidcaronly")
            self.assertEqual(api.route_option(priority, ["motorway", "toll"]), "traavoidtoll")

    def test_route_parameters_and_precision(self):
        self.assertEqual(api.route_parameters((127.1, 37.4), (127.2, 37.5), "TIME", [
            {"lon": 127.15, "lat": 37.45}, {"lon": 127.16, "lat": 37.46}
        ], [], 1, "gasoline"), [
            ("start", "127.10000000,37.40000000"), ("goal", "127.20000000,37.50000000"),
            ("waypoints", "127.15000000,37.45000000|127.16000000,37.46000000"),
            ("option", "trafast"), ("cartype", "1"), ("fueltype", "gasoline"), ("lang", "ko")])
        parameters = dict(api.route_parameters((127, 37), (128, 38), "TIME", [], ["toll"], 6, "lpg"))
        self.assertNotIn("waypoints", parameters)
        self.assertEqual(parameters["option"], "traavoidtoll")

    def test_decode_payload(self):
        payload = {"items": [{"title": "예시"}]}
        self.assertEqual(api.decode_payload(json.dumps(payload).encode("utf-8")), payload)
        for data in [b"", b"not-json", b"\xff", b"[]", b"null", b'"text"', b"123"]:
            with self.subTest(data=data):
                self.assertEqual(api.decode_payload(data), {})

    def test_route_language_default_and_whitelist(self):
        for language, expected in [("en", "en"), ("ko", "ko"), (None, "ko"), ("ja", "ko"), ([], "ko")]:
            with self.subTest(language=language):
                params = dict(api.route_parameters((127, 37), (128, 38), "TIME", [], [], 1, "gasoline", language))
                self.assertEqual(params["lang"], expected)

    def test_local_error_precedence(self):
        cases = [({"errorMessage": "first", "error": {"message": "second"}}, "first"),
                 ({"error": {"message": "nested", "details": "detail"}}, "nested"),
                 ({"error": {"details": "detail"}}, "detail"),
                 ({"error": "bad", "message": "message"}, "message"),
                 ({"errMsg": "last"}, "last"), ({}, "network")]
        for payload, expected in cases:
            self.assertEqual(api.local_search_error(payload, "network", 403), expected)
        self.assertEqual(api.local_search_error({}, "", 403), "HTTP 403")

    def test_route_error_precedence(self):
        self.assertEqual(api.route_error({"msg": "first", "message": "second"}, "network", 500), "first")
        self.assertEqual(api.route_error({"message": "second"}, "network", 500), "second")
        self.assertEqual(api.route_error({}, "network", 500), "network")
        self.assertEqual(api.route_error({}, "", 500), "HTTP 500")

    def test_search_item_envelopes(self):
        items = [{"title": "예시"}]
        self.assertEqual(api.local_search_items({"items": items}), items)
        self.assertEqual(api.local_search_items({"data": {"items": items}}), items)
        self.assertEqual(api.local_search_items({"items": items, "data": {"items": ["other"]}}), items)
        self.assertEqual(api.local_search_items({"data": []}), [])


class QtRequestBoundaryTests(unittest.TestCase):
    def setUp(self):
        # Execute the real boundary functions with fake Qt constructors; no live keys.
        source = Path(__file__).resolve().parents[1] / "navermap_qgis_bridge" / "api_requests.py"
        tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        url = Mock()
        query = Mock()
        request = Mock()
        self.url, self.query, self.request = url, query, request
        self.namespace = {
            "validated_credential": __import__("navermap_qgis_bridge.credential_validation", fromlist=["validated_credential"]).validated_credential,
            "QUrl": Mock(return_value=url), "QUrlQuery": Mock(return_value=query),
            "QNetworkRequest": Mock(return_value=request),
            "LOCAL_SEARCH_ENDPOINT": api.LOCAL_SEARCH_ENDPOINT,
            "ROUTE_ENDPOINT": api.ROUTE_ENDPOINT,
            "local_search_parameters": api.local_search_parameters,
            "route_parameters": api.route_parameters,
        }
        self.namespace["QNetworkRequest"].Attribute = SimpleNamespace(HttpStatusCodeAttribute="status")
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        exec(compile(ast.Module(body=functions, type_ignores=[]), "api_requests.py", "exec"), self.namespace)

    def test_poi_request_headers_and_query(self):
        result = self.namespace["local_search_request"]("예시 & +", "PLACEHOLDER_ID", "PLACEHOLDER_SECRET")
        self.assertIs(result, self.request)
        self.namespace["QUrl"].assert_called_once_with(api.LOCAL_SEARCH_ENDPOINT)
        self.url.setQuery.assert_called_once_with(self.query)
        self.assertEqual(self.query.addQueryItem.call_args_list[0].args, ("query", "예시 & +"))
        self.assertEqual([c.args for c in self.request.setRawHeader.call_args_list], [
            (b"X-NCP-APIGW-API-KEY-ID", b"PLACEHOLDER_ID"),
            (b"X-NCP-APIGW-API-KEY", b"PLACEHOLDER_SECRET")])

    def test_route_request_headers_and_query(self):
        result = self.namespace["route_request"]((127, 37), (128, 38), "TIME", [], [],
                                                  1, "gasoline", "PLACEHOLDER_ID", "PLACEHOLDER_SECRET")
        self.assertIs(result, self.request)
        self.namespace["QUrl"].assert_called_once_with(api.ROUTE_ENDPOINT)
        self.assertEqual([c.args for c in self.query.addQueryItem.call_args_list],
                         api.route_parameters((127, 37), (128, 38), "TIME", [], [], 1, "gasoline"))
        self.assertEqual([c.args for c in self.request.setRawHeader.call_args_list], [
            (b"x-ncp-apigw-api-key-id", b"PLACEHOLDER_ID"),
            (b"x-ncp-apigw-api-key", b"PLACEHOLDER_SECRET"), (b"Content-Type", b"application/json")])

    def test_english_language_reaches_qt_query(self):
        self.namespace["route_request"]((127, 37), (128, 38), "TIME", [], [],
                                       1, "gasoline", "PLACEHOLDER_ID", "PLACEHOLDER_SECRET", language="en")
        self.assertIn(("lang", "en"), [call.args for call in self.query.addQueryItem.call_args_list])

    def test_reply_read_before_deletion(self):
        reply = Mock()
        reply.attribute.return_value = 200
        reply.readAll.return_value = b'{}'
        reply.error.return_value = 0
        reply.errorString.return_value = ""
        self.assertEqual(self.namespace["read_reply"](reply), (200, b'{}', 0, ""))
        self.assertEqual([c[0] for c in reply.mock_calls],
                         ["attribute", "readAll", "error", "errorString", "deleteLater"])


class PluginResponseIntegrationTests(unittest.TestCase):
    def setUp(self):
        methods = [find_method(name) for name in
                   ("_process_local_search_reply", "_handle_route_reply", "_process_route_reply")]
        self.reader = Mock()
        self.namespace = {"read_reply": self.reader, "decode_payload": api.decode_payload,
                          "local_search_error": api.local_search_error,
                          "route_error": api.route_error, "route_option": api.route_option,
                          "local_search_items": api.local_search_items,
                          "QNetworkReply": SimpleNamespace(NetworkError=SimpleNamespace(NoError=0)),
                          "QgsMessageLog": Mock(), "LOG_TAG": "test", "MSG_WARNING": 1, "MSG_CRITICAL": 2}
        exec(compile(ast.Module(body=methods, type_ignores=[]), "plugin.py", "exec"), self.namespace)

    def test_poi_response_delivery_and_stale_reply(self):
        for status, body, success in [(200, {"data": {"items": [{"lon": 127, "lat": 37}]}}, True),
                                     (403, {"error": {"message": "denied"}}, False)]:
            plugin, reply = Mock(), Mock()
            plugin.local_search_replies = {reply: "test-request"}
            plugin._normalize_local_search_items.side_effect = normalize_local_search_items
            self.reader.return_value = (status, json.dumps(body).encode(), 0, "")
            self.namespace["_process_local_search_reply"](plugin, reply)
            args = plugin._emit_local_search_results.call_args.args
            self.assertEqual(args[:2], ("test-request", success))
            self.assertEqual(len(args[3]), 1 if success else 0)
            self.assertEqual(plugin.local_search_replies, {})
        plugin, reply = Mock(), Mock()
        plugin.local_search_replies = {}
        self.reader.reset_mock()
        self.namespace["_process_local_search_reply"](plugin, reply)
        self.reader.assert_not_called()
        reply.deleteLater.assert_called_once()

    def test_route_error_and_malformed_response(self):
        for status, raw, expected in [(403, b'{"msg":"denied"}', "경로 탐색 실패: denied"),
                                      (200, b'[]', "경로 탐색 결과가 없습니다."),
                                      (200, b'{"code":1,"message":"none"}', "none"),
                                      (200, b'{"code":"invalid"}', "경로 응답 처리 또는 이력 저장에 실패했습니다."),
                                      (200, b'{"route":[]}', "경로 탐색 결과가 없습니다."),
                                      (200, b'{"route":[1]}', "경로 응답 처리 또는 이력 저장에 실패했습니다.")]:
            plugin, reply = Mock(), Mock()
            plugin.route_reply = reply
            plugin._process_route_reply.side_effect = lambda *args: self.namespace["_process_route_reply"](plugin, *args)
            self.reader.return_value = (status, raw, 0, "")
            self.namespace["_handle_route_reply"](
                plugin, reply, "RECOMMEND", [], [], {}, (127, 37), (128, 38), "출발", "도착")
            plugin._set_route_status.assert_called_once_with(False, expected)
            self.assertIsNone(plugin.route_reply)


if __name__ == "__main__":
    unittest.main()
