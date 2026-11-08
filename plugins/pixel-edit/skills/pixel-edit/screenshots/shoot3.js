const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({deviceScaleFactor:2,viewport:{width:492,height:300}});
for(const n of ['c2b','c3b','c5c','c6b']){await p.goto('file://'+process.cwd()+'/'+n+'.html');await p.waitForTimeout(400);
 for(const h of ['h1','h2']){await p.evaluate(c=>document.body.className=c,h);await p.screenshot({path:`./${n}_${h}.png`,fullPage:true});}}
await b.close();})();
