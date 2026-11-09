const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));const eo=x=>1-Math.pow(1-x,3);const prog=(t,t0,d)=>clamp((t-t0)/d);const $=id=>document.getElementById(id);
function rise(el,t,t0,d=0.5,dy=36){const e=eo(prog(t,t0,d));el.style.opacity=e;el.style.transform=`translateY(${(1-e)*dy}px)`;el.style.filter=`blur(${(1-e)*10}px)`;}
function wipe(el,t,t0,d=0.4){const e=eo(prog(t,t0,d));el.style.clipPath=`inset(0 ${(1-e)*100}% 0 0 round 14px)`;}
function grow(el,t,t0,d=0.45){const e=eo(prog(t,t0,d));el.style.transform=`scaleX(${e})`;}
function dim(el,t,t0,to=0.25,d=0.4){const e=eo(prog(t,t0,d));el.style.opacity=1-(1-to)*e;}
