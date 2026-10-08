# SPDX-License-Identifier: GPL-2.0-or-later
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from xml.etree import ElementTree as ET

from navermap_qgis_bridge import gpx_export as gpx
from host_methods import find_method


STAMP = "2026-01-02T03:04:05+09:00"
NS = {"g": gpx.GPX_NS, "n": gpx.NAVER_NS}


def sample_route():
    route = {key: "" for key in gpx.ROUTE_FIELDS}
    route.update(history_id="test-history", route_id="test-route", searched_at=STAMP,
                 origin_lon=127.1, origin_lat=37.4, origin_name='출발 & <예시>',
                 destination_lon=127.2, destination_lat=37.5, destination_name='도착 "예시"',
                 waypoints_json=json.dumps([{"lon": 127.15, "lat": 37.45, "label": "경유지"}]),
                 result_summary="예시 안내", distance_m=100, duration_s=60,
                 guidance_count=1, priority="RECOMMEND", avoid="", car_type=1,
                 car_fuel="gasoline", car_hipass=0)
    return route


def sample_guide():
    return dict(sequence=1, longitude=127.16, latitude=37.46, guidance="좌회전 & 직진",
                category="left", name="안내", guide_type=1, distance_m=20, duration_s=5)


POINTS = [(127.1, 37.4), (127.15, 37.45), (127.2, 37.5)]


