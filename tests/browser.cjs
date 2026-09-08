// Local-only UI checks. All non-local network requests are intercepted.
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=path.resolve(__dirname,'..');
const data=JSON.parse(fs.readFileSync(path.join(root,'skills.json'),'utf8'));
const out=path.join(root,'.test-output');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
  const pathname=new URL(req.url,'http://localhost').pathname;
  const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
  try {res.setHeader('Content-Type',file.endsWith('.json')?'application/json':'text/html; charset=utf-8');res.end(fs.readFileSync(file));}
  catch {res.writeHead(404);res.end();}
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const base='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',route=>{
      if(route.request().url().startsWith(base)) return route.continue();
      if(route.request().method()==='POST') return route.fulfill({status:202,contentType:'application/json',body:JSON.stringify({ok:true,state:'received',issue:'https://github.com/Coingyy/skillshare/issues/999'})});
      return route.fulfill({status:200,body:''});
    });
    await page.goto(base);await page.waitForSelector('.card');
    assert.equal(await page.locator('.card').count(),data.skills.length);
    // Exercise all independent category/platform/type combinations via real DOM events.
    const combinations=await page.evaluate(skills=>{
      const categories=[...document.querySelectorAll('[data-cat]')].map(b=>b.dataset.cat);
      const platforms=[...document.querySelectorAll('[data-platform]')].map(b=>b.dataset.platform);
      const types=[...document.querySelector('#type-filter').options].map(o=>o.value);
      let count=0;
      for(const c of categories) for(const p of platforms) for(const t of types) {
        document.querySelector(`[data-cat="${c}"]`).click();document.querySelector(`[data-platform="${p}"]`).click();
        const select=document.querySelector('#type-filter');select.value=t;select.dispatchEvent(new Event('change'));
        const actual=[...document.querySelectorAll('.card')].map(c=>c.id.slice(9)).sort();
        const expected=skills.filter(s=>(c==='all'||s.category===c)&&(p==='all'||s.platforms[p].status!=='unverified')&&(t==='all'||s.type===t)).map(s=>s.id).sort();
        if(JSON.stringify(actual)!==JSON.stringify(expected)) throw new Error('Filter mismatch '+[c,p,t]);
        count++;
      }
      document.querySelector('#reset-filters').click();return count;
    },data.skills);
    await page.getByRole('button',{name:'ChatGPT',exact:true}).click();
    assert.equal(await page.locator('.card').count(),data.skills.filter(s=>s.platforms.chatgpt.status!=='unverified').length);
    await page.locator('#include-unverified').check();assert.equal(await page.locator('.card').count(),data.skills.length);
    await page.locator('#reset-filters').click();
    await page.locator('#catalog-search').fill('a-term-no-offering-matches');assert.equal(await page.locator('.card').count(),0);
    assert.match(await page.locator('#grid').innerText(),/No matches/);
    await page.locator('#catalog-search').fill('superpowers');assert.equal(await page.locator('.card').count(),1);
    await page.locator('#reset-filters').click();
    assert.equal(await page.locator('a[href="#"]:not(.logo)').count(),0);
    const links=await page.locator('#grid a').evaluateAll(nodes=>nodes.map(n=>n.href));
    assert.ok(links.every(link=>link.startsWith('https://')));
    await page.screenshot({path:path.join(out,'desktop.png')});
    await page.locator('#catalog-search').fill('Playwright MCP');
    await page.locator('.setup-details summary').first().click();
    await page.locator('#catalog').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(out,'desktop-setup.png')});
    // Form is mocked; no actual issue is opened.
    await page.locator('#in-url').fill('https://github.com/example/test-submission');
    await page.locator('#submit-btn').click();
    await page.waitForFunction(()=>document.querySelector('#submission-status').textContent.includes('Submission received'));
    assert.ok(!(await page.locator('#submission-status').innerText()).includes('Published in this catalog'));
    await page.reload();await page.waitForSelector('.card');
    assert.match(await page.locator('#submission-status').innerText(),/publication is not confirmed/);
    await page.locator('#reset-filters').click();
    for(const width of [390,320]) {
      await page.setViewportSize({width,height:844});await page.evaluate(()=>scrollTo(0,0));
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Overflow at '+width);
      await page.screenshot({path:path.join(out,'mobile-'+width+'.png')});
      await page.locator('#catalog-search').fill('Playwright MCP');
      await page.locator('.setup-details summary').first().click();await page.locator('#catalog').scrollIntoViewIfNeeded();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Expanded overflow at '+width);
      await page.screenshot({path:path.join(out,'mobile-setup-'+width+'.png')});
      await page.locator('#reset-filters').click();
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify({combinations,entries:data.skills.length,viewports:[1440,390,320],consoleErrors:errors,mockedSubmission:true,checkedLinks:links.length},null,2));
    console.log('Browser checks passed:',combinations,'filter combinations;',links.length,'HTTPS links; desktop and mobile; mocked submission.');
  } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
