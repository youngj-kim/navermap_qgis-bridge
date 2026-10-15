# SPDX-License-Identifier: GPL-2.0-or-later
import unittest
from xml.etree import ElementTree as ET

from navermap_qgis_bridge.credential_validation import validated_credential
from navermap_qgis_bridge.data_transforms import guidance_category
from navermap_qgis_bridge.gpx_export import gpx_text, gpx_naver_text


class ReviewRegressions(unittest.TestCase):
    def test_credentials_reject_non_ascii_spaces_and_controls(self):
        for value in ("", "example key", "example\x00key", "예시", "example\x7fkey"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validated_credential(value)
        self.assertEqual(validated_credential("PLACEHOLDER_ID"), "PLACEHOLDER_ID")

    def test_all_roundabout_codes_override_direction_text(self):
        for code in (*range(21, 35), *range(91, 105)):
            with self.subTest(code=code):
                self.assertEqual(guidance_category(code, "유턴 후 우회전"), "roundabout")

    def test_gpx_removes_invalid_xml_characters_from_all_text_helpers(self):
        root = ET.Element("root")
        text = "한글\x01\x00\x0b\ud800\ufffe😀\t\n"
        gpx_text(root, "name", text)
        gpx_naver_text(root, "history_id", text)
        parsed = ET.fromstring(ET.tostring(root, encoding="utf-8"))
        self.assertEqual([item.text for item in parsed], ["한글😀\t\n"] * 2)
