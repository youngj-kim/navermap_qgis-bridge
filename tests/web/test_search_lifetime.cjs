// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const source = fs.readFileSync(require('path').join(__dirname, '../../navermap_qgis_bridge/web/js/search.js'), 'utf8');
const selections = [], renders = [], statuses = [];
let complete;
const context = vm.createContext({
  parseCoordinateInput: q => q === '127,37' ? {lon:127,lat:37} : null,
  formatCoordinate: () => '127,37', searchResults: {hidden:false},
  qgisBridge: {}, geocoderService: {}, searchRequestId: 0,
  searchSubmit: {disabled:false}, lastLocalSearchError: '', setStatus: s => statuses.push(s),
  geocodeAddress: () => new Promise(resolve => { complete = resolve; }),
  renderSearchResults: results => renders.push(results),
  selectSearchResult: result => selections.push(result)
});
context.mapLanguage = 'ko';
vm.runInContext(require('fs').readFileSync(require('path').join(__dirname, '../../navermap_qgis_bridge/web/js/i18n.js'), 'utf8'), context);
vm.runInContext(source.slice(source.indexOf('    function searchLocal(')), context);
context.searchLocal('old place');
assert.equal(context.searchSubmit.disabled, true);
context.searchLocal('127,37');
assert.equal(context.searchSubmit.disabled, false);
const statusCount = statuses.length;
complete([{lon:128,lat:38,title:'old result'}]);
setImmediate(() => {
  assert.equal(selections.length, 1);
  assert.equal(renders.length, 0, 'stale results must not reopen the list');
  assert.equal(statuses.length, statusCount, 'stale status must not overwrite coordinates');
  assert.equal(context.searchSubmit.disabled, false);
  console.log('PASS: coordinate selection invalidates pending place search and restores controls');
});
