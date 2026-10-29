# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed checks of the extracted distribution, never of the working tree."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


CHECKER_SHA256 = "026424b50e6e2920fe604e1e637842f141115f5784d6f7144f61aacddc9a2771"


def run(command, environment):
    result = subprocess.run(command, env=environment, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=300)
    if result.returncode:
        # Scanner output may contain credentials. Keep it out of console/build logs.
        raise RuntimeError(f"Release check failed: {Path(command[0]).name} (exit {result.returncode})")
    return result.stdout


def check_reports(bandit, secrets, qt_log):
    if bandit.get("errors") or bandit.get("results") or "results" not in bandit:
        raise RuntimeError("Bandit reported findings or an incomplete scan")
    if "results" not in secrets or secrets["results"]:
        raise RuntimeError("detect-secrets reported findings or an incomplete scan")
    if qt_log.strip() != "=== dry_run mode | Start Logs ===":
        raise RuntimeError("Qt6 checker reported findings or an incomplete scan")


def scan(package, reports, scanner_path, qt_launcher, checker):
    scanner_path, checker = Path(scanner_path).resolve(), Path(checker).resolve()
    if not scanner_path.is_dir() or not checker.is_file() or not qt_launcher:
        raise RuntimeError("Release checks require scanner dependencies, a QGIS 4 launcher and Qt6 checker")
    if hashlib.sha256(checker.read_bytes()).hexdigest() != CHECKER_SHA256:
        raise RuntimeError("Qt6 checker does not match the reviewed SHA256; review tool updates first")
    reports.mkdir()
    environment = dict(os.environ, PYTHONPATH=str(scanner_path), PYTHONDONTWRITEBYTECODE="1")
    bandit_path = reports / "bandit.json"
    run([sys.executable, "-B", "-m", "bandit", "-r", str(package),
         "-f", "json", "-o", str(bandit_path)], environment)
    secrets = json.loads(run([sys.executable, "-B", "-m", "detect_secrets", "scan",
                              "--all-files", str(package)], environment))
    run([sys.executable, "-B", "-m", "flake8", str(package),
         "--isolated", "--select", "E731,F821,F822,F823"], environment)
    qt_log = reports / "qt6.log"
    worker = Path(__file__).with_name("qt6_check.py")
    run([qt_launcher, "-B", str(worker), str(scanner_path), str(checker),
         str(package), str(qt_log)], environment)
    check_reports(json.loads(bandit_path.read_text(encoding="utf-8")), secrets,
                  qt_log.read_text(encoding="utf-8"))
    (reports / "detect-secrets.json").write_text(json.dumps(secrets, indent=2), encoding="utf-8")
    versions = run([sys.executable, "-B", "-c",
                   "import importlib.metadata,json; print(json.dumps({n:importlib.metadata.version(n) "
                   "for n in ['bandit','detect-secrets','flake8','tokenize-rt']}))"], environment)
    return {"tools": json.loads(versions), "qt6_checker_sha256": CHECKER_SHA256,
            "checks": ["bandit", "detect-secrets", "flake8", "qgis4-qt6"]}
