import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE);
const browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
const out='../../outputs/ai-hubs-check';await fs.mkdir(out,{recursive:true});
async function go(path){const r=await page.goto('http://127.0.0.1:3000'+path,{waitUntil:'networkidle'});assert.equal(r.status(),200,path);await page.locator('[data-app-ready="true"]').waitFor();}
for(const width of [1440,390]){
 await page.setViewportSize({width,height:950});await go('/');
 const cards=page.locator('main section').filter({has:page.getByRole('heading',{name:'Explore',exact:true})}).locator('a').filter({has:page.locator('h3')});
 assert.deepEqual((await cards.locator('h3').allTextContents()).slice(0,4),['ChatGPT / Codex','Claude / Claude Code','Data Structures & Algorithms','Web Development']);
 const a=await cards.nth(0).boundingBox(),b=await cards.nth(1).boundingBox(),c=await cards.nth(2).boundingBox();assert.ok(a.y<c.y && b.y<c.y);if(width===1440){assert.equal(a.y,b.y);assert.ok(a.width>500)}
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false);
 await page.screenshot({path:`${out}/home-${width}.png`,fullPage:true});
 await cards.nth(0).click();await page.getByRole('heading',{name:'ChatGPT / Codex',exact:true}).waitFor();
 await go('/ai-tools/claude-claude-code');await page.getByRole('heading',{name:'Claude / Claude Code',exact:true}).waitFor();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false);await page.screenshot({path:`${out}/claude-hub-${width}.png`,fullPage:true});
}
for(const slug of ['chatgpt-codex','claude-claude-code'])for(const leaf of ['getting-started','prompting-workflows','coding-review-checklist']){await go('/ai-tools/'+slug+'/'+leaf);assert.equal(await page.locator('h1').count(),1);assert.ok((await page.locator('main').innerText()).includes('Official')||(await page.locator('main').innerText()).includes('official'))}
await go('/search?q=Codex');assert.ok(await page.locator('main a[href="/ai-tools/chatgpt-codex"]').count());
assert.deepEqual(errors,[]);console.log('AI cards order, sizing, both hubs, six guides, search and mobile layout passed.');await fs.writeFile(`${out}/report.json`,JSON.stringify({featuredCards:2,hubs:2,guides:6,widths:[1440,390],search:true,browserErrors:errors},null,2));await browser.close();
