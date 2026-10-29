# SPDX-License-Identifier: GPL-2.0-or-later
"""Run the official checker with full QGIS 4 introspection, in dry-run mode."""
import runpy
import sys


def main():
    dependencies, checker, package, logfile = sys.argv[1:]
    sys.path.insert(0, dependencies)
    import qgis._3d
    import qgis.analysis
    import qgis.gui
    from qgis.core import Qgis
    from qgis.PyQt.QtCore import QT_VERSION_STR
    if Qgis.QGIS_VERSION_INT < 40000 or not QT_VERSION_STR.startswith("6."):
        raise RuntimeError("Full Qt6 checking requires QGIS 4 with Qt6")
    sys.argv = [checker, "--dry_run", "--logfile", logfile, package]
    runpy.run_path(checker, run_name="__main__")


if __name__ == "__main__":
    main()
