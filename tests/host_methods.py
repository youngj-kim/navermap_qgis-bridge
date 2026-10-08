# SPDX-License-Identifier: GPL-2.0-or-later
"""Locate host methods without importing QGIS, after role-based extraction."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "navermap_qgis_bridge"
HOST_MODULES = ("plugin.py", "search_routes.py", "route_history.py",
                "history_exports.py", "map_layers.py", "canvas_sync.py")


def host_classes():
    for filename in HOST_MODULES:
        tree = ast.parse((ROOT / filename).read_text(encoding="utf-8-sig"))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                yield filename, node


def find_method(name):
    matches = [method for _, cls in host_classes() for method in cls.body
               if isinstance(method, ast.FunctionDef) and method.name == name]
    if len(matches) != 1:
        raise AssertionError(f"Expected one host method {name}, got {len(matches)}")
    return matches[0]
