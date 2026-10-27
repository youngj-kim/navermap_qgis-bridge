# SPDX-License-Identifier: GPL-2.0-or-later
"""Build a source-only QGIS plugin ZIP, excluding credentials and dev artifacts."""
import argparse
import ast
import configparser
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


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
    parser.add_argument("--label", default="test-20261008", help="Filename label, not metadata version")
    args = parser.parse_args()
    if not args.label or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                             for character in args.label):
        raise ValueError("Invalid build label")
    metadata = configparser.ConfigParser()
    metadata.read(PLUGIN / "metadata.txt", encoding="utf-8-sig")
    version = metadata["general"]["version"]
    if not version or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
                          for character in version):
        raise ValueError("Invalid metadata version")
    output = ROOT / "dist" / f"navermap_qgis_bridge-{version}-{args.label}.zip"
    entries = package_entries()
    output.parent.mkdir(exist_ok=True)
    # Never overwrite an existing test package silently.
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for name, source in sorted(entries.items()):
            archive.write(source, name)
    count = validate_archive(output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(output)
    print(f"PASS: {count} files; one plugin root; syntax/imports/assets/CRC checked; no local settings")
    print(f"Size: {output.stat().st_size} bytes; SHA256: {digest}")


if __name__ == "__main__":
    main()
