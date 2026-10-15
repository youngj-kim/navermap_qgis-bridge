// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const read = file => fs.readFileSync(path.join(__dirname, '../../navermap_qgis_bridge/web/js/', file), 'utf8');
const zooms = [], moves = [], markers = [], panos = [];
let zoom = 16, center = {lng:()=>127,lat:()=>37};
const context = vm.createContext({
  mapViewSnapshot: {lon:127,lat:37,zoom:16}, mapDragActive:false, moveRequestId:0, qgisBridge:{
    zoomQgisView:(...args)=>zooms.push(args),moveQgisCenter:(...args)=>{assert.equal(args.length,2);moves.push(args);}},
  marker:{setPosition:p=>markers.push(p)}, roadview:{getPanoId:()=>1,setPosition:p=>panos.push(p)},
  isBridgeSyncSuppressed:()=>false, suppressBridgeSync(){}, setStatus(){},
  window:{setReverseSyncDiagnostic(){}}, Number, Math,
  naver:{maps:{Point:class {constructor(x,y){this.x=x;this.y=y;}},
    LatLng:class {constructor(lat,lon){this.lat=()=>lat;this.lng=()=>lon;}}}},
  map:{getCenter:()=>center,setCenter:value=>center=value,getZoom:()=>zoom,
       setZoom:value=>zoom=value, getOptions:key=>key==='minZoom'?0:21,
       getProjection:()=>({fromCoordToOffset:()=>({x:0,y:0}),fromOffsetToCoord:p=>p,
                          getDistance:()=>128*2**(17-zoom)})}
});
vm.runInContext(read('sync.js'), context);
vm.runInContext(read('navigation.js').split('    window.loadRouteHistoryInput')[0], context);
zoom = 17;
context.syncNaverMapToQgis();
assert.deepEqual(zooms, [[127,37,1]]);
assert.equal(markers.length, 0);
context.syncNaverMapToQgis();
assert.equal(zooms.length, 1, 'idle must not repeat or move panorama marker');
assert.equal(moves.length, 0);
context.window.syncNaverView(127.1,37.1,4,true);
assert.equal(zoom, 15);
assert.equal(markers.length, 0);
assert.equal(panos.length, 0, 'scale-only updates must preserve panorama position');
context.window.syncNaverView(127.2,37.2,2,false);
assert.equal(zoom, 16);
assert.equal(panos.length, 1, 'normal center movement should still move panorama');
assert.equal(markers.length, 1);
context.window.syncNaverView(200,37,2,false);
assert.equal(panos.length, 1, 'invalid coordinates must be ignored');
// Intermediate drag moves QGIS, then its final position must also move the panorama.
context.mapDragActive = true;
center = {lng:()=>127.3,lat:()=>37.3};
context.syncNaverMapToQgis();
assert.deepEqual(moves.at(-1), [127.3,37.3]);
assert.equal(panos.length, 1, 'do not request a panorama on every intermediate drag');
context.mapDragActive = false;
context.syncNaverMapToQgis(true,true);
assert.deepEqual(moves.at(-1), [127.3,37.3]);
assert.equal(panos.length, 2, 'drag end must move panorama even if intermediate snapshot matches');
const moveCount=moves.length;
context.syncNaverMapToQgis();
assert.equal(moves.length,moveCount,'settled idle must not echo movement');
// An unsuccessful bridge invocation must remain retryable at the same coordinate.
center = {lng:()=>127.4,lat:()=>37.4};
const deliver = context.qgisBridge.moveQgisCenter;
context.qgisBridge.moveQgisCenter=()=>{throw new Error('temporary bridge failure');};
context.syncNaverMapToQgis(true);
context.qgisBridge.moveQgisCenter=deliver;
context.syncNaverMapToQgis(true);
assert.deepEqual(moves.at(-1),[127.4,37.4]);
assert.equal(panos.length,3);
console.log('PASS: zoom preservation, map drag -> QGIS/panorama, drag-end final delivery, failed-call retry and idle deduplication');
