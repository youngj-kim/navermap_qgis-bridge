# SPDX-License-Identifier: GPL-2.0-or-later
"""Run related checks as a group, stopping on failure without installing dependencies."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WEB_CHECKS = ("test_photo_date.cjs", "test_coordinates.cjs", "test_search_lifetime.cjs",
              "test_external_transport.cjs", "test_view_scale.cjs", "test_workflows.cjs", "test_viewer_layout.cjs")
QGIS_CHECKS = ("qgis_smoke.py", "qgis_bridge_smoke.py", "qgis_lifecycle_smoke.py", "qgis_review_smoke.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("core", "web", "qgis"), action="append")
    parser.add_argument("--node", default=os.environ.get("TEST_NODE_COMMAND") or shutil.which("node"))
    parser.add_argument("--qgis-launcher", action="append", default=[])
    args = parser.parse_args()
    groups = args.group or ["core", "web"]
    commands = []
    if "core" in groups:
        commands.append([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"])
    if "web" in groups:
        if not args.node:
            parser.error("Node.js is required; provide --node")
        commands.extend([args.node, str(ROOT / "tests" / "web" / check)] for check in WEB_CHECKS)
    if "qgis" in groups:
        if not args.qgis_launcher:
            parser.error("Specify installed QGIS runtimes with --qgis-launcher")
        for launcher in args.qgis_launcher:
            commands.extend([launcher, "-B", str(ROOT / "tests" / check)] for check in QGIS_CHECKS)
    for command in commands:
        print("RUN:", subprocess.list2cmdline(command), flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print(f"PASS: {len(commands)} check commands ({', '.join(groups)})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
