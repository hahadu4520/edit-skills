const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{const d=process.argv[2];const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
for(const f of fs.readdirSync(d).filter(x=>x.endsWith('.html'))){await p.goto('file://'+path.join(d,f));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
await p.screenshot({path:path.join(d,f.replace('.html','.png')),omitBackground:true});}await b.close();})();
