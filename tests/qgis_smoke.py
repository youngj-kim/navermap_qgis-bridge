# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline real-QGIS smoke test. Run with the installed python-qgis launcher.

No credentials, NAVER requests, saved profiles or user projects are accessed.
This verifies loading/layers/export only, not live maps or browser interactions.
"""
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qgis.core import Qgis, QgsApplication, QgsCoordinateReferenceSystem, QgsPointXY, QgsProject, QgsVectorLayer
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtWidgets import QMainWindow
from navermap_qgis_bridge import classFactory


app = QgsApplication([], True)
app.initQgis()
window = QMainWindow()
canvas = QgsMapCanvas()
canvas.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
iface = Mock()
iface.mainWindow.return_value = window
iface.mapCanvas.return_value = canvas
plugin = classFactory(iface)
temporary = None
try:
    plugin.initGui()
    points = [QgsPointXY(127.1, 37.4), QgsPointXY(127.2, 37.5)]
    vehicle = {"car_type": 1, "car_fuel": "gasoline", "car_hipass": False}
    guide = dict(route_id="test-route", sequence=1, section_no=0, guide_type=1,
                 category="left", guidance="test guidance", name="test", distance_m=20,
                 duration_s=5, cumulative_distance_m=20, cumulative_duration_s=5,
                 road_index=0, longitude=127.15, latitude=37.45)
    plugin._create_route_layer(points, 100, 60, 1, "test", "RECOMMEND", 0, [], vehicle)
    plugin._create_route_guidance_layer([guide])
    plugin._set_route_point("origin", 127.1, 37.4)
    plugin._set_route_point("destination", 127.2, 37.5)
    plugin._update_roadview_layer(127.1, 37.4, 0, 0, 100, "test-pano")
    for layer in [plugin.route_layer, plugin.route_guidance_layer,
                  plugin.route_points_layer, plugin.roadview_layer]:
        assert layer.isValid() and layer.featureCount() > 0
    plugin._append_route_history("test-history", "test-route", "2026-01-02T03:04:05+09:00",
                                 points, (127.1, 37.4), (127.2, 37.5), "origin", "destination",
                                 [], 100, 60, 1, "test", "RECOMMEND", [], vehicle, [guide])
    assert len(plugin._route_history_payload()["items"]) == 1
    temporary = TemporaryDirectory(prefix="navermap-qgis-smoke-")
    directory = temporary.name
    output = Path(directory) / "test.gpx"
    assert plugin._write_gpx_history(plugin.route_history_layer, plugin.guidance_history_layer, output) == (1, 1)
    for name in ["tracks", "routes", "waypoints"]:
        imported = QgsVectorLayer(f"{output}|layername={name}", "test", "ogr")
        assert imported.isValid() and imported.featureCount() > 0, name
        assert output.with_name("test_" + name + ".qml").exists()
        del imported
    route_history = plugin.route_history_layer
    geojson = Path(directory) / "test.geojson"
    assert plugin._write_geojson_history_layer(route_history, geojson, "routes") == 1
    shapefile = Path(directory) / "test.shp"
    assert plugin._write_shapefile_history_layer(
        route_history, shapefile, "LineString", "routes", plugin._route_shapefile_fields()) == 1
    gpkg = Path(directory) / "test.gpkg"
    assert plugin._write_history_layer(route_history, gpkg, "routes", "LineString") == 1
    assert plugin._write_history_layer(route_history, gpkg, "routes", "LineString") == 0
    for filename in [geojson, shapefile, gpkg]:
        imported = QgsVectorLayer(str(filename), "test", "ogr")
        assert imported.isValid() and imported.featureCount() == 1, filename.suffix
        del imported
    plugin._handle_viewer_moved(127.3, 37.6)
    assert abs(canvas.center().x() - 127.3) < 1e-6
    print("PASS QGIS", Qgis.QGIS_VERSION, "loading, actions, layers, history, GPX/GeoJSON/SHP/GPKG export/reimport, GPKG deduplication, styles, canvas center")
finally:
    plugin.unload()
    QgsProject.instance().removeAllMapLayers()
    del plugin, canvas, window
    app.exitQgis()
    if temporary is not None:
        temporary.cleanup()
