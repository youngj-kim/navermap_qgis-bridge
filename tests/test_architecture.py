# SPDX-License-Identifier: GPL-2.0-or-later
import ast
import builtins
import os
import shutil
import subprocess
import symtable
import unittest

from host_methods import ROOT, HOST_MODULES, host_classes
from navermap_qgis_bridge.viewer_document import build_viewer_html, CHANNEL_SCRIPT


class ArchitectureTests(unittest.TestCase):
    def test_all_python_sources_parse(self):
        for path in ROOT.glob("*.py"):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8-sig"))

    def test_host_global_dependencies_declared(self):
        for filename in [path.name for path in ROOT.glob("*.py")]:
            source = (ROOT / filename).read_text(encoding="utf-8-sig")
            table = symtable.symtable(source, filename, "exec")
            available = set(table.get_identifiers()) | set(dir(builtins)) | {"__file__", "__name__"}
            def check(scope):
                for symbol in scope.get_symbols():
                    if symbol.is_global() and symbol.is_referenced():
                        self.assertIn(symbol.get_name(), available, f"{filename}: {symbol.get_name()}")
                for child in scope.get_children():
                    check(child)
            check(table)

    def test_host_methods_resolve_without_duplicate_owners(self):
        owners = {}
        nodes = list(host_classes())
        for filename, cls in nodes:
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                # The getter/setter pair intentionally has one property name.
                if method.name == "route_reply":
                    continue
                self.assertNotIn(method.name, owners, method.name)
                owners[method.name] = filename
        for filename, cls in nodes:
            for node in ast.walk(cls):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "self" and node.func.attr.startswith("_")):
                    self.assertIn(node.func.attr, owners, f"{filename}: {node.func.attr}")

    def test_native_and_external_document_assembly(self):
        native = build_viewer_html("PLACEHOLDER_KEY", debug=True)
        external = build_viewer_html("PLACEHOLDER_KEY", "<script>/* external test */</script>", debug=True)
        self.assertIn(CHANNEL_SCRIPT, native)
        self.assertNotIn(CHANNEL_SCRIPT, external)
        self.assertIn("/* external test */", external)
        for html in [native, external]:
            for token in ["__VIEWER_CSS__", "__VIEWER_JS__", "__NAVER_APP_KEY_JSON__"]:
                self.assertNotIn(token, html)
            self.assertIn('const naverAppKey = "PLACEHOLDER_KEY";', html)
            self.assertIn("function updateRoadviewPhotoDate()", html)
            self.assertIn("#roadview-photo-date", html)

    def test_debug_is_optional_and_key_cannot_end_script(self):
        normal = build_viewer_html("", debug=False)
        debug = build_viewer_html("", debug=True)
        hidden = "#viewer-build, #reverse-sync-diagnostic { display: none; }"
        self.assertIn(hidden, normal)
        self.assertNotIn(hidden, debug)
        html = build_viewer_html("</script><script>test</script>", debug=True)
        self.assertIn('"\\u003c/script\\u003e', html)
        self.assertNotIn('const naverAppKey = "</script>', html)

    def test_browser_fixture_matches_production_document(self):
        node = os.environ.get("TEST_NODE_COMMAND") or shutil.which("node")
        if not node:
            self.skipTest("Node.js unavailable; renderer parity requires Node.js")
        result = subprocess.run([
            node, "-e",
            "process.stdout.write(require('./tests/web/load_viewer.cjs').loadViewer());",
        ], cwd=ROOT.parent, capture_output=True, encoding="utf-8", check=True)
        self.assertEqual(result.stdout, build_viewer_html("", debug=False))
