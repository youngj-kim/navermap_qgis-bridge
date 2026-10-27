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
      qgisBridge = {importRouteHistory:()=>calls.push('import'),
        deleteRouteHistories:ids=>calls.push(JSON.parse(ids)), selectRouteHistory:id=>calls.push(id)};
      window.histories = ['a','b','c'].map(history_id=>({history_id, origin_name:'A', destination_name:'B', guidance_count:1}));
      renderRouteHistory({items:histories});
      activateRoutePanelTab('history');
    });
    await page.click('.history-import');
    assert.deepEqual(await page.evaluate(()=>calls), ['import']);
    assert.equal(await page.isDisabled('.history-delete-selected'), true);
    await page.locator('.history-select').nth(0).check();
    assert.equal(await page.locator('.history-select-all').evaluate(el=>el.indeterminate), true);
    assert.deepEqual(await page.evaluate(()=>calls), ['import'], 'checkbox must not focus route');
    await page.locator('.history-select').nth(1).focus();
    await page.keyboard.press('Space');
    await page.click('.history-delete-selected');
    assert.deepEqual(await page.evaluate(()=>calls.at(-1)), ['a','b']);
    await page.evaluate(()=>renderRouteHistory({items:histories}));
    assert.equal(await page.locator('.history-select:checked').count(), 2, 'selection retained after refresh');
    await page.check('.history-select-all');
    assert.equal(await page.locator('.history-select:checked').count(), 3);
    await page.uncheck('.history-select-all');
    assert.equal(await page.isDisabled('.history-delete-selected'), true);
    await page.check('.history-select-all');
    await page.evaluate(()=>renderRouteHistory({items:histories.slice(2)}));
    assert.equal(await page.locator('.history-select:checked').count(), 1, 'removed IDs pruned');
    await page.evaluate(()=>{routeBusy=true;updateRouteControls();});
    for(const selector of ['.history-import','.history-delete-selected','.history-select-all','.history-select'])
      assert.equal(await page.isDisabled(selector), true);
    await page.evaluate(()=>{routeBusy=false;updateRouteControls();renderRouteHistory({items:[]});});
    assert.equal(await page.isVisible('.history-import'), true, 'import accessible without history');
    assert.equal(await page.isDisabled('.history-delete-selected'), true);
    assert.equal(await page.locator('.history-select').count(), 0);
    for(const width of [280,360,1100]) {
      await page.setViewportSize({width,height:800});
      const fits = await page.locator('.history-toolbar').evaluate(el=>el.scrollWidth <= el.clientWidth);
      assert.equal(fits,true, `toolbar fits ${width}`);
    }
    await page.evaluate(()=>{mapLanguage='en';renderRouteHistory({items:histories});});
    assert.equal(await page.locator('.history-import').textContent(), 'Import files');
    assert.equal(await page.locator('.history-delete-selected').textContent(), 'Delete selected (0)');
    await page.evaluate(()=>{mapLanguage='ko';renderRouteHistory({items:histories});});
    if (process.env.HISTORY_SCREENSHOT) await page.locator('#route-guidance-panel').screenshot({path:process.env.HISTORY_SCREENSHOT});
    console.log('PASS history import, multi-selection/delete, keyboard, refresh/reset, busy and narrow toolbar');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
