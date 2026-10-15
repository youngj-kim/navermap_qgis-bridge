# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from navermap_qgis_bridge.history_schema import history_memory_uri, history_import_fields, history_shapefile_fields
from navermap_qgis_bridge.view_scale import ground_distance


class SchemaAndScaleTests(unittest.TestCase):
    def test_legacy_aliases_and_fare_fields_match_memory_order(self):
        for kind, count in (("route", 22), ("guidance", 17)):
            exported = history_shapefile_fields(kind)
            imported = history_import_fields(kind)
            names = [field.split(":")[0] for field in history_memory_uri(kind).split("&field=")[1:]]
            self.assertEqual(names, [spec["source"] for spec in exported])
            self.assertEqual(len(names), count)
            self.assertEqual(imported, [{"source":s["source"],"name":s["name"]} for s in exported])
            self.assertTrue(all(len(s["name"]) <= 10 for s in exported))
            self.assertEqual(len({s["name"] for s in exported}), count)
        self.assertIn({"source":"destination_lon","name":"dst_lon"}, history_import_fields("route"))
        self.assertEqual(history_memory_uri("route").split("&field=")[-2:], ['toll_fare:integer','taxi_fare:integer'])

    def test_ground_distance_known_scale_and_dateline(self):
        self.assertEqual(ground_distance((127,37),(127,37)), 0)
        self.assertAlmostEqual(ground_distance((0,0),(1,0)), 111195.08, places=1)
        self.assertAlmostEqual(ground_distance((179.5,0),(-179.5,0)), 111195.08, places=1)
        with self.assertRaises(ValueError):
            ground_distance((float("nan"),0), (127,37))
