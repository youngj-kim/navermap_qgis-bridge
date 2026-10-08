// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const html = require('./load_viewer.cjs').loadViewer();
const start = html.indexOf('    function updateRoadviewPhotoDate()');
const end = html.indexOf('    function formatGuidanceDistance', start);
assert.ok(start > 0 && end > start);
const label = {textContent: ''};
const context = vm.createContext({document: {getElementById: id => {
  assert.equal(id, 'roadview-photo-date');
  return label;
}}, roadview: null});
vm.runInContext(html.slice(start, end), context);
let count = 0;
for (const [location, expected] of [
  [{photodate: '2024-06'}, '촬영일: 2024-06'],
  [{photodate: ' 2024-06-15 '}, '촬영일: 2024-06-15'],
  [{photodate: '202406'}, '촬영일: 202406'],
  [{photodate: ''}, '촬영일 정보 없음'],
  [{photodate: '  '}, '촬영일 정보 없음'],
  [{}, '촬영일 정보 없음'],
  [null, '촬영일 정보 없음'],
  [{photodate: 202406}, '촬영일 정보 없음'],
  [{photodate: '<img src=x onerror=alert(1)>'}, '촬영일: <img src=x onerror=alert(1)>']
]) {
  context.roadview = {getLocation: () => location};
  context.updateRoadviewPhotoDate();
  assert.equal(label.textContent, expected);
  count++;
}
for (const roadview of [null, {}, {getLocation: () => {throw Error('not ready');}}]) {
  context.roadview = roadview;
  context.updateRoadviewPhotoDate();
  assert.equal(label.textContent, '촬영일 정보 없음');
  count++;
}
assert.match(html, /addListener\(roadview, "pano_changed", \(\) => \{\s*updateRoadviewPhotoDate\(\);/);
assert.match(html, /addListener\(roadview, "init", \(\) => \{\s*updateRoadviewPhotoDate\(\);/);
console.log(`PASS: ${count} metadata cases, event hooks before sync suppression, text-only rendering`);
