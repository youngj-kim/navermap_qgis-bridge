# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from unittest.mock import Mock

from navermap_qgis_bridge.api_transport import ApiTransport


class ApiTransportTests(unittest.TestCase):
    def setUp(self):
        self.manager, self.schedule = Mock(), Mock()
        self.transport = ApiTransport(self.manager, self.schedule)

    def test_search_registration_callbacks_and_timeout(self):
        done, timeout = Mock(), Mock()
        reply = self.transport.start_search("request", "request-id", done, timeout)
        self.assertEqual(self.transport.search_replies[reply], "request-id")
        reply.finished.connect.call_args.args[0]()
        done.assert_called_once_with(reply)
        delay, callback = self.schedule.call_args.args
        self.assertEqual(delay, 7000)
        callback()
        timeout.assert_called_once_with(reply)

    def test_route_callback_and_cancel_order(self):
        done = Mock()
        reply = self.transport.start_route("request", done)
        reply.finished.connect.call_args.args[0]()
        done.assert_called_once_with(reply)
        reply.reset_mock()
        reply.abort.side_effect = lambda: self.assertIsNone(self.transport.route_reply)
        self.transport.cancel_route()
        self.assertEqual([c[0] for c in reply.mock_calls],
                         ["finished.disconnect", "abort", "deleteLater"])
        self.transport.cancel_route()  # Idempotent.
        reply.abort.assert_called_once()

    def test_close_cancels_all_and_late_timeout_has_no_owner(self):
        route, search = Mock(), Mock()
        self.manager.get.side_effect = [route, search]
        self.transport.start_route("route", Mock())
        timeout = Mock(side_effect=lambda reply: self.assertNotIn(reply, self.transport.search_replies))
        self.transport.start_search("search", "id", Mock(), timeout)
        self.transport.close()
        self.assertIsNone(self.transport.route_reply)
        self.assertEqual(self.transport.search_replies, {})
        for reply in [route, search]:
            reply.abort.assert_called_once()
            reply.deleteLater.assert_called_once()
        self.schedule.call_args.args[1]()
        self.transport.close()

    def test_disconnect_failure_still_aborts(self):
        reply = Mock()
        self.transport.route_reply = reply
        reply.finished.disconnect.side_effect = TypeError("disconnected")
        self.transport.cancel_route()
        reply.abort.assert_called_once()
        reply.deleteLater.assert_called_once()

    def test_route_timeout_releases_owner_before_notification(self):
        timeout = Mock(side_effect=lambda: self.assertIsNone(self.transport.route_reply))
        reply = self.transport.start_route("request", Mock(), timeout)
        delay, expire = self.schedule.call_args.args
        self.assertEqual(delay, 30000)
        expire()
        expire()
        timeout.assert_called_once()
        reply.abort.assert_called_once()

    def test_old_route_timeout_cannot_cancel_replacement_or_completed_reply(self):
        first, second = Mock(), Mock()
        self.manager.get.side_effect = [first, second]
        old_timeout, new_timeout = Mock(), Mock()
        self.transport.start_route("A", Mock(), old_timeout)
        old_expire = self.schedule.call_args.args[1]
        self.transport.cancel_route()
        self.transport.start_route("B", Mock(), new_timeout)
        new_expire = self.schedule.call_args.args[1]
        old_expire()
        self.assertIs(self.transport.route_reply, second)
        second.abort.assert_not_called()
        self.transport.route_reply = None  # Completion releases ownership.
        new_expire()
        old_timeout.assert_not_called()
        new_timeout.assert_not_called()
