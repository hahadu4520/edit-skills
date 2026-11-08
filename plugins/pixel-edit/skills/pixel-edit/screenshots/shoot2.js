const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({deviceScaleFactor:2,viewport:{width:492,height:300}});const meta={};
for(const n of ['c2b','c3b','c5c','c6b']){await p.goto('file://'+process.cwd()+'/'+n+'.html');await p.waitForTimeout(400);
 meta[n]=await p.$$eval('mark',ms=>ms.map(m=>({k:+m.dataset.k,r:[...m.getClientRects()].map(r=>[r.left*2,r.top*2,r.right*2,r.bottom*2])})));
 await p.screenshot({path:'./'+n+'.png',fullPage:true});}
fs.writeFileSync('./meta.json',JSON.stringify(meta));await b.close();})();
