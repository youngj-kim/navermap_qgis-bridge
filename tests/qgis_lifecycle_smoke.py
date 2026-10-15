# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline QGIS lifecycle and HTTP contracts; synthetic data, no profile/API access."""
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import Qgis, QgsApplication, QgsPointXY, QgsProject, QgsCoordinateReferenceSystem, QgsRectangle
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtWidgets import QMainWindow
from navermap_qgis_bridge import classFactory
from navermap_qgis_bridge.external_bridge import NaverExternalBridgeServer
from navermap_qgis_bridge.web_bridge import NaverWebBridge

app = QgsApplication([], True)
app.initQgis()
window, canvas = QMainWindow(), QgsMapCanvas()
iface = Mock()
iface.mainWindow.return_value = window
iface.mapCanvas.return_value = canvas
plugin = classFactory(iface)
server = NaverExternalBridgeServer(port=0)
opener = build_opener(ProxyHandler({}))
try:
    plugin.initGui()
    points = [QgsPointXY(127, 37), QgsPointXY(128, 38)]
    vehicle = {"car_type": 1, "car_fuel": "gasoline", "car_hipass": False}
    plugin._create_route_layer(points, 100, 60, 0, "test", "TIME", 0, [], vehicle)
    plugin._set_route_point("origin", 127, 37)
    plugin._append_route_history("test-history", "test-route", "2026-01-01T00:00:00+09:00",
                                points, (127, 37), (128, 38), "A", "B", [],
                                100, 60, 0, "test", "TIME", [], vehicle, [], 0, None)
    reply, search = Mock(), Mock()
    plugin.route_reply = reply
    plugin.local_search_replies[search] = "test"
    QgsProject.instance().clear()
    assert plugin.project_epoch == 1 and not plugin.project_transitioning
    assert plugin.route_reply is None and plugin.local_search_replies == {}
    reply.abort.assert_called_once()
    search.abort.assert_called_once()
    assert plugin.route_layer is None and plugin.route_points_layer is None
    plugin._handle_route_reply(reply, "TIME", [], [], vehicle, (127,37), (128,38), "A", "B")
    assert plugin.route_layer is None, "late response must not create layers in new project"
    assert plugin.route_history_layer.featureCount() == 1
    assert next(plugin.route_history_layer.getFeatures())["toll_fare"] == 0
    plugin._focus_route_history("test-history")
    assert plugin.route_layer.isValid(), "session history should redisplay in new project"

    for crs in ("EPSG:4326", "EPSG:3857"):
        canvas.setDestinationCrs(QgsCoordinateReferenceSystem(crs))
        canvas.setExtent(QgsRectangle(126, 36, 128, 38) if crs == "EPSG:4326"
                         else QgsRectangle(14100000, 4400000, 14200000, 4500000))
        plugin._handle_viewer_zoomed(127, 37, 4)
        assert abs(plugin._canvas_ground_resolution() - 4) / 4 < .02, crs
    plugin.dock = Mock()
    native = NaverWebBridge()
    native.centerRequested.connect(plugin._handle_viewer_moved)
    native.moveQgisCenter(127.1,37.1)
    actual = plugin._to_epsg_4326(canvas.center())
    assert abs(actual[0]-127.1)<1e-7 and abs(actual[1]-37.1)<1e-7
    plugin.external_bridge_server = server
    server.reset_project(plugin.project_epoch)
    assert server.enqueue('move_center', {'_epoch':plugin.project_epoch,'lon':127.2,'lat':37.2})==200
    plugin._process_external_bridge_events()
    actual = plugin._to_epsg_4326(canvas.center())
    assert abs(actual[0]-127.2)<1e-7 and abs(actual[1]-37.2)<1e-7
    plugin.external_bridge_server = None
    plugin.last_canvas_view = None
    plugin._sync_canvas_center()
    assert plugin.dock.set_view.call_args.args[3] is False
    canvas.zoomByFactor(.5)
    plugin._sync_canvas_center()
    assert plugin.dock.set_view.call_args.args[3] is True, "zoom must preserve panorama"
    center = canvas.center()
    canvas.setCenter(QgsPointXY(center.x() + 10, center.y()))
    plugin._sync_canvas_center()
    assert plugin.dock.set_view.call_args.args[3] is False, "pan must move panorama"
    plugin.dock = None

    server.reset_project(0)
    server.start()
    def post(path, body):
        try:
            with opener.open(Request(server.url.split("#")[0] + path, data=body,
                                     headers={"Content-Type": "application/json", "X-Bridge-Token": server._token}), timeout=5) as response:
                return response.status
        except HTTPError as exc:
            return exc.code
    assert post("api/request-route", b'[]') == 400
    assert post("api/unknown", b'{}') == 404
    assert post("api/cancel-route", b'{"_epoch":0}') == 200
    server.reset_project(1, accepting=False)
    assert post("api/cancel-route", b'{"_epoch":1}') == 409
    server.reset_project(1)
    assert post("api/request-route", b'{"_epoch":0}') == 409
    assert post("api/cancel-route", b'{"_epoch":1}') == 200
    assert server.drain_events()[0]["epoch"] == 1
    print(f"PASS: QGIS {Qgis.QGIS_VERSION}; project reset, cancellation, retained history, HTTP epoch/validation, EPSG:4326/3857 scale sync")
finally:
    server.stop()
    plugin.unload()
    QgsProject.instance().clear()
    del plugin, canvas, iface, window
    app.exitQgis()
