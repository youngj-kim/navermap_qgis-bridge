// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');

(async () => {
  const script = fs.readFileSync(path.join(__dirname, '../../navermap_qgis_bridge/web/js/external_transport.js'), 'utf8');
  const posts = [], intervals = [], centers = [], signals = [];
  let state = {}, events = {events: []};
  const context = vm.createContext({
    window: {centerNaverMap: (...args) => centers.push(args), open() {}},
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
    ['updateRoadviewState', [127,37,1,2,3,'test'], '/api/roadview-state', {lon:127,lat:37,pan:1,tilt:2,zoom:3,pano_id:'test'}],
    ['setRoutePoint', ['origin',127,37], '/api/route-point', {role:'origin',lon:127,lat:37}],
    ['clearRoutePoint', ['origin'], '/api/clear-route-point', {role:'origin'}],
    ['clearRoutePoints', [], '/api/clear-route-points', {}],
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
    assert.deepEqual(posted.payload, payload);
    assert.equal(posted.headers['Content-Type'], 'application/json');
  }
  bridge.routeStatusChanged.connect((...args) => signals.push(args));
  state = {center: {sequence:1, lon:127, lat:37}};
  events = {events: [{sequence:1, signal:'routeStatusChanged', args:[true,'test']} ]};
  await intervals[0]();
  await intervals[1]();
  assert.deepEqual(centers, [[127,37]]);
  assert.deepEqual(signals, [[true,'test']]);
  await intervals[0]();
  assert.equal(centers.length, 1, 'unchanged center repeated');
  console.log(`PASS: ${cases.length} external command contracts; state and signal polling`);
})().catch(error => { console.error(error); process.exitCode = 1; });
