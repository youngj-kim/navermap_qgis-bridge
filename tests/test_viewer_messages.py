# SPDX-License-Identifier: GPL-2.0-or-later
import ast
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from navermap_qgis_bridge.viewer_messages import PAYLOAD_MESSAGES, ViewerMessages
from host_methods import find_method


class ViewerMessagesTests(unittest.TestCase):
    def setUp(self):
        self.dock = Mock()
        self.external = Mock()
        self.messages = ViewerMessages(lambda: self.dock, lambda: self.external)
        self.payload = {"title": '예시 "장소"', "results": [], "success": True}

    def test_payload_contracts(self):
        for name, (method, signal) in PAYLOAD_MESSAGES.items():
            with self.subTest(name=name):
                self.dock.reset_mock()
                self.external.reset_mock()
                self.messages.publish(name, self.payload)
                getattr(self.dock, method).assert_called_once_with(self.payload)
                self.external.emit_signal.assert_called_once_with(
                    signal, json.dumps(self.payload, ensure_ascii=False))
                self.assertEqual(json.loads(self.external.emit_signal.call_args.args[1]),
                                 self.payload)

    def test_missing_endpoints(self):
        for dock_present, external_present in [(False, False), (True, False), (False, True)]:
            with self.subTest(dock=dock_present, external=external_present):
                dock, external = Mock(), Mock()
                messages = ViewerMessages(lambda: dock if dock_present else None,
                                          lambda: external if external_present else None)
                for name in PAYLOAD_MESSAGES:
                    messages.publish(name, self.payload)
                messages.route_status(True, "정상")
                messages.route_history_input(self.payload)
                self.assertEqual(bool(dock.mock_calls), dock_present)
                self.assertEqual(bool(external.mock_calls), external_present)

    def test_endpoint_recreation(self):
        self.messages.publish("route_history", self.payload)
        previous = self.dock
        previous.reset_mock()
        self.dock = Mock()
        self.external = None
        self.messages.publish("route_history", self.payload)
        self.dock.set_route_history.assert_called_once_with(self.payload)
        self.assertFalse(previous.mock_calls)
        self.dock = None
        self.messages.publish("route_history", self.payload)

    def test_center_and_guidance_order(self):
        calls = []
        self.dock.set_center.side_effect = lambda *a: calls.append(("dock-center", a))
        self.dock.set_route_guidance.side_effect = lambda p: calls.append(("dock-guidance", p))
        self.external.set_center.side_effect = lambda *a: calls.append(("external-center", a))
        self.external.emit_signal.side_effect = lambda *a: calls.append(("external-guidance", a))
        self.messages.publish("route_guidance", self.payload, center=(127.5, 37.5))
        self.assertEqual([c[0] for c in calls], ["dock-center", "dock-guidance",
                                               "external-center", "external-guidance"])
        self.assertEqual(calls[0][1], (127.5, 37.5))
        self.assertEqual(calls[2][1], (127.5, 37.5))

    def test_external_stopped_during_native_delivery(self):
        previous = self.external
        def stop_external(_payload):
            self.external = None
        self.dock.set_route_history.side_effect = stop_external
        self.messages.publish("route_history", self.payload)
        previous.emit_signal.assert_not_called()

    def test_status_contract(self):
        self.messages.route_status(1, 123)
        # Dock owns its previous coercion; the external wire format stays bool/str.
        self.dock.set_route_status.assert_called_once_with(1, 123)
        self.external.emit_signal.assert_called_once_with("routeStatusChanged", True, "123")

    def test_history_input_contract_and_external_fallback(self):
        self.messages.route_history_input(self.payload)
        self.dock.load_route_history_input.assert_called_once_with(self.payload)
        self.external.emit_signal.assert_called_once_with(
            "loadRouteHistoryInput", json.dumps(self.payload, ensure_ascii=False))
        self.dock.reset_mock()
        self.external.reset_mock()
        self.dock.web_view = None
        self.messages.route_history_input(self.payload)
        self.dock.load_route_history_input.assert_not_called()
        self.external.emit_signal.assert_called_once()

    def test_unknown_message_rejected_without_delivery(self):
        with self.assertRaises(KeyError):
            self.messages.publish("unknown", self.payload)
        self.assertFalse(self.dock.mock_calls)
        self.assertFalse(self.external.mock_calls)

    def test_history_input_keeps_both_native_paths(self):
        # Execute just the method without importing Qt, using a fake Dock.
        root = Path(__file__).resolve().parents[1] / "navermap_qgis_bridge"
        tree = ast.parse((root / "dock_widget.py").read_text(encoding="utf-8-sig"))
        dock_class = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                          and n.name == "NaverMapDockWidget")
        method = next(n for n in dock_class.body if isinstance(n, ast.FunctionDef)
                      and n.name == "load_route_history_input")
        namespace = {"json": json}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "dock_widget.py", "exec"), namespace)
        dock = Mock()
        namespace[method.name](dock, self.payload)
        dock.set_route_history_input.assert_called_once_with(self.payload)
        script = dock.web_view.page.return_value.runJavaScript.call_args.args[0]
        prefix = "window.loadRouteHistoryInput("
        self.assertTrue(script.startswith(prefix) and script.endswith(");"))
        self.assertEqual(json.loads(script[len(prefix):-2]), self.payload)

    def test_signal_names_exist_in_both_transports(self):
        root = Path(__file__).resolve().parents[1] / "navermap_qgis_bridge"
        native = (root / "web_bridge.py").read_text(encoding="utf-8-sig")
        external = (root / "web" / "js" / "external_transport.js").read_text(encoding="utf-8-sig")
        for signal in [*(pair[1] for pair in PAYLOAD_MESSAGES.values()),
                       "routeStatusChanged", "loadRouteHistoryInput"]:
            with self.subTest(signal=signal):
                self.assertIn(signal + " = pyqtSignal(", native)
                self.assertIn('signal("' + signal + '")', external)

    def test_plugin_dispatches_to_common_sender(self):
        names = {"_emit_local_search_results", "_sync_route_history_panel", "_set_route_status"}
        methods = [find_method(name) for name in names]
        self.assertEqual(len(methods), len(names))
        namespace = {}
        exec(compile(ast.Module(body=methods, type_ignores=[]), "plugin.py", "exec"), namespace)
        plugin = Mock()
        namespace["_emit_local_search_results"](plugin, "test-request", 1, "정상", [])
        plugin.viewer_messages.publish.assert_called_once_with("local_search_results", {
            "request_id": "test-request", "success": True, "message": "정상", "results": []})
        plugin.reset_mock()
        plugin._route_history_payload.return_value = self.payload
        namespace["_sync_route_history_panel"](plugin, "test-history")
        plugin._route_history_payload.assert_called_once_with("test-history")
        plugin.viewer_messages.publish.assert_called_once_with("route_history", self.payload)
        namespace["_set_route_status"](plugin, False, "실패")
        plugin.viewer_messages.route_status.assert_called_once_with(False, "실패")


if __name__ == "__main__":
    unittest.main()
