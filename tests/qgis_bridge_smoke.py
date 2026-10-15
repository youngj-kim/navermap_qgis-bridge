# SPDX-License-Identifier: GPL-2.0-or-later
"""Check the default localhost bridge with a real QGIS Python runtime.

No NAVER calls, viewer HTML, credentials or profile writes are used.
"""
import json
import os
import sys
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qgis.core import Qgis
from navermap_qgis_bridge.external_bridge import NaverExternalBridgeServer
from navermap_qgis_bridge.settings import naver_map_base_url

with patch.dict(os.environ, {"NAVER_MAP_BASE_URL": ""}):
    assert naver_map_base_url() == "http://localhost:8083/navermap_qgis_bridge/"

server = NaverExternalBridgeServer()
opener = build_opener(ProxyHandler({}))
try:
    assert server.start().startswith("http://localhost:8083/#token=")
    with opener.open(Request(server.url.split("#")[0] + "api/state", headers={"X-Bridge-Token": server._token}), timeout=5) as response:
        assert response.status == 200
        assert json.load(response) == {"center": None, "epoch": 0, "accepting": True, "sequence": 0}
    server.set_center(127.1, 37.4)
    with opener.open(Request(server.url.split("#")[0] + "api/state", headers={"X-Bridge-Token": server._token}), timeout=5) as response:
        center = json.load(response)["center"]
        assert center["lon"] == 127.1 and center["lat"] == 37.4
finally:
    server.stop()
assert server.url == ""
print(f"PASS: QGIS {Qgis.QGIS_VERSION}; default origin and HTTP bridge on 8083; state and shutdown")
