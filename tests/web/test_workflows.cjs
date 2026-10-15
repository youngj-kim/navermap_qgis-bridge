// SPDX-License-Identifier: GPL-2.0-or-later
const assert = require('assert/strict');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.TEST_BROWSER_CHANNEL ? {channel:process.env.TEST_BROWSER_CHANNEL} : {})});
  try {
    const page = await browser.newPage();
    await page.setContent(require('./load_viewer.cjs').loadViewer().replace(/<script src="qrc:[^"]*"><\/script>/, ''));
    await page.evaluate(() => {
      window.calls = [];
      window.naver = {maps:{MapTypeId:{NORMAL:'normal',SATELLITE:'satellite',HYBRID:'hybrid'},
        StreetLayer: class {setMap(value){calls.push(value ? 'street-on' : 'street-off');}}}};
      map = {getCenter:()=>({lng:()=>127,lat:()=>37}),setCenter(value){if(value.lng() !== 127 || value.lat() !== 37) calls.push('move');},
             setZoom(){calls.push('zoom');},setMapTypeId(value){calls.push(value);}};
      qgisBridge = {setRoutePoint(){},clearRoutePoint(){},clearRoutePoints(){},
                    requestRoute:()=>calls.push('request'),cancelRoute:()=>calls.push('cancel')};
      updateRouteControls();
      viewerOptions.initialize();
    });
    await page.selectOption('#map-type', 'HYBRID');
    await page.click('#street-toggle');
    await page.click('#street-toggle');
    assert.deepEqual(await page.evaluate(() => calls), ['hybrid','street-on','street-off']);
    await page.evaluate(() => {calls.length = 0; routeOriginInput.value='keep me';
      renderSearchResults([{title:'A',address:'address',lon:127,lat:37}]);});
    assert.equal(await page.locator('#search-results-toggle').count(), 0);
    assert.equal(await page.isVisible('#search-results'), true);
    assert.equal(await page.locator('.search-result').count(), 1);
    await page.click('#explorer-toggle');
    assert.equal(await page.isVisible('#route-origin-input'), false);
    assert.equal(await page.isVisible('#viewer-layout'), true);
    assert.equal(await page.isVisible('#fullscreen-toggle'), true);
    for (const layout of ['map-top','roadview-top','map-left','roadview-left']) {
      await page.selectOption('#viewer-layout', layout);
      assert.equal(await page.evaluate(value => viewer.classList.contains('layout-'+value), layout), true);
      assert.equal(await page.isVisible('#route-origin-input'), false);
    }
    await page.click('#explorer-toggle');
    assert.equal(await page.inputValue('#route-origin-input'), 'keep me');
    await page.click('#route-avoid-toggle');
    await page.check('input[value="toll"]');
    await page.check('input[value="motorway"]');
    assert.equal(await page.isChecked('input[value="toll"]'), false);
    assert.equal(await page.isDisabled('#route-priority'), true);
    assert.equal(await page.isDisabled('#route-car-hipass'), true);
    assert.equal(await page.locator('#route-car-type option[value="7"]').count(), 0);
    await page.evaluate(() => {
      window.pending = [];
      resolveRouteLocation = () => new Promise(resolve => pending.push(resolve));
      routeOriginInput.value = 'A'; routeDestinationInput.value = 'B';
      updateRouteControls();
      routeCreateButton.click();
    });
    assert.equal(await page.isDisabled('#route-cancel'), false);
    await page.click('#route-cancel');
    await page.evaluate(async () => {
      pending.forEach(resolve => resolve({lon:127,lat:37}));
      await Promise.resolve(); await Promise.resolve();
    });
    assert.deepEqual(await page.evaluate(() => calls), ['cancel'], 'cancelled geocoding must not submit a route');
    await page.evaluate(() => {
      routeOrigin = {lon:127,lat:37}; routeDestination = {lon:128,lat:38};
      updateRouteControls(); routeCreateButton.click();
    });
    await page.waitForFunction(() => calls.includes('request'));
    await page.evaluate(() => {
      routeHistory = [{history_id:'retained'}];
      window.resetViewerProject();
    });
    assert.equal(await page.inputValue('#route-origin-input'), '');
    assert.equal(await page.isDisabled('#route-cancel'), true);
    assert.equal(await page.evaluate(() => routeHistory[0].history_id), 'retained');
    await page.clock.install();
    await page.evaluate(async () => {
      routeOriginInput.value='A'; routeDestinationInput.value='B';
      routeOrigin={lon:127,lat:37}; routeDestination={lon:128,lat:38};
      updateRouteControls(); routeCreateButton.click();
      await Promise.resolve();
    });
    await page.clock.fastForward(35000);
    assert.equal(await page.isDisabled('#route-cancel'), true);
    assert.equal(await page.evaluate(() => calls.at(-1)), 'cancel');
    console.log('PASS: map options/panel state, exclusive settings, cancel during geocoding, project reset/history retention, response watchdog');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode=1;});
