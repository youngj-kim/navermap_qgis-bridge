# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline review regressions; placeholders only, no profile or NAVER requests."""
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import Qgis, QgsApplication, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsCoordinateReferenceSystem, QgsVectorLayer
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtWidgets import QMainWindow
from navermap_qgis_bridge import classFactory
from navermap_qgis_bridge.external_bridge import NaverExternalBridgeServer
from navermap_qgis_bridge.history_operations import history_transaction, validate_import_pair
from navermap_qgis_bridge.compat import MSGBOX_YES

app = QgsApplication([], True)
app.initQgis()
window, canvas = QMainWindow(), QgsMapCanvas()
canvas.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
iface = Mock()
iface.mainWindow.return_value, iface.mapCanvas.return_value = window, canvas
plugin = classFactory(iface)
server = NaverExternalBridgeServer(port=0)
opener = build_opener(ProxyHandler({}))
try:
    plugin.initGui()
    server.start()
    base = server.url.split("#")[0]
    def request(path, body=None, **headers):
        try:
            with opener.open(Request(base + path, data=body, headers=headers), timeout=5) as reply:
                return reply.status, reply.read()
        except HTTPError as exc:
            return exc.code, b""
    auth = {"X-Bridge-Token": server._token}
    assert request("api/state")[0] == 403
    assert request("api/events?since=0")[0] == 403
    assert request("api/state", **{**auth, "Origin": "https://example.invalid"})[0] == 403
    assert request("", Host="example.invalid")[0] == 403
    assert request("api/state", **auth)[0] == 200
    body = b'{"_epoch":0}'
    assert request("api/cancel-route", body, **auth)[0] == 415
    assert request("api/cancel-route", body, **{**auth, "Content-Type": "text/plain"})[0] == 415
    assert request("api/cancel-route", body, **{**auth, "Content-Type": "application/json", "Origin": base.rstrip("/")})[0] == 200
    assert server.next_event()["type"] == "cancel_route"
    for index in range(105):
        server.emit_signal("routeStatusChanged", True, str(index))
    status, raw = request("api/events?since=0", **auth)
    assert status == 200 and json.loads(raw)["gap"] is True
    other = NaverExternalBridgeServer(port=server._server.server_address[1])
    try:
        other.start()
    except OSError:
        pass
    else:
        other.stop()
        raise AssertionError("second server bound the same port")

    import importlib
    plugin_module = importlib.import_module("navermap_qgis_bridge.plugin")
    occupied_port = server._server.server_address[1]
    def factory(*args, **kwargs):
        return NaverExternalBridgeServer(port=kwargs.get("port", occupied_port))
    with patch.object(plugin_module,"NaverExternalBridgeServer",side_effect=factory):
        alternate = plugin._ensure_external_bridge()
        assert alternate is not None and alternate._server.server_address[1] != occupied_port
        plugin._stop_external_bridge()

    points = [QgsPointXY(127, 37), QgsPointXY(128, 38)]
    guide = dict(route_id="route", sequence=1, section_no=1, guide_type=3, category="uturn",
                 guidance="방면으로 우회전", name="guide", distance_m=20, duration_s=5,
                 cumulative_distance_m=20, cumulative_duration_s=5, road_index=0,
                 longitude=127, latitude=37)
    vehicle = dict(car_type=1, car_fuel="gasoline", car_hipass=False)
    plugin._append_route_history("history", "route", "2026-10-13T00:00:00+09:00", points,
        (127,37), (128,38), "A", "B", [], 100, 60, 1, "test", "TIME", [], vehicle, [guide])
    routes, guides = plugin.route_history_layer, plugin.guidance_history_layer
    assert next(guides.getFeatures())["category"] == "right"
    validate_import_pair(routes, guides, plugin._history_value)
    before = routes.featureCount(), guides.featureCount()
    try:
        with history_transaction(routes, guides):
            assert routes.dataProvider().deleteFeatures([f.id() for f in routes.getFeatures()])
            raise RuntimeError("injected second-layer failure")
    except RuntimeError:
        pass
    assert (routes.featureCount(), guides.featureCount()) == before
    from navermap_qgis_bridge import route_history as history_module
    original_add = history_module.checked_add
    def fail_guidance(layer, features):
        if layer is guides:
            raise RuntimeError("injected guidance write failure")
        return original_add(layer, features)
    with patch.object(history_module, "checked_add", side_effect=fail_guidance):
        try:
            plugin._append_route_history("failed-history", "route", "2026-10-13T00:00:00+09:00", points,
                (127,37), (128,38), "A", "B", [], 100, 60, 1, "test", "TIME", [], vehicle, [guide])
        except RuntimeError:
            pass
        else:
            raise AssertionError("guidance save failure ignored")
    assert (routes.featureCount(), guides.featureCount()) == before
    from navermap_qgis_bridge import search_routes as search_module
    reply = Mock()
    plugin.route_reply = reply
    payload = {"code":0, "route":{"trafast":[{"path":[[127,37],[128,38]],
               "summary":{"distance":100,"duration":60000}, "guide":[]}]}}
    iface.messageBar().pushSuccess.reset_mock()
    with patch.object(search_module, "read_reply", return_value=(200,json.dumps(payload).encode(),search_module.QNetworkReply.NetworkError.NoError,"")), patch.object(plugin, "_append_route_history", side_effect=RuntimeError("injected save failure")), patch.object(plugin, "_set_route_status") as status:
        plugin._handle_route_reply(reply,"TIME",[],[],vehicle,(127,37),(128,38),"A","B")
        assert status.call_args.args[0] is False
        iface.messageBar().pushSuccess.assert_not_called()
    # Invalid counts and coordinate systems are rejected before importing either half.
    feature = next(routes.getFeatures())
    assert routes.dataProvider().changeAttributeValues({feature.id(): {routes.fields().indexOf("guidance_count"): 2}})
    try:
        validate_import_pair(routes, guides, plugin._history_value)
    except RuntimeError:
        pass
    else:
        raise AssertionError("inconsistent guide count accepted")
    assert routes.dataProvider().changeAttributeValues({feature.id(): {routes.fields().indexOf("guidance_count"): 1}})
    routes.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    try:
        validate_import_pair(routes, guides, plugin._history_value)
    except RuntimeError:
        pass
    else:
        raise AssertionError("wrong CRS accepted")
    routes.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    # Imported stale categories are repaired in memory and in exported files.
    guide_feature = next(guides.getFeatures())
    guides.dataProvider().changeAttributeValues({guide_feature.id(): {guides.fields().indexOf("category"): "uturn"}})
    target_routes, target_guides = routes.clone(), guides.clone()
    target_guides.dataProvider().deleteFeatures([f.id() for f in target_guides.getFeatures()])
    assert plugin._append_imported_history(guides, target_guides, "Point", plugin._full_history_field_specs("guidance")) == 1
    assert next(target_guides.getFeatures())["category"] == "right"
    with TemporaryDirectory(prefix="navermap-review-") as directory:
        output = Path(directory) / "guides.geojson"
        plugin._write_geojson_history_layer(guides, output, "guides")
        assert json.loads(output.read_text(encoding="utf-8"))["features"][0]["properties"]["category"] == "right"
    gpkg_temporary = TemporaryDirectory(prefix="navermap-gpkg-repair-")
    directory = gpkg_temporary.name
    output = Path(directory) / "guides.gpkg"
    assert plugin._write_history_layer(guides, output, "guides", "Point") == 1
    saved = QgsVectorLayer(f"{output}|layername=guides", "saved", "ogr")
    saved_feature = next(saved.getFeatures())
    assert saved.dataProvider().changeAttributeValues({saved_feature.id(): {saved.fields().indexOf("category"): "uturn"}})
    del saved
    assert plugin._write_history_layer(guides, output, "guides", "Point") == 0
    saved = QgsVectorLayer(f"{output}|layername=guides", "saved", "ogr")
    assert next(saved.getFeatures())["category"] == "right", "same-file GPKG dedup left stale category"
    del saved
    from navermap_qgis_bridge.compat import MSGBOX_NO
    with TemporaryDirectory(prefix="navermap-overwrite-") as directory:
        destination = Path(directory) / "selected.geojson"
        paired = plugin._geojson_output_paths(destination)
        paired[0].write_text("existing", encoding="utf-8")
        with patch.object(history_module.QInputDialog,"getItem",return_value=("GeoJSON (*.geojson)",True)), patch.object(history_module.QFileDialog,"getSaveFileName",return_value=(str(destination),"")), patch.object(history_module.QMessageBox,"question",return_value=MSGBOX_NO) as question, patch.object(plugin,"_write_geojson_history_layer") as write:
            plugin._export_single_route_history("history")
            question.assert_called_once()
            write.assert_not_called()
            assert paired[0].read_text(encoding="utf-8") == "existing"
    feature = next(routes.getFeatures())
    routes.dataProvider().changeAttributeValues({feature.id(): {routes.fields().indexOf("origin_name"): "가" * 100}})
    try:
        plugin._shapefile_compatible_layer(routes, "LineString", plugin._route_shapefile_fields())
    except RuntimeError:
        pass
    else:
        raise AssertionError("oversized UTF-8 string silently truncated")

    # Reentrant timer calls must leave later commands queued; unexpected exceptions do not lose them.
    server.drain_events()
    plugin.external_bridge_server = server
    server.reset_project(plugin.project_epoch)
    server.enqueue("export_route_history", {"_epoch":plugin.project_epoch, "history_id":"history"})
    server.enqueue("cancel_route", {"_epoch":plugin.project_epoch})
    def modal(_identifier):
        plugin._process_external_bridge_events()
        assert server._events.qsize() == 1
        raise RuntimeError("injected modal failure")
    with patch.object(plugin, "_export_single_route_history", side_effect=modal), patch.object(plugin, "_cancel_route") as cancel:
        plugin._process_external_bridge_events()
        cancel.assert_called_once()
    plugin.external_bridge_server = None
    plugin.dock = Mock()
    plugin.reverse_sync_guard_timer.start()
    plugin._schedule_canvas_sync()
    assert plugin.canvas_sync_timer.isActive(), "guard discarded final user movement"
    plugin.dock = None
    print(f"PASS QGIS {Qgis.QGIS_VERSION}: bridge authorization/content-type/exclusive port/gap; history validation/rollback/category migration/export; SHP bytes; modal reentrancy; deferred canvas sync")
finally:
    server.stop()
    plugin.external_bridge_server = None
    plugin.unload()
    QgsProject.instance().removeAllMapLayers()
    app.exitQgis()
    if "gpkg_temporary" in globals():
        gpkg_temporary.cleanup()
