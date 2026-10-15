# SPDX-License-Identifier: GPL-2.0-or-later
import ast
import math
from pathlib import Path
import unittest

from navermap_qgis_bridge import data_transforms as transforms
from host_methods import find_method


class DataTransformsTests(unittest.TestCase):
    def test_coordinate_conversion(self):
        for value, expected in [("1271005516", 127.1005516),
                                ("374669954", 37.4669954),
                                (127.5, 127.5), (-1275000000, -127.5),
                                (0, 0), (1000, 1000)]:
            with self.subTest(value=value):
                self.assertEqual(transforms.local_search_coordinate(value), expected)
        for value in [None, "", "invalid", float("nan"), float("inf")]:
            with self.subTest(value=value):
                self.assertIsNone(transforms.local_search_coordinate(value))

    def test_poi_normalization(self):
        self.assertEqual(transforms.normalize_local_search_items([{
            "title": " <b>예시 장소</b> ", "mapx": "1275000000",
            "mapy": "375000000", "roadAddress": " 예시 도로 ",
            "address": "예시 지번", "category": "분류",
            "description": "<b>설명</b>"
        }]), [{"title": "예시 장소", "address": "예시 도로",
               "roadAddress": "예시 도로", "jibunAddress": "예시 지번",
               "category": "분류", "description": "설명",
               "lon": 127.5, "lat": 37.5, "source": "local"}])

    def test_poi_aliases_and_fallbacks(self):
        for lon_key, lat_key in [("longitude", "latitude"), ("lon", "lat"), ("x", "y")]:
            with self.subTest(lon_key=lon_key):
                result = transforms.normalize_local_search_items([
                    {lon_key: 127, lat_key: 37, "category": "분류"}])[0]
                self.assertEqual((result["lon"], result["lat"]), (127, 37))
                self.assertEqual(result["title"], "분류")
        result = transforms.normalize_local_search_items([{"lon": 127, "lat": 37}])[0]
        self.assertEqual(result["title"], "POI 검색 결과")

    def test_invalid_poi_items(self):
        self.assertEqual(transforms.normalize_local_search_items([
            None, "invalid", {}, {"lon": "bad", "lat": 37},
            {"lon": 181, "lat": 37}, {"lon": 127, "lat": 91},
            {"lon": "nan", "lat": 37}
        ]), [])

    def test_guidance_precedence(self):
        for code, text, expected in [
            (1, "", "straight"), (2, "", "left"), (3, "방면으로 우회전", "right"),
            (4, "", "left"), (5, "", "right"), (6, "", "uturn"), (8, "", "left"),
            (11, "", "left"), (12, "", "left"), (13, "", "left"),
            (14, "", "right"), (15, "", "right"), (16, "", "right"),
            (87, "", "waypoint"), (88, "", "destination"),
            (100, "좌회전", "roundabout"), (101, "우회전", "roundabout"),
            (21, "직진", "roundabout"), (34, "", "roundabout"),
            (91, "", "roundabout"), (104, "", "roundabout"),
            (50, "왼쪽", "transition"), (122, "", "transition"),
            (999, "유턴 후 좌회전", "uturn"), (999, "왼쪽", "left"),
            (999, "오른쪽", "right"), (999, "직진", "straight"), (999, "", "other")
        ]:
            with self.subTest(code=code, text=text):
                self.assertEqual(transforms.guidance_category(code, text), expected)

    def test_numeric_and_html_behavior(self):
        for value in [None, "bad", ""]:
            self.assertEqual(transforms.safe_number(value), 0)
            self.assertEqual(transforms.safe_float(value), 0.0)
        self.assertEqual(transforms.safe_number(12.9), 12)
        self.assertEqual(transforms.safe_float("12.5"), 12.5)
        # Preserve existing behavior; finite-value validation belongs to callers.
        self.assertTrue(math.isnan(transforms.safe_float("nan")))
        self.assertEqual(transforms.strip_html("<b>A</b>&amp;B"), "A&B")

    def test_plugin_delegates_to_transforms(self):
        for name in ["normalize_local_search_items", "local_search_coordinate",
                     "strip_html", "safe_number", "safe_float", "guidance_category"]:
            method = find_method("_" + name)
            self.assertIsInstance(method.body[0], ast.Return)
            self.assertEqual(method.body[0].value.func.id, name)


if __name__ == "__main__":
    unittest.main()
