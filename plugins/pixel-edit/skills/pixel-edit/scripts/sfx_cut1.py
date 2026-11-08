# 8-bit SFX bed for cut v1, mixed under du's voice (already processed in her edit).
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
import numpy as np, subprocess, sys
SR=48000; T=43.55
SRC=os.environ.get('SRC','input.mov')
def sq(f0,f1,dur,duty=0.5,vol=1.0):
    n=int(dur*SR); t=np.arange(n)/SR; f=np.linspace(f0,f1,n); ph=np.cumsum(f)/SR
    w=np.where((ph%1)<duty,1.0,-1.0); env=np.minimum(1,t/0.004)*np.exp(-t/(dur*0.45))
    return w*env*vol
def tri(f,dur,vol=1.0):
    n=int(dur*SR); t=np.arange(n)/SR; w=2*np.abs(2*((t*f)%1)-1)-1; return w*np.exp(-t/(dur*0.5))*vol
pop=lambda: sq(520,1250,0.09,0.25)
blip=lambda: sq(1600,1600,0.035,0.25,0.6)
swipe=lambda: tri(2200,0.05,0.5)
def notes(seq,step,duty=0.5):
    out=np.zeros(int((len(seq)*step+0.25)*SR))
    for i,f in enumerate(seq): s=sq(f,f,step*1.6,duty); a=int(i*step*SR); out[a:a+len(s)]+=s[:len(out)-a]
    return out
ding=lambda: notes([1318.5,1975.5],0.07)
jingle=lambda: notes([1046.5,1318.5,1568,2093],0.075,0.25)
EV=[(0.08,pop(),1),(3.0,pop(),1),(3.45,swipe(),1),(3.95,swipe(),1),(6.23,blip(),.8),(6.6,swipe(),1),(8.37,blip(),.8),(9.3,swipe(),1),(11.5,swipe(),1),
    (17.53,pop(),.9),(17.88,blip(),.6),(18.13,blip(),.6),(18.38,blip(),.6),
    (24.53,pop(),.9),(26.2,blip(),.8),(28.53,blip(),.8),(31.7,blip(),.8),
    (35.5,ding(),1),(38.25,jingle(),1)]
voice=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',SRC,'-t',str(T),'-f','s16le','-ac','2','-ar',str(SR),'-'],capture_output=True).stdout,np.int16).astype(np.float32).reshape(-1,2)/32768
bed=np.zeros(len(voice))
for t,s,g in EV:
    a=int(t*SR); e=min(len(bed),a+len(s)); bed[a:e]+=s[:e-a]*g
bed*=10**(-24/20)   # well under the voice
mix=voice+bed[:,None]
f=int(0.08*SR); mix[-f:]*=np.linspace(1,0,f)[:,None]
(np.clip(mix,-1,1)*32767).astype(np.int16).tofile(WORK+'/cut/mix.s16')
print('peak voice',np.abs(voice).max(),'peak bed',np.abs(bed).max())
