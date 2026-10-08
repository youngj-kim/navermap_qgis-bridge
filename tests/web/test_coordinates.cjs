// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const path = require('path');
const html = require('./load_viewer.cjs').loadViewer();
const start = html.indexOf('    function parseCoordinateInput(');
const end = html.indexOf('    function formatCoordinate(', start);
assert.ok(start > 0 && end > start);
const context = vm.createContext({});
vm.runInContext(html.slice(start, end), context);
const cases = [
  ['127.1,37.4', {lon:127.1, lat:37.4}],
  ['37.4,127.1', {lon:127.1, lat:37.4}],
  [' 127.1 37.4 ', {lon:127.1, lat:37.4}],
  ['-127.1,-37.4', {lon:-127.1, lat:-37.4}],
  ['180,90', {lon:180, lat:90}],
  ['0,0', {lon:0, lat:0}],
  ['45,80', {lon:45, lat:80}], // Ambiguous values retain longitude-first behavior.
  ['181,37', null], ['127,91', null], ['NaN,37', null],
  ['Infinity,37', null], ['', null], ['127,', null],
  ['127,37,0', null], ['서울역', null]
];
for (const [value, expected] of cases) {
  const actual = context.parseCoordinateInput(value);
  assert.deepEqual(actual && JSON.parse(JSON.stringify(actual)), expected, value);
}
console.log(`PASS: ${cases.length} coordinate input cases`);
