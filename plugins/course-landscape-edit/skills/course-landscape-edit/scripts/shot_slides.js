const {chromium}=require('playwright');const path=require('path');
(async()=>{const [,,dir,out,...names]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
for(const n of names){await p.goto('file://'+path.resolve(dir,n+'.html'));await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
await p.screenshot({path:path.join(out,n+'.jpg'),type:'jpeg',quality:88});}await b.close();})();
