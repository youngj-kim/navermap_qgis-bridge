// SPDX-License-Identifier: GPL-2.0-or-later
const fs = require('fs');
const assert = require('assert/strict');
const { chromium } = require('playwright');

(async () => {
  const html = require('./load_viewer.cjs').loadViewer();
  for (const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)) {
    new Function(match[1].replace('__NAVER_APP_KEY_JSON__', '""'));
  }
  const browser = await chromium.launch({ headless: true, ...(process.env.TEST_BROWSER_CHANNEL ? {channel: process.env.TEST_BROWSER_CHANNEL} : {}) });
  try {
    const page = await browser.newPage();
    await page.setContent(html.replace('__NAVER_APP_KEY_JSON__', '""').replace(/<script src="qrc:[^"]*"><\/script>/, ''));
    await page.evaluate(() => {
      // Emulate NAVER setSize writing a fixed pixel size to its own host element.
      window.naver = { maps: { Size: function(w, h) { this.width = w; this.height = h; } } };
      const sdk = (id) => ({
        setSize(size) {
          const surface = document.getElementById(id);
          surface.style.width = `${size.width}px`;
          surface.style.height = `${size.height}px`;
        },
        getCenter: () => ({lat: () => 37, lng: () => 127}),
        setCenter: () => {}
      });
      map = sdk('map-surface');
      roadview = sdk('roadview-surface');
      for (const id of ['map-surface','roadview-surface']) {
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:absolute;inset:0;z-index:999999;background:#eee';
        document.getElementById(id).appendChild(overlay);
      }
    });
    let count = 0;
    for (const layout of ['map-top', 'roadview-top', 'map-left', 'roadview-left']) {
      for (const viewport of [{width:700,height:900},{width:1350,height:1080},{width:960,height:900},{width:1500,height:950}]) {
        await page.setViewportSize(viewport);
        for (const ratio of [30,50,70]) {
          await page.evaluate(({layout,ratio}) => { applyViewerLayout(layout); applyViewerSplit(ratio); }, {layout,ratio});
          await page.waitForTimeout(650);
          const result = await page.evaluate(() => {
            const rect = id => { const r=document.getElementById(id).getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}; };
            return { map:rect('map'), roadview:rect('roadview'), mapSurface:rect('map-surface'), roadSurface:rect('roadview-surface'), viewer:rect('viewer'), footer:rect('status-bar') };
          });
          for (const [pane,surface] of [[result.map,result.mapSurface],[result.roadview,result.roadSurface]]) {
            assert.ok(Math.abs(pane.width-surface.width)<1 && Math.abs(pane.height-surface.height)<1, JSON.stringify({layout,viewport,ratio,result}));
            assert.ok(pane.height>0 && pane.width>0);
            assert.ok(pane.bottom<=result.footer.y+1, 'pane overlaps footer');
          }
          assert.ok(result.footer.bottom<=result.viewer.bottom+1, 'footer clipped');
          const dateVisible = await page.evaluate(() => {
            const label = document.getElementById('roadview-photo-date');
            const r = label.getBoundingClientRect();
            const pane = document.getElementById('roadview').getBoundingClientRect();
            label.style.pointerEvents = 'auto';
            const onTop = document.elementFromPoint(r.x+r.width/2,r.y+r.height/2) === label;
            label.style.pointerEvents = '';
            return onTop && r.x >= pane.x && r.y >= pane.y && r.right <= pane.right && r.bottom <= pane.bottom;
          });
          assert.ok(dateVisible, `date label clipped or obscured: ${layout} ${ratio}`);
          const buttonVisible = await page.evaluate(() => {
            const button=document.getElementById('split-toggle');
            const r=button.getBoundingClientRect();
            return [[0.5,0.5],[0.15,0.5],[0.85,0.5],[0.5,0.15],[0.5,0.85]].every(([x,y])=>button.contains(document.elementFromPoint(r.x+r.width*x,r.y+r.height*y)));
          });
          assert.ok(buttonVisible, `toggle obscured: ${layout} ${JSON.stringify(viewport)} ${ratio}`);
          const before = await page.locator('#viewer-layout').inputValue();
          await page.locator('#split-toggle').click();
          const after = await page.locator('#viewer-layout').inputValue();
          assert.notEqual(after,before,'toggle did not swap layout');
          count++;
        }
      }
    }
    // Toolbar and route actions stay on one row even in narrow floating docks.
    for (const width of [280,360,540,700,1100]) {
      await page.setViewportSize({width,height:900});
      for (const collapsed of [true,false]) {
        await page.evaluate(value => {
          document.getElementById('explorer-body').hidden=value;
          document.getElementById('explorer-toggle').textContent=value?'탐색창 펼치기 ▾':'탐색창 접기 ▴';
        }, collapsed);
        const sameRow=await page.evaluate(()=>{
          const toolbar=document.getElementById('viewer-toolbar').getBoundingClientRect();
          const controls=['explorer-toggle','viewer-layout','map-language-toggle','fullscreen-toggle'].map(id=>document.getElementById(id).getBoundingClientRect());
          return controls.every(r=>Math.abs(r.y-controls[0].y)<1 && r.width>0 && r.x>=toolbar.x-1 && r.right<=toolbar.right+1);
        });
        assert.ok(sameRow, `toolbar wrapped or overflowed at ${width}px, collapsed=${collapsed}`);
        if (!collapsed) {
          const actionsFit = await page.evaluate(() => {
            const container = document.getElementById('route-actions').getBoundingClientRect();
            const buttons = Array.from(document.querySelectorAll('#route-actions button')).map(button=>button.getBoundingClientRect());
            return buttons.length === 5 && buttons.every(rect =>
              Math.abs(rect.y-buttons[0].y)<1 && rect.width>0 && rect.x>=container.x-1 && rect.right<=container.right+1);
          });
          assert.ok(actionsFit, `route actions wrapped or overflowed at ${width}px`);
        }
      }
    }
    await page.setViewportSize({width:1500,height:950});
    await page.evaluate(()=>{document.getElementById('explorer-body').hidden=false;});
    await page.click('#explorer-toggle');
    for (const layout of ['map-top','roadview-top','map-left','roadview-left']) {
      await page.selectOption('#viewer-layout',layout);
      await page.waitForTimeout(650);
      assert.equal(await page.isVisible('#viewer-layout'),true);
      assert.equal(await page.isVisible('#search-form'),false);
      const fits=await page.evaluate(()=>['map','roadview'].every(id=>{
        const pane=document.getElementById(id), surface=document.getElementById(id+'-surface');
        return pane.clientHeight>0 && Math.abs(pane.clientHeight-surface.clientHeight)<1 && Math.abs(pane.clientWidth-surface.clientWidth)<1;
      }));
      assert.ok(fits, 'collapsed explorer layout failed: '+layout);
    }
    await page.click('#explorer-toggle');
    // Header growth changes the space left for both panes without resizing the window.
    await page.evaluate(() => { document.getElementById('route-controls').style.paddingBottom='120px'; });
    await page.waitForTimeout(650);
    const filled = await page.evaluate(() => ['map','roadview'].every(id => Math.abs(document.getElementById(id).clientHeight-document.getElementById(`${id}-surface`).clientHeight)<1));
    assert.ok(filled, 'SDK resize missed header growth');
    console.log(`PASS: ${count} layout/viewport/split cases; 10 narrow/expanded toolbar cases; collapsed layout; header growth; inline JS syntax`);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode=1; });
