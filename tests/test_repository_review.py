# SPDX-License-Identifier: GPL-2.0-or-later
"""Security/Qt compatibility invariants from the 0.99 repository review."""
import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "navermap_qgis_bridge"


class RepositoryReviewTests(unittest.TestCase):
    def test_gpx_module_only_uses_xml_export_apis(self):
        tree = ast.parse((ROOT / "gpx_export.py").read_text(encoding="utf-8-sig"))
        xml_apis = {node.attr for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "ET"}
        self.assertEqual(xml_apis, {"Element", "SubElement", "ElementTree", "register_namespace"})

    def test_credential_identifiers_keep_existing_user_configuration(self):
        tree = ast.parse((ROOT / "settings.py").read_text(encoding="utf-8-sig"))
        constants = {node.targets[0].id: ast.literal_eval(node.value)
                     for node in tree.body if isinstance(node, ast.Assign)
                     and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant)}
        self.assertEqual(constants["ENV_NAVER_API_HUB_REST_KEY"], "NAVER_API_HUB_CLIENT_SECRET")
        self.assertEqual(constants["QGIS_NAVER_API_HUB_REST_KEY"],
                         "navermap_qgis_bridge/naver_api_hub_client_secret")
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in {"environment_api_hub_client_secret", "stored_api_hub_client_secret"}]
        namespace = {**constants, "os": os}
        namespace["QgsSettings"] = lambda: type("Settings", (), {
            "value": lambda self, name, default: "PLACEHOLDER_SECRET" if name == constants["QGIS_NAVER_API_HUB_REST_KEY"] else default})()
        exec(compile(ast.Module(body=functions, type_ignores=[]), "settings.py", "exec"), namespace)
        with patch.dict(os.environ, {"NAVER_API_HUB_CLIENT_SECRET": "PLACEHOLDER_ENV"}):
            self.assertEqual(namespace["environment_api_hub_client_secret"](), "PLACEHOLDER_ENV")
        self.assertEqual(namespace["stored_api_hub_client_secret"](), "PLACEHOLDER_SECRET")

    def test_missing_web_runtime_reports_external_fallback(self):
        tree = ast.parse((ROOT / "dock_widget.py").read_text(encoding="utf-8-sig"))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in {"_record_import_error", "web_runtime_diagnostic"}]
        namespace = {"QWebEngineView": None, "QWebChannel": None, "WEB_RUNTIME_IMPORT_ERRORS": []}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "dock_widget.py", "exec"), namespace)
        namespace["_record_import_error"]("Qt WebEngine", ImportError("unavailable"))
        self.assertIn("Qt WebEngine: unavailable", namespace["web_runtime_diagnostic"]())
        namespace.update(QWebEngineView=object(), QWebChannel=object())
        self.assertEqual(namespace["web_runtime_diagnostic"](), "")

    def test_plugin_uses_qgis_pyqt_imports_only(self):
        for source in ROOT.glob("*.py"):
            for node in ast.walk(ast.parse(source.read_text(encoding="utf-8-sig"))):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or "").startswith(("PyQt5", "PyQt6")), str(source))
