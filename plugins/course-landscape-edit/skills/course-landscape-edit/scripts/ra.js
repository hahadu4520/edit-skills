const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{const [,,dir,name,dur]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+path.join(dir,name+'.html'));await p.evaluate(()=>document.fonts.ready);for(const t of [1,5,10,20,35]){await p.evaluate(t=>render(t),t);await p.waitForTimeout(120);}await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
const out=path.join(dir,'fr_'+name);fs.mkdirSync(out,{recursive:true});const n=Math.ceil(parseFloat(dur)*30)+2;
for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/30);await p.screenshot({path:path.join(out,String(i).padStart(5,'0')+'.jpg'),type:'jpeg',quality:92});}
await b.close();})();
