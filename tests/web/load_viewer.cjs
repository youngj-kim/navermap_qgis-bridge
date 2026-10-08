// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const path = require('path');
const webDir = path.join(__dirname, '../../navermap_qgis_bridge/web');
const read = name => fs.readFileSync(path.join(webDir, name), 'utf8').replace(/\r\n/g, '\n');

function loadViewer({appKey = '', bridgeScript, debug = false} = {}) {
  const manifest = JSON.parse(read('viewer_assets.json'));
  let css = read(manifest.css);
  if (!debug) css += '\n#viewer-build, #reverse-sync-diagnostic { display: none; }\n';
  const js = manifest.scripts.map(read).join('\n');
  let html = read('navermap_viewer.html').replace('__VIEWER_CSS__', css).replace('__VIEWER_JS__', js);
  const key = JSON.stringify(appKey).replace(/</g, '\\u003c').replace(/>/g, '\\u003e');
  html = html.replace('__NAVER_APP_KEY_JSON__', key);
  if (bridgeScript !== undefined) {
    html = html.replace('<script src="qrc:///qtwebchannel/qwebchannel.js"></script>', bridgeScript);
  }
  return html;
}

module.exports = {loadViewer};
