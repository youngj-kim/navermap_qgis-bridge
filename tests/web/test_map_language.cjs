// SPDX-License-Identifier: GPL-2.0-or-later
const assert = require('assert/strict');
const {chromium} = require('playwright');
const {loadViewer} = require('./load_viewer.cjs');
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.TEST_BROWSER_CHANNEL ? {channel:process.env.TEST_BROWSER_CHANNEL} : {})});
  try {
    const page = await browser.newPage();
    await page.route('http://viewer.test/**', route => route.fulfill({contentType:'text/html', body:loadViewer().replace(/<script src="qrc:[^"]*"><\/script>/, '')}));
    async function setup() {
      await page.evaluate(() => {
        window.reloads = 0;
        class LatLng {constructor(lat, lon){this.y=lat;this.x=lon;} lat(){return this.y;} lng(){return this.x;}}
        window.naver = {maps:{LatLng, MapTypeId:{NORMAL:'NORMAL', HYBRID:'HYBRID', SATELLITE:'SATELLITE'},
          LatLngBounds:class {extend(){}}, Polyline:class {setMap(){}},
          StreetLayer:class {setMap(){}}}};
        let center = new LatLng(37,127), zoom=14, position=center;
        map = {getCenter:()=>center, setCenter:value=>{center=value;}, getZoom:()=>zoom,
          setZoom:value=>{zoom=value;},setMapTypeId(){},fitBounds(){}};
        marker = {getPosition:()=>position,setPosition:value=>{position=value;}};
        let roadPosition = new LatLng(36,126), pov={pan:45,tilt:5,fov:90};
        roadview = {getLocation:()=>({coord:roadPosition}),getPov:()=>pov,
          setPosition:value=>{roadPosition=value;},setPov:value=>{pov=value;}};
        qgisBridge = {reloadViewer(){window.reloads++;}};
        viewerOptions.initialize();
        initializeMapLanguageButton();
      });
    }
    await page.goto('http://viewer.test/');
    assert.equal(await page.evaluate(()=>mapLanguage), 'ko', 'fresh viewer defaults to Korean');
    await setup();
    await page.evaluate(() => {
      routeOrigin = {lon:127,lat:37}; routeOriginInput.value='출발지';
      addWaypoint(); routeWaypoints[0].input.value='경유지'; routeWaypoints[0].coordinate={lon:128,lat:38};
      displayedRoutePayload={path:[{lon:127,lat:37},{lon:128,lat:38}],guides:[],summary:{}};
    });
    await page.selectOption('#map-type','HYBRID');
    await page.click('#street-toggle');
    await page.click('#explorer-toggle');
    assert.equal(await page.isVisible('#map-language-toggle'),true);
    await page.click('#map-language-toggle');
    assert.equal(await page.evaluate(()=>reloads),1);
    assert.equal(await page.evaluate(()=>JSON.parse(sessionStorage.getItem(mapLanguageStateKey)).language),'en');
    await page.reload();
    await setup();
    await page.evaluate(()=>restoreMapLanguageState());
    assert.equal(await page.locator('#map-language-toggle').textContent(),'KR');
    assert.equal(await page.evaluate(()=>mapLanguage),'en');
    assert.equal(await page.locator('html').getAttribute('lang'),'en');
    assert.equal(await page.locator('#search-submit').textContent(),'Search');
    assert.equal(await page.locator('#route-create').textContent(),'Get route');
    assert.equal(await page.locator('#route-origin-input').getAttribute('placeholder'),'Place, address or lon,lat');
    assert.equal(await page.locator('#route-reset').getAttribute('aria-label'),'Reset route inputs');
    assert.equal(await page.locator('#viewer-layout option[value="map-top"]').textContent(),'Map above / Street View below');
    assert.equal(await page.locator('#street-toggle').textContent(),'Hide coverage');
    assert.equal(await page.evaluate(()=>routeWaypoints[0].label.textContent),'Stop 1');
    const untranslated = await page.evaluate(() => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      const texts=[];
      while(walker.nextNode()) {
        const node=walker.currentNode;
        if (!node.parentElement.closest('script,style') && /[가-힣]/.test(node.textContent)) texts.push(node.textContent);
      }
      return texts;
    });
    assert.deepEqual(untranslated,[], 'Application labels must all be translated');
    await page.evaluate(() => {
      window.tbtOriginal = "창훈사거리에서 '장안구청, 경기도교육청조원청사' 방면으로 우회전";
      window.tbtPayload = {path:[],summary:{},guides:[{sequence:1,guide_type:3,
        guidance:tbtOriginal,longitude:127,latitude:37}]};
      renderRouteGuidance(tbtPayload);
      qgisBridge.selectRouteGuidance = () => {};
    });
    const englishTbt = "Turn right at 창훈사거리 towards '장안구청, 경기도교육청조원청사'";
    assert.equal(await page.locator('.guidance-title').textContent(), englishTbt);
    assert.equal(await page.locator('.guidance-title').getAttribute('title'), await page.evaluate(()=>tbtOriginal));
    await page.click('.guidance-item');
    assert.equal(await page.locator('#status').textContent(), `1. ${englishTbt}`);
    await page.evaluate(()=>roadview.setPosition(new naver.maps.LatLng(36,126)));
    assert.equal(await page.evaluate(()=>tbtPayload.guides[0].guidance), await page.evaluate(()=>tbtOriginal));
    const cases = [
      ['우회전','Turn right'], ["'광교산로' 방면으로 좌회전", "Turn left towards '광교산로'"],
      ['비보호 좌회전','Make an unprotected left turn'], ['유턴','Make a U-turn'],
      ['회전교차로에서 3시 방향','Head at 3 o\'clock at the roundabout'],
      ['로터리에서 직진','Continue straight at the roundabout'],
      ['회전 교차로에서 왼쪽 9시 방향',"Turn left at 9 o'clock at the roundabout"],
      ['로터리에서 오른쪽 1시 방향',"Turn right at 1 o'clock at the roundabout"],
      ['직진 방향','Continue straight'],
      ['오른쪽 고속도로 진입','Enter the expressway on the right'],
      ['왼쪽 지하차도 옆길 진입','Enter the side road beside the underpass on the left'],
      ['전방 도시고속도로 진출','Exit the urban expressway ahead'],
      ["미사교차로에서 '팔당대교, 하남시청, 양평' 방면으로 오른쪽 고속도로 출구",
        "Exit the expressway on the right at 미사교차로 towards '팔당대교, 하남시청, 양평'"],
      ['오른쪽 고속도로 입구','Enter the expressway on the right'],
      ['왼쪽 도시고속도로 출구','Exit the urban expressway on the left'],
      ['전방 자동차전용도로 출구','Exit the motorway ahead'],
      ['지하차도 오른쪽 옆길','Take the side road on the right beside the underpass'],
      ["미사사거리에서 '미사강변도시' 방면으로 지하차도 오른쪽 옆길",
        "Take the side road on the right beside the underpass at 미사사거리 towards '미사강변도시'"],
      ['고가차도 왼쪽 옆길 진입','Take the side road on the left beside the overpass'],
      ['오른쪽 옆길','Take the side road on the right'],
      ['하이패스 전용 톨게이트 통과','Pass through the Hi-pass-only tollgate'],
      ['직진 후 우회전','Continue straight, then turn right'],
      ['목적지 도착','Arrive at the destination'], ['경유지','Waypoint'],
      ['Unknown instruction','Unknown instruction'], ['새로운 안내 형식','새로운 안내 형식'],
      ["'우회전로' 방면으로 직진", "Continue straight towards '우회전로'"]
    ];
    for (const [guidance,expected] of cases) {
      assert.equal(await page.evaluate(guidance=>localizedGuidance({guidance}),guidance),expected);
    }
    // Preserve the pre-existing route/state assertions below; restore the TBT
    // payload before the actual English -> Korean browser reload at the end.
    await page.evaluate(()=>{displayedRoutePayload={path:[{lon:127,lat:37},{lon:128,lat:38}],guides:[],summary:{}};});
    await page.evaluate(() => {
      updateRoadviewPhotoDate();
      renderSearchResults([{title:'서울역',address:'서울특별시',lon:127,lat:37}]);
    });
    assert.equal(await page.locator('#roadview-photo-date').textContent(),'Capture date unavailable');
    assert.equal(await page.locator('.search-result-title').textContent(),'서울역');
    assert.equal(await page.locator('.search-result-address').textContent(),'서울특별시');
    assert.equal(await page.evaluate(()=>formatGuidanceDuration(120)),'2 min');
    assert.equal(await page.evaluate(()=>translateViewerStatus('실시간 최적 경로 생성 완료: 2.0 km, 예상 4분, 경유지 1개, 차량: 소형/휘발유')),
      'Real-time optimal route ready: 2.0 km, estimated 4 min, stops: 1, vehicle: Small/Gasoline');
    assert.equal(await page.evaluate(()=>uiText`위치를 찾지 못했습니다: ${'서울역 {0}'}`),'Location not found: 서울역 {0}');
    for (const width of [280,360,500,1100]) {
      await page.setViewportSize({width,height:950});
      await page.evaluate(()=>{document.getElementById('explorer-body').hidden=false;});
      const fits = await page.evaluate(() => {
        const container=document.getElementById('route-actions').getBoundingClientRect();
        const buttons=Array.from(document.querySelectorAll('#route-actions button')).map(element=>element.getBoundingClientRect());
        return buttons.every(rect=>Math.abs(rect.y-buttons[0].y)<1 && rect.right<=container.right+1);
      });
      assert.ok(fits, `English route buttons overflow at ${width}px`);
    }
    assert.deepEqual(await page.evaluate(()=>[map.getCenter().lat(),map.getCenter().lng(),map.getZoom()]),[37,127,14]);
    assert.equal(await page.inputValue('#route-origin-input'),'출발지');
    assert.equal(await page.evaluate(()=>routeWaypoints[0].input.value),'경유지');
    assert.equal(await page.evaluate(()=>displayedRoutePayload.path.length),2);
    assert.deepEqual(await page.evaluate(()=>roadview.getPov()),{pan:45,tilt:5,fov:90});
    assert.equal(await page.evaluate(()=>currentRoadviewCoordinate().lat()),36);
    assert.equal(await page.locator('#street-toggle').getAttribute('aria-pressed'),'true');
    assert.equal(await page.evaluate(()=>sessionStorage.getItem(mapLanguageStateKey)),null);
    await page.evaluate(()=>{routeBusy=true;});
    await page.click('#map-language-toggle');
    assert.equal(await page.evaluate(()=>reloads),0);
    assert.equal(await page.locator('#status').textContent(),'Wait for the search to finish before switching languages.');
    await page.evaluate(()=>{routeBusy=false;});
    await page.click('#map-language-toggle');
    assert.equal(await page.evaluate(()=>JSON.parse(sessionStorage.getItem(mapLanguageStateKey)).language),'ko');
    // Inspect the actual SDK loader URL without contacting NAVER or using a key.
    const sdk = await page.evaluate(() => {
      delete window.naver;
      const append = document.head.appendChild.bind(document.head);
      let src;
      document.head.appendChild = element => {src=element.src; return element;};
      loadNaverScript('PLACEHOLDER');
      document.head.appendChild = append;
      return src;
    });
    assert.equal(new URL(sdk).searchParams.get('language'),'en');
    assert.equal(new URL(sdk).searchParams.get('submodules'),'panorama,geocoder');
    await setup();
    await page.evaluate(()=>{window.naverExternalBridge={};renderRouteGuidance(tbtPayload);});
    await Promise.all([page.waitForNavigation(), page.click('#map-language-toggle')]);
    await setup();
    await page.evaluate(()=>restoreMapLanguageState());
    assert.equal(await page.evaluate(()=>mapLanguage),'ko');
    assert.equal(await page.locator('#map-language-toggle').textContent(),'EN');
    assert.equal(await page.locator('#search-submit').textContent(),'검색');
    assert.equal(await page.locator('.guidance-title').textContent(), "창훈사거리에서 '장안구청, 경기도교육청조원청사' 방면으로 우회전");
    assert.equal(page.url(),'http://viewer.test/');
    async function captureRouteLanguage() {
      return page.evaluate(async () => {
        let options;
        qgisBridge.setRoutePoint = () => {};
        qgisBridge.requestRoute = (...args) => {options = JSON.parse(args[7]);};
        routeOrigin = {lon:127,lat:37}; routeDestination = {lon:128,lat:38};
        routeOriginInput.value = '127,37'; routeDestinationInput.value = '128,38';
        updateRouteControls();
        routeCreateButton.click();
        await new Promise(resolve => setTimeout(resolve, 0));
        routeBusy = false; window.clearTimeout(routeWatchdog); updateRouteControls();
        return options.language;
      });
    }
    assert.equal(await captureRouteLanguage(), 'ko', 'Korean UI must request Korean route instructions');
    await page.evaluate(()=>{window.naverExternalBridge={};});
    await Promise.all([page.waitForNavigation(), page.click('#map-language-toggle')]);
    await setup();
    await page.evaluate(()=>restoreMapLanguageState());
    assert.equal(await captureRouteLanguage(), 'en', 'English UI must request English route instructions');
    await page.evaluate(()=>renderRouteGuidance({path:[],summary:{},guides:[{
      sequence:1,guidance:"Turn right towards 'Namdaemun-ro 7-gil'",longitude:127,latitude:37}]}));
    assert.equal(await page.locator('.guidance-title').textContent(), "Turn right towards 'Namdaemun-ro 7-gil'");
    console.log('PASS: language toggle, native reload, state restoration, busy guard and SDK language');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
