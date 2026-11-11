import { chromium } from '@playwright/test';
import { readFileSync, mkdirSync } from 'node:fs';
const stage = process.argv[2] ?? 'after';
const password = process.env.DEMO_PASSWORD ?? readFileSync('../.env','utf8').match(/^DEMO_PASSWORD=(.+)$/m)?.[1];
const browser = await chromium.launch({channel:'chrome'});
const page = await browser.newPage({viewport:{width:1440,height:900}});
const out = `../docs/evidence/ui/${stage}`; mkdirSync(out,{recursive:true});
await page.goto('http://127.0.0.1:5173');
await page.getByRole('button',{name:'Sign in',exact:true}).waitFor();
await page.screenshot({path:`${out}/login-desktop.png`,fullPage:true});
await page.getByLabel('Password',{exact:true}).fill(password);
await page.getByRole('button',{name:'Sign in',exact:true}).click();
await page.getByLabel('Select portfolio').waitFor();
for (const [name,slug] of [['Overview','overview'],['Integrations','integrations'],['Leases & ledger','leases'],['Reconciliation','reconciliation'],['Billing previews','billing'],['Audit & operations','audit']]) {
 await page.getByRole('button',{name,exact:true}).click(); await page.waitForTimeout(700);
 await page.screenshot({path:`${out}/${slug}-desktop.png`,fullPage:true});
 if(name==='Leases & ledger'){
  await page.getByRole('button',{name:'Ledger',exact:true}).click(); await page.waitForTimeout(500);
  await page.screenshot({path:`${out}/ledger-desktop.png`,fullPage:true});
  await page.locator('tbody tr button').first().click(); await page.getByRole('dialog').waitFor();
  await page.screenshot({path:`${out}/source-modal-desktop.png`,fullPage:true});
  await page.getByRole('button',{name:'Close dialog'}).click();
 }
}
await page.getByRole('button',{name:'Overview',exact:true}).click();
for(const [width,height,label] of [[768,1024,'tablet'],[390,844,'mobile']]){
 await page.setViewportSize({width,height}); await page.waitForTimeout(300);
 await page.screenshot({path:`${out}/overview-${label}.png`,fullPage:true});
}
const identity = await (await page.request.get("/api/auth/me")).json();
await page.request.post("/api/auth/logout", {headers:{"X-CSRF-Token":identity.csrf}});
await browser.close(); console.log(`Captured ${stage} synthetic UI screenshots`);
