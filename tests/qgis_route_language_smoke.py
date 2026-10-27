# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline real-Qt request-language checks through both bridge entry points."""
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtCore import QUrlQuery
from navermap_qgis_bridge import classFactory
from navermap_qgis_bridge import search_routes
from navermap_qgis_bridge.web_bridge import NaverWebBridge

app = QgsApplication([], True)
app.initQgis()
plugin = classFactory(Mock())
plugin._set_route_point = Mock()
plugin.api_transport = Mock()
bridge = NaverWebBridge()
bridge.routeRequested.connect(plugin._request_route)
try:
    with patch.object(search_routes, "naver_client_id", return_value="PLACEHOLDER_ID"), \
         patch.object(search_routes, "naver_client_secret", return_value="PLACEHOLDER_SECRET"):
        for options, expected in [({}, "ko"), ({"language":"en"}, "en"),
                                  ({"language":"ko"}, "ko"), ({"language":"invalid"}, "ko")]:
            args = (127., 37., 128., 38., "TIME", "[]", "[]", json.dumps(options), "출발", "도착")
            bridge.requestRoute(*args)
            request = plugin.api_transport.start_route.call_args.args[0]
            assert QUrlQuery(request.url()).queryItemValue("lang") == expected
            plugin.api_transport.start_route.reset_mock()
            names = ("origin_lon", "origin_lat", "destination_lon", "destination_lat", "priority",
                     "waypoints_json", "avoid_json", "vehicle_json", "origin_label", "destination_label")
            plugin.external_bridge_server = Mock()
            plugin.external_bridge_server.next_event.side_effect = [
                {"type":"request_route", "epoch":plugin.project_epoch, "payload":dict(zip(names, args))}, None]
            plugin._process_external_bridge_events()
            plugin.api_transport.start_route.assert_called_once()
            request = plugin.api_transport.start_route.call_args.args[0]
            assert QUrlQuery(request.url()).queryItemValue("lang") == expected
        print("PASS:", Qgis.QGIS_VERSION, "native/external language to real Qt URL; Korean default; no API calls")
finally:
    del bridge, plugin
    app.exitQgis()
