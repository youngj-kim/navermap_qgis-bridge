# SPDX-License-Identifier: GPL-2.0-or-later
"""Assemble split web sources into one document for both viewer transports."""

import json
import os
from pathlib import Path


WEB_DIR = Path(__file__).resolve().parent / "web"
CHANNEL_SCRIPT = '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>'


def external_bridge_script():
    script = (WEB_DIR / "js" / "external_transport.js").read_text(encoding="utf-8")
    return "<script>\n" + script + "\n</script>"


def build_viewer_html(app_key, bridge_script=None, *, debug=None):
    manifest = json.loads((WEB_DIR / "viewer_assets.json").read_text(encoding="utf-8"))
    html = (WEB_DIR / "navermap_viewer.html").read_text(encoding="utf-8")
    css = (WEB_DIR / manifest["css"]).read_text(encoding="utf-8")
    javascript = "\n".join(
        (WEB_DIR / filename).read_text(encoding="utf-8")
        for filename in manifest["scripts"]
    )
    if debug is None:
        debug = os.environ.get("NAVER_BRIDGE_DEBUG", "").lower() in {"1", "true", "yes"}
    if not debug:
        css += "\n#viewer-build, #reverse-sync-diagnostic { display: none; }\n"
    html = html.replace("__VIEWER_CSS__", css).replace("__VIEWER_JS__", javascript)
    # Do not let a credential containing HTML delimiters terminate the script tag.
    key_json = json.dumps(app_key).replace("<", "\\u003c").replace(">", "\\u003e")
    html = html.replace("__NAVER_APP_KEY_JSON__", key_json)
    if bridge_script is not None:
        html = html.replace(CHANNEL_SCRIPT, bridge_script)
    return html
