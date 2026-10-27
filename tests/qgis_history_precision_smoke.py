# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline history precision regression; optional GeoPackage paths are read only."""
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import Qgis, QgsApplication, QgsPointXY, QgsVectorLayer, QgsProject
from navermap_qgis_bridge import classFactory
from navermap_qgis_bridge.history_operations import validate_import_pair
app = QgsApplication([], True)
app.initQgis()
plugin = classFactory(Mock())
temporary = TemporaryDirectory(prefix='history-precision-')
try:
    guide = dict(route_id='route', sequence=1, section_no=1, guide_type=3,
                 guidance='test', name='test', distance_m=20, duration_s=5,
                 cumulative_distance_m=20, cumulative_duration_s=5, road_index=0,
                 longitude=127.0229552, latitude=37.3162351)
    plugin._append_route_history('history', 'route', '2026-10-23',
        [QgsPointXY(127,37), QgsPointXY(128,38)], (127,37), (128,38),
        'A', 'B', [], 100, 60, 1, 'test', 'TIME', [],
        dict(car_type=1, car_fuel='gasoline', car_hipass=False), [guide])
    routes, guides = plugin.route_history_layer, plugin.guidance_history_layer
    feature = next(guides.getFeatures())
    for field in ('longitude', 'latitude'):
        assert abs(feature[field] - guide[field]) < 1e-10, (field, feature[field])
    validate_import_pair(routes, guides, plugin._history_value)
    # Legacy five-decimal rounding is accepted, larger corruption is rejected.
    for delta, accepted in ((0.000005, True), (0.0000051, False), (0.001, False)):
        for field in ('longitude', 'latitude'):
            changes = {guides.fields().indexOf(n): guide[n] + (delta if n == field else 0)
                       for n in ('longitude', 'latitude')}
            assert guides.dataProvider().changeAttributeValues({feature.id(): changes})
            try:
                validate_import_pair(routes, guides, plugin._history_value)
            except RuntimeError:
                assert not accepted, (field, delta)
            else:
                assert accepted, (field, delta)
    assert guides.dataProvider().changeAttributeValues({feature.id(): {
        guides.fields().indexOf(n): guide[n] for n in ('longitude', 'latitude')}})
    output = Path(temporary.name) / 'precision.gpkg'
    plugin._write_history_layer(routes, output, 'naver_route_history', 'LineString')
    plugin._write_history_layer(guides, output, 'naver_guidance_history', 'Point')
    for filename in [str(output), *sys.argv[1:]]:
        source_routes = QgsVectorLayer(filename+'|layername=naver_route_history', 'routes', 'ogr')
        source_guides = QgsVectorLayer(filename+'|layername=naver_guidance_history', 'guides', 'ogr')
        assert source_routes.isValid() and source_guides.isValid()
        validate_import_pair(source_routes, source_guides, plugin._history_value)
        targets = routes.clone(), guides.clone()
        for target in targets:
            assert target.dataProvider().truncate()
        for source, target, kind, geometry in ((source_routes, targets[0], 'route', 'LineString'),
                                              (source_guides, targets[1], 'guidance', 'Point')):
            from navermap_qgis_bridge.history_schema import history_import_fields
            assert plugin._append_imported_history(source, target, geometry, history_import_fields(kind)) == source.featureCount()
        validate_import_pair(*targets, plugin._history_value)
        print('PASS', Qgis.QGIS_VERSION, Path(filename).name, source_routes.featureCount(), source_guides.featureCount())
        del source_routes, source_guides, targets, source, target
finally:
    QgsProject.instance().removeAllMapLayers()
    del plugin, routes, guides
    app.exitQgis()
    temporary.cleanup()
