# SPDX-License-Identifier: GPL-2.0-or-later
"""Build a source-only QGIS plugin ZIP, excluding credentials and dev artifacts."""
import argparse
import ast
import configparser
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from release_checks import scan


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "navermap_qgis_bridge"
PREFIX = "navermap_qgis_bridge/"
ROOT_ASSETS = {"metadata.txt", "LICENSE", "icon.png", "settings.example.json"}
WEB_EXTENSIONS = {".html", ".css", ".js", ".json", ".svg"}
USER_DOCS = ("setup.md", "usage.md", "troubleshooting.md", "fare-comparison.md",
             "install-test-checklist.md", "install-test-checklist.html",
             "setup.en.md", "usage.en.md", "troubleshooting.en.md", "fare-comparison.en.md",
             "install-test-checklist.en.md", "install-test-checklist.en.html")


def package_entries():
    entries = {}
    for source in PLUGIN.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(PLUGIN)
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        include = (len(relative.parts) == 1 and
                   (source.suffix == ".py" or relative.name in ROOT_ASSETS))
        include = include or (relative.parts[0] == "web" and source.suffix in WEB_EXTENSIONS)
        if include and relative.name != "settings.json":
            if source.suffix == ".py":
                ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(relative))
            entries[PREFIX + relative.as_posix()] = source
    entries[PREFIX + "README.md"] = ROOT / "docs" / "package-readme.md"
    entries[PREFIX + "README.en.md"] = ROOT / "docs" / "package-readme.en.md"
    entries[PREFIX + "CHANGELOG.md"] = ROOT / "CHANGELOG.md"
    entries[PREFIX + "CHANGELOG.en.md"] = ROOT / "CHANGELOG.en.md"
    for name in USER_DOCS:
        entries[PREFIX + "docs/" + name] = ROOT / "docs" / name
    example = json.loads((PLUGIN / "settings.example.json").read_text(encoding="utf-8-sig"))
    if not all(isinstance(value, str) and value.startswith("YOUR_") for value in example.values()):
        raise ValueError("Example configuration must contain placeholders only")
    return entries


def validate_archive(filename):
    with ZipFile(filename) as archive:
        names = archive.namelist()
        if any(not name.startswith(PREFIX) or ".." in Path(name).parts for name in names):
            raise ValueError("Invalid plugin root or archive path")
        if any(Path(name).name == "settings.json" or "__pycache__" in name or name.endswith(".pyc")
               for name in names):
            raise ValueError("Local settings or bytecode found in archive")
        if archive.testzip() is not None:
            raise ValueError("ZIP checksum validation failed")
        for name in ["__init__.py", "plugin.py", "metadata.txt", "LICENSE", "web_bridge.py",
                     "viewer_document.py", "web/navermap_viewer.html", "web/viewer_assets.json",
                     "web/js/external_transport.js"]:
            if PREFIX + name not in names:
                raise ValueError("Required package file missing: " + name)
        manifest = json.loads(archive.read(PREFIX + "web/viewer_assets.json"))
        for name in ("README.md", "README.en.md", "CHANGELOG.md", "CHANGELOG.en.md",
                     *("docs/" + item for item in USER_DOCS)):
            if PREFIX + name not in names:
                raise ValueError("User documentation missing: " + name)
        for asset in [manifest["css"], *manifest["scripts"]]:
            if PREFIX + "web/" + asset not in names:
                raise ValueError("Viewer asset missing: " + asset)
        for name in names:
            if name.endswith(".py"):
                source = archive.read(name).decode("utf-8-sig")
                tree = ast.parse(source, filename=name)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                        module = PREFIX + node.module.replace(".", "/") + ".py"
                        if module not in names:
                            raise ValueError("Internal import missing from archive: " + module)
        return len(names)


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--label", help="Test filename label, not metadata version")
    mode.add_argument("--release", action="store_true", help="Build a version-only release filename")
    mode.add_argument("--experimental", action="store_true", help="Build a version-only experimental filename")
    parser.add_argument("--scanner-path", default=str(ROOT / "dist/security-tools"))
    parser.add_argument("--qt6-checker", default=str(ROOT / "dist/pyqt5_to_pyqt6.py"))
    parser.add_argument("--qgis4-launcher", default=os.environ.get("QGIS4_PYTHON"))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    label = None if args.release or args.experimental else (args.label if args.label is not None else "test-20261008")
    if label is not None and (not label or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                                              for character in label)):
        raise ValueError("Invalid build label")
    metadata = configparser.ConfigParser()
    metadata.read(PLUGIN / "metadata.txt", encoding="utf-8-sig")
    version = metadata["general"]["version"]
    if not version or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
                          for character in version):
        raise ValueError("Invalid metadata version")
    if args.release and (metadata["general"].getboolean("experimental", fallback=True)
                         or not metadata["general"].get("changelog", "").strip()):
        raise ValueError("Release builds require non-experimental metadata and a changelog")
    if args.experimental and (not metadata["general"].getboolean("experimental", fallback=False)
                              or not metadata["general"].get("changelog", "").strip()):
        raise ValueError("Experimental builds require experimental metadata and a changelog")
    suffix = "" if label is None else f"-{label}"
    output = args.output_dir.resolve() / f"navermap_qgis_bridge-{version}{suffix}.zip"
    entries = package_entries()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.with_suffix(".checks").exists():
        raise FileExistsError(f"Build output already exists: {output}")
    with tempfile.TemporaryDirectory(prefix="release-check-", dir=output.parent) as temporary:
        staging = Path(temporary)
        candidate = staging / "candidate.zip"
        with ZipFile(candidate, "x", compression=ZIP_DEFLATED) as archive:
            for name, source in sorted(entries.items()):
                archive.write(source, name)
        count = validate_archive(candidate)
        if args.release or args.experimental:
            print("Checking extracted distribution: security and QGIS 4 / Qt6...", flush=True)
            extracted = staging / "extracted"
            with ZipFile(candidate) as archive:
                archive.extractall(extracted)
            package = extracted / "navermap_qgis_bridge"
            before = {p.relative_to(package): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in package.rglob("*") if p.is_file()}
            reports = staging / "reports"
            summary = scan(package, reports, args.scanner_path, args.qgis4_launcher, args.qt6_checker)
            after = {p.relative_to(package): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in package.rglob("*") if p.is_file()}
            if before != after:
                raise RuntimeError("Scanner modified the extracted distribution")
            summary["zip_sha256"] = hashlib.sha256(candidate.read_bytes()).hexdigest()
            (reports / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            shutil.copytree(reports, output.with_suffix(".checks"))
        else:
            print("DEVELOPMENT ONLY: security/Qt6 release gates were not run")
        # Exclusive creation prevents silently replacing an existing release.
        with output.open("xb") as destination:
            try:
                with candidate.open("rb") as source:
                    shutil.copyfileobj(source, destination)
            except BaseException:
                destination.close()
                output.unlink()
                raise
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(output)
    print(f"PASS: {count} files; one plugin root; syntax/imports/assets/CRC checked; no local settings")
    print(f"Size: {output.stat().st_size} bytes; SHA256: {digest}")


if __name__ == "__main__":
    main()