class GpxExportTests(unittest.TestCase):
    def build(self, route=None, points=None, guides=None):
        return gpx.build_gpx_document([
            (sample_route() if route is None else route,
             POINTS if points is None else points,
             [sample_guide()] if guides is None else guides)
        ], STAMP)

    def test_matches_before_refactor_fixture(self):
        tree, _, _ = self.build()
        fixture = Path(__file__).parent / "fixtures" / "history_before_refactor.gpx"
        expected = ET.parse(fixture).getroot()
        self.assertEqual(ET.tostring(tree.getroot()), ET.tostring(expected))

    def test_namespace_metadata_and_counts(self):
        tree, route_count, guide_count = self.build()
        root = tree.getroot()
        self.assertEqual(root.tag, "{" + gpx.GPX_NS + "}gpx")
        self.assertEqual(root.attrib, {"version": "1.1", "creator": "Naver Map QGIS Bridge"})
        self.assertEqual(root.findtext("g:metadata/g:time", namespaces=NS), STAMP)
        self.assertEqual((route_count, guide_count), (1, 1))

    def test_waypoint_types_and_extension_attributes(self):
        tree, _, _ = self.build()
        points = tree.getroot().findall("g:wpt", NS)
        self.assertEqual([p.findtext("g:type", namespaces=NS) for p in points],
                         ["origin", "waypoint", "destination", "guidance:left"])
        self.assertEqual(points[-1].findtext("g:extensions/n:sequence", namespaces=NS), "1")
        for point in points:
            self.assertEqual(point.findtext("g:extensions/n:history_id", namespaces=NS), "test-history")

    def test_track_route_coordinate_precision(self):
        tree, _, _ = self.build()
        root = tree.getroot()
        track = root.findall("g:trk/g:trkseg/g:trkpt", NS)
        route = root.findall("g:rte/g:rtept", NS)
        expected = [{"lon": f"{lon:.8f}", "lat": f"{lat:.8f}"} for lon, lat in POINTS]
        self.assertEqual([p.attrib for p in track], expected)
        self.assertEqual([p.attrib for p in route], expected)
        self.assertEqual(root.findtext("g:trk/g:extensions/n:distance_m", namespaces=NS), "100")

    def test_short_geometries_skipped(self):
        for points in [[], [(127, 37)]]:
            with self.subTest(points=points):
                tree, count, guides = self.build(points=points)
                self.assertEqual((count, guides), (0, 0))
                self.assertEqual(len(tree.getroot()), 1)  # Metadata only.

    def test_empty_and_multiple_histories(self):
        tree, count, guides = gpx.build_gpx_document([], STAMP)
        self.assertEqual((count, guides, len(tree.getroot())), (0, 0, 1))
        record = (sample_route(), POINTS, [sample_guide()])
        tree, count, guides = gpx.build_gpx_document(iter([record, record]), STAMP)
        self.assertEqual((count, guides), (2, 2))
        self.assertEqual(len(tree.getroot().findall("g:trk", NS)), 2)

    def test_missing_waypoint_json_and_labels(self):
        for value in [None, "", "bad", "{}", "null"]:
            with self.subTest(value=value):
                route = sample_route()
                route.update(waypoints_json=value, origin_name="", destination_name=None)
                self.assertEqual(gpx.waypoints_from_history(route), [])
                self.assertEqual(gpx.gpx_route_name(route), "출발지 → 도착지")
                tree, _, count = self.build(route=route, guides=[])
                self.assertEqual(count, 0)
                self.assertEqual(len(tree.getroot().findall("g:wpt", NS)), 2)

    def test_invalid_waypoint_coordinates_not_serialized(self):
        root = ET.Element("root")
        for lon, lat in [(181, 37), (127, 91), (float("nan"), 37), (127, float("inf"))]:
            gpx.append_gpx_wpt(root, lon, lat, "invalid", "waypoint", "test-history")
        self.assertEqual(len(root), 0)

    def test_xml_text_escaped_without_changing_values(self):
        tree, _, _ = self.build()
        encoded = ET.tostring(tree.getroot(), encoding="unicode")
        self.assertIn("&amp;", encoded)
        self.assertIn("&lt;예시&gt;", encoded)
        decoded = ET.fromstring(encoded)
        self.assertEqual(decoded.findtext("g:wpt/g:name", namespaces=NS), '출발 & <예시>')

    def test_plugin_still_writes_and_saves_styles(self):
        method = find_method("_write_gpx_history")
        document = Mock()
        builder = Mock(return_value=(document, 1, 2))
        namespace = dict(build_gpx_document=builder, ROUTE_FIELDS=gpx.ROUTE_FIELDS,
                         GUIDE_FIELDS=gpx.GUIDE_FIELDS, datetime=Mock())
        exec(compile(ast.Module(body=[method], type_ignores=[]), "plugin.py", "exec"), namespace)
        plugin, layer = Mock(), Mock()
        layer.getFeatures.return_value = []
        path = Path("example.gpx")
        result = namespace[method.name](plugin, layer, None, path)
        self.assertEqual(result, (1, 2))
        document.write.assert_called_once_with(str(path), encoding="utf-8",
                                              xml_declaration=True, short_empty_elements=True)
        plugin._save_gpx_sidecar_styles.assert_called_once_with(path)

        class Feature(dict):
            def geometry(self):
                return "test-geometry"

        layer.getFeatures.return_value = [Feature(sample_route())]
        plugin._guidance_features_by_history.return_value = {"test-history": [sample_guide()]}
        plugin._route_points_from_geometry.return_value = [
            SimpleNamespace(x=lambda lon=lon: lon, y=lambda lat=lat: lat)
            for lon, lat in POINTS
        ]
        captured = []
        def capture_records(records, _timestamp):
            captured.extend(records)
            _, route_count, guide_count = gpx.build_gpx_document(captured, STAMP)
            return document, route_count, guide_count
        builder.side_effect = capture_records
        self.assertEqual(namespace[method.name](plugin, layer, None, path), (1, 1))
        self.assertEqual(captured, [(sample_route(), POINTS, [sample_guide()])])

        document.write.side_effect = OSError("test failure")
        plugin.reset_mock()
        with self.assertRaisesRegex(RuntimeError, "example.gpx 저장 실패"):
            namespace[method.name](plugin, layer, None, path)
        plugin._save_gpx_sidecar_styles.assert_not_called()


if __name__ == "__main__":
    unittest.main()
