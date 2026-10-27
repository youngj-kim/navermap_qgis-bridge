# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline multi-file import, duplicate, rollback, batch delete and bridge checks."""
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qgis.core import Qgis, QgsApplication, QgsPointXY, QgsProject
from navermap_qgis_bridge import classFactory
from navermap_qgis_bridge.compat import MSGBOX_YES, MSGBOX_NO
from navermap_qgis_bridge import route_history as module
from navermap_qgis_bridge.web_bridge import NaverWebBridge
app = QgsApplication([], True)
app.initQgis()
plugin = classFactory(Mock())
plugin._sync_route_history_panel = Mock()
plugin._clear_current_route_display = Mock()
temporary = TemporaryDirectory(prefix='history-batch-')
try:
    files = []
    for index in range(3):
        guide = dict(route_id='route', sequence=1, section_no=1, guide_type=3,
                     guidance='test', name='test', distance_m=20, duration_s=5,
                     cumulative_distance_m=20, cumulative_duration_s=5, road_index=0,
                     longitude=127.0229552, latitude=37.3162351)
        plugin._append_route_history(str(index), 'route', '2026-10-23',
            [QgsPointXY(127,37), QgsPointXY(128,38)], (127,37), (128,38),
            'A', 'B', [], 100, 60, 1, 'test', 'TIME', [],
            dict(car_type=1, car_fuel='gasoline', car_hipass=False), [guide])
        filename = Path(temporary.name) / f'{index}.gpkg'
        files.append(str(filename))
        plugin._write_history_layer(plugin.route_history_layer, filename, 'naver_route_history', 'LineString')
        plugin._write_history_layer(plugin.guidance_history_layer, filename, 'naver_guidance_history', 'Point')
        # Each input has just its own history.
        plugin.route_history_layer.dataProvider().truncate()
        plugin.guidance_history_layer.dataProvider().truncate()
    def counts():
        return plugin.route_history_layer.featureCount(), plugin.guidance_history_layer.featureCount()
    def load(paths):
        with patch.object(module.QFileDialog, 'getOpenFileNames', return_value=(paths, '')):
            plugin._load_route_history_file()
    load(files[:2])
    assert counts() == (2, 2)
    load(files[:2])
    assert counts() == (2, 2), 'duplicate batch'
    load([])
    assert counts() == (2, 2), 'cancel picker'
    with patch.object(module.QMessageBox, 'critical') as error:
        load([files[2], str(Path(temporary.name) / 'missing.gpkg')])
        error.assert_called_once()
    assert counts() == (2, 2), 'invalid batch must not import valid first file'
    original = plugin._append_imported_history
    calls = 0
    def fail_second(*args, **kwargs):
        global calls
        calls += 1
        if calls == 2:
            raise RuntimeError('injected guidance failure')
        return original(*args, **kwargs)
    with patch.object(plugin, '_append_imported_history', side_effect=fail_second), patch.object(module.QMessageBox, 'critical'):
        load([files[2]])
    assert counts() == (2, 2), 'import rollback'
    load([files[2]])
    assert counts() == (3, 3)
    plugin.active_route_history_id = '0'
    with patch.object(module.QMessageBox, 'question', return_value=MSGBOX_NO):
        plugin._delete_route_histories(json.dumps(['0','1']))
    assert counts() == (3, 3)
    for invalid in ('{}', '[1]', 'bad json'):
        plugin._delete_route_histories(invalid)
    assert counts() == (3, 3)
    # Nested modal events cannot start another file picker or batch delete.
    def confirm(*args):
        with patch.object(module.QFileDialog, 'getOpenFileNames') as picker:
            plugin._load_route_history_file()
            picker.assert_not_called()
        plugin._delete_route_histories('["2"]')
        return MSGBOX_YES
    with patch.object(module.QMessageBox, 'question', side_effect=confirm) as question:
        plugin._delete_route_histories('["0","1","1","missing"]')
        question.assert_called_once()
        assert '2건' in question.call_args.args[2]
    assert counts() == (1, 1)
    assert plugin._memory_history_ids(plugin.route_history_layer) == {'2'}
    plugin._clear_current_route_display.assert_called_once()
    # Project switches while the dialog is open invalidate the pending action.
    def switch_project(*args):
        plugin.project_epoch += 1
        return MSGBOX_YES
    with patch.object(module.QMessageBox, 'question', side_effect=switch_project):
        plugin._delete_route_histories('["2"]')
    assert counts() == (1, 1)
    bridge = NaverWebBridge()
    imports, deletes = [], []
    bridge.routeHistoryImportRequested.connect(lambda: imports.append(True))
    bridge.routeHistoryBatchDeleteRequested.connect(deletes.append)
    bridge.importRouteHistory()
    bridge.deleteRouteHistories('["2"]')
    assert imports == [True] and deletes == ['["2"]']
    plugin.external_bridge_server = Mock()
    plugin.external_bridge_server.next_event.side_effect = [
        dict(epoch=plugin.project_epoch, type='import_route_history', payload={}),
        dict(epoch=plugin.project_epoch, type='delete_route_histories', payload={'history_ids_json':'["2"]'}), None]
    with patch.object(plugin, '_load_route_history_file') as importer, patch.object(plugin, '_delete_route_histories') as deleter:
        plugin._process_external_bridge_events()
        importer.assert_called_once_with()
        deleter.assert_called_once_with('["2"]')
    print('PASS', Qgis.QGIS_VERSION, 'batch import/dedup/cancel/invalid/rollback, delete/cancel/project-switch/reentry, WebChannel signals')
finally:
    QgsProject.instance().removeAllMapLayers()
    del plugin, original
    import gc
    gc.collect()
    app.exitQgis()
    temporary.cleanup()
