# SPDX-License-Identifier: GPL-2.0-or-later
"""Test server state without QGIS imports, sockets, profiles or credentials."""
import ast
import json
import secrets
import threading
import unittest
from queue import Empty, Full, Queue

from host_methods import ROOT


class ProjectBridgeTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((ROOT / "external_bridge.py").read_text(encoding="utf-8-sig"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "NaverExternalBridgeServer")
        namespace = dict(secrets=secrets, threading=threading, Queue=Queue, Empty=Empty, Full=Full, json=json)
        exec(compile(ast.Module(body=[cls], type_ignores=[]), "external_bridge.py", "exec"), namespace)
        self.server = namespace[cls.name]()

    def test_reset_discards_queued_events_and_old_responses(self):
        server = self.server
        self.assertEqual(server.enqueue("request_route", {"_epoch": 0}), 200)
        server.emit_signal("routeStatusChanged", True, "old")
        server.reset_project(1, accepting=False)
        self.assertEqual(server.drain_events(), [])
        self.assertEqual(server._outbound_events, [])
        self.assertEqual(server.enqueue("request_route", {"_epoch": 1}), 409)
        server.reset_project(1)
        self.assertEqual(server.enqueue("request_route", {"_epoch": 0}), 409)
        self.assertEqual(server.enqueue("request_route", {}), 409)
        self.assertEqual(server.enqueue("request_route", {"_epoch": 1}), 200)
        self.assertEqual(server.drain_events()[0]["epoch"], 1)

    def test_queue_is_bounded_and_outbound_sequence_survives_reset(self):
        server = self.server
        for _ in range(512):
            self.assertEqual(server.enqueue("move_center", {"_epoch": 0}), 200)
        self.assertEqual(server.enqueue("move_center", {"_epoch": 0}), 429)
        server.emit_signal("routeStatusChanged", True, "A")
        server.reset_project(1)
        server.emit_signal("routeStatusChanged", True, "B")
        self.assertEqual(server._outbound_events[0]["sequence"], 2)
        self.assertEqual(server._outbound_events[0]["epoch"], 1)
