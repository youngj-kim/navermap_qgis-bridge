# SPDX-License-Identifier: GPL-2.0-or-later
"""Outbound viewer messages, independent of Qt and transport implementations."""

import json


# Dock methods accept objects; external signals accept JSON strings.
PAYLOAD_MESSAGES = {
    "local_search_results": ("set_local_search_results", "localSearchResultsChanged"),
    "route_guidance": ("set_route_guidance", "routeGuidanceChanged"),
    "route_history": ("set_route_history", "routeHistoryChanged"),
}


class ViewerMessages:
    def __init__(self, dock_provider, external_provider):
        # Resolve on each delivery: docks and servers can be recreated or stopped.
        self._dock_provider = dock_provider
        self._external_provider = external_provider

    def publish(self, name, payload, center=None):
        dock_method, signal = PAYLOAD_MESSAGES[name]
        dock = self._dock_provider()
        if dock is not None:
            if center is not None:
                dock.set_center(*center)
            getattr(dock, dock_method)(payload)
        external = self._external_provider()
        if external is not None:
            if center is not None:
                external.set_center(*center)
            external.emit_signal(signal, json.dumps(payload, ensure_ascii=False))

    def route_status(self, success, message):
        dock = self._dock_provider()
        if dock is not None:
            dock.set_route_status(success, message)
        external = self._external_provider()
        if external is not None:
            external.emit_signal("routeStatusChanged", bool(success), str(message))

    def route_history_input(self, payload):
        dock = self._dock_provider()
        if dock is not None and dock.web_view is not None:
            dock.load_route_history_input(payload)
        external = self._external_provider()
        if external is not None:
            external.emit_signal(
                "loadRouteHistoryInput", json.dumps(payload, ensure_ascii=False)
            )
