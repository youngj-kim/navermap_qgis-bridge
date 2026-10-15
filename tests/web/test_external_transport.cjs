// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');

(async () => {
  const script = fs.readFileSync(path.join(__dirname, '../../navermap_qgis_bridge/web/js/external_transport.js'), 'utf8');
  const posts = [], intervals = [], centers = [], signals = [];
  let state = {epoch:0, accepting:true}, events = {epoch:0, events: []};
  const context = vm.createContext({
    URLSearchParams,
    window: {location: {hash: "#token=test-token"}, centerNaverMap: (...args) => centers.push(args), open() {}},
    document: {documentElement: {classList: {add() {}}}},
    console,
    setInterval: (callback, delay) => { assert.equal(delay, 400); intervals.push(callback); },
    fetch: async (url, options) => {
      if (options && options.method === 'POST') {
        posts.push({url, payload: JSON.parse(options.body), headers: options.headers});
        return {ok: true};
      }
      return {ok: true, json: async () => url === '/api/state' ? state : events};
    }
  });
  vm.runInContext(script, context);
  await new Promise(setImmediate);
  const bridge = context.window.naverExternalBridge;
  const cases = [
    ['moveQgisCenter', [127, 37], '/api/move-center', {lon:127, lat:37}],
    ['zoomQgisView', [127,37,2], '/api/zoom-view', {lon:127,lat:37,meters_per_pixel:2}],
    ['updateRoadviewState', [127,37,1,2,3,'test'], '/api/roadview-state', {lon:127,lat:37,pan:1,tilt:2,zoom:3,pano_id:'test'}],
    ['setRoutePoint', ['origin',127,37], '/api/route-point', {role:'origin',lon:127,lat:37}],
    ['clearRoutePoint', ['origin'], '/api/clear-route-point', {role:'origin'}],
    ['clearRoutePoints', [], '/api/clear-route-points', {}],
    ['cancelRoute', [], '/api/cancel-route', {}],
    ['selectRouteGuidance', [1,127,37], '/api/select-route-guidance', {sequence:1,lon:127,lat:37}],
    ['selectRouteHistory', ['test'], '/api/select-route-history', {history_id:'test'}],
    ['loadRouteHistory', ['test'], '/api/load-route-history', {history_id:'test'}],
    ['deleteRouteHistory', ['test'], '/api/delete-route-history', {history_id:'test'}],
    ['exportRouteHistory', ['test'], '/api/export-route-history', {history_id:'test'}],
    ['refreshRouteHistory', [], '/api/refresh-route-history', {}],
    ['requestLocalSearch', ['test','예시'], '/api/request-local-search', {request_id:'test',query:'예시'}],
    ['requestRoute', [127,37,128,38,'TIME','[]','[]','{}','origin','destination'], '/api/request-route',
      {origin_lon:127,origin_lat:37,destination_lon:128,destination_lat:38,priority:'TIME',
        waypoints_json:'[]',avoid_json:'[]',vehicle_json:'{}',origin_label:'origin',destination_label:'destination'}]
  ];
  for (const [name,args,url,payload] of cases) {
    bridge[name](...args);
    const posted = posts.pop();
    assert.equal(posted.url, url);
    assert.deepEqual(posted.payload, {...payload, _epoch:0});
    assert.equal(posted.headers['Content-Type'], 'application/json');
    assert.equal(posted.headers['X-Bridge-Token'], 'test-token');
  }
  bridge.routeStatusChanged.connect((...args) => signals.push(args));
  state = {epoch:0, accepting:true, center: {sequence:1, lon:127, lat:37}};
  events = {epoch:0, events: [{epoch:0, sequence:1, signal:'routeStatusChanged', args:[true,'test']} ]};
  await intervals[0]();
  await intervals[1]();
  assert.deepEqual(centers, [[127,37]]);
  assert.deepEqual(signals, [[true,'test']]);
  await intervals[0]();
  assert.equal(centers.length, 1, 'unchanged center repeated');
  const resets = [];
  bridge.projectReset.connect(epoch => resets.push(epoch));
  state = {epoch:1, accepting:true};
  await intervals[0]();
  await intervals[1]();
  assert.deepEqual(resets, [1]);
  assert.equal(signals.length, 1, 'old project signals ignored');
  bridge.cancelRoute();
  assert.equal(posts.pop().payload._epoch, 1);
  const replaySignals = [];
  state = {epoch:1, accepting:true, sequence:50};
  events = {epoch:1, events:[{epoch:1, sequence:49, signal:'loadRouteHistoryInput', args:['old']} ]};
  const freshIntervals = [];
  const fresh = vm.createContext({URLSearchParams, window: {location:{hash:'#token=test-token'}},
    document:{documentElement:{classList:{add(){}}}}, console,
    setInterval: callback => freshIntervals.push(callback),
    fetch: async (url, options) => ({ok:true, json:async () => url === '/api/state' ? state : events})});
  vm.runInContext(script, fresh);
  fresh.window.naverExternalBridge.loadRouteHistoryInput.connect(value => replaySignals.push(value));
  await new Promise(setImmediate);
  assert.equal(replaySignals.length, 0, 'new tab replayed old input event');
  events = {epoch:1, gap:true, events:[{epoch:1, sequence:151, signal:'loadRouteHistoryInput', args:['stale']} ]};
  await freshIntervals[1]();
  assert.equal(replaySignals.length, 0, 'gap replayed stale input');
  console.log(`PASS: ${cases.length} external command contracts; state and signal polling`);
})().catch(error => { console.error(error); process.exitCode = 1; });
