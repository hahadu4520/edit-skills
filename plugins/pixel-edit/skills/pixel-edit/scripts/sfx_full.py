# 8-bit SFX bed for the full edit, mixed well under du's (already processed) voice.
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
import numpy as np, subprocess
from sfx_cut1 import sq, tri, notes, pop, blip, swipe, ding, jingle, SR
SRC=os.environ.get('SRC','input.mov')
def noise(dur,vol=1.0):
    n=int(dur*SR); t=np.arange(n)/SR; r=np.random.default_rng(1).choice([-1.0,1.0],n)
    r=np.repeat(r[::8],8)[:n]; return r*np.exp(-t/(dur*0.3))*vol
buzz=lambda: sq(180,140,0.18,0.5,0.8)
knock=lambda: tri(160,0.08,1.0)
thump=lambda: np.concatenate([sq(220,90,0.1,0.5,0.9)])
tick=lambda: sq(2400,2400,0.012,0.25,0.25)
EV=[(0.08,pop(),1),(3.0,pop(),1),(3.45,swipe(),1),(3.95,swipe(),1),(6.23,blip(),.8),(6.6,swipe(),1),(8.37,blip(),.8),(9.3,swipe(),1),(11.5,swipe(),1),
    (17.53,pop(),.9),(17.88,blip(),.6),(18.13,blip(),.6),(18.38,blip(),.6),(24.53,pop(),.9),(26.2,blip(),.8),(28.53,blip(),.8),(31.7,blip(),.8),
    (35.5,ding(),1),(38.25,jingle(),1),
    (43.62,ding(),.8),(44.9,blip(),.7),(47.9,blip(),.7),(48.9,sq(400,1200,0.5,0.25,0.5),1),(51.62,jingle(),1),
    (53.75,blip(),.8),(55.35,blip(),.8),(59.8,blip(),.8),
    (61.73,pop(),1),(69.67,blip(),.8),(70.6,swipe(),1),(76.9,blip(),.8),(78.3,blip(),.8),(79.75,pop(),1),
    (84.10,pop(),1),(87.5,blip(),.8),(88.3,swipe(),1),(91.2,blip(),.7),(93.7,blip(),.7),(95.0,blip(),.7),
    (97.57,ding(),1),(98.57,blip(),.8),(101.32,blip(),.8),(101.82,sq(1900,1900,0.035,0.25,0.6),1),(102.32,sq(2200,2200,0.035,0.25,0.6),1),
    (103.97,buzz(),.7),(108.17,sq(1400,500,0.35,0.25,0.5),1),(109.47,jingle(),1),
    (110.33,pop(),1),(112.7,swipe(),1),(114.13,blip(),.8),(114.6,swipe(),1),(120.0,pop(),1),(128.7,blip(),.7),(130.0,blip(),.7),
    (131.13,ding(),1),(133.33,blip(),.8),(133.48,blip(),.8),(133.63,blip(),.8),(133.83,pop(),1),
    (144.9,blip(),.7),(145.3,blip(),.7),(145.7,blip(),.7),(147.63,ding(),.8),(147.93,buzz(),.5),(148.23,buzz(),.5),(148.73,blip(),.9),(150.63,pop(),.9),(151.63,jingle(),1),
    (156.5,pop(),.9),(164.33,ding(),1),(169.63,knock(),1),(169.85,knock(),1),(173.93,pop(),.9),(174.73,jingle(),.9),
    (176.80,pop(),1),(181.3,swipe(),1),(184.67,blip(),.9),(185.0,swipe(),1),(186.60,blip(),.8),(193.17,blip(),.8),(194.0,swipe(),1),
    (200.7,blip(),.7),(201.3,blip(),.7),(201.9,blip(),.7),(203.27,pop(),1),(204.9,swipe(),1),(210.8,swipe(),1),(213.0,blip(),.8),(213.4,swipe(),1),(216.3,swipe(),1),
    (218.8,blip(),.8),(223.63,pop(),1),(228.0,swipe(),1),(230.07,blip(),.8),(232.6,jingle(),.8),(234.27,blip(),.8),(234.6,swipe(),1),
    (237.4,blip(),.8),(245.9,blip(),.8),(250.33,ding(),1),(252.93,noise(0.35),.8),(256.77,ding(),.7),(262.07,pop(),.8),(264.27,blip(),.8),(267.27,thump(),1),(267.47,jingle(),1),
    (268.20,pop(),1),(268.5,swipe(),1),(275.2,blip(),.8),(277.87,pop(),1),(278.22,blip(),.7),(278.62,blip(),.7),(282.33,pop(),.9),(285.17,jingle(),1)]
for a,b in [(62.3,65.6),(84.4,86.4),(187.3,190.6)]:
    t=a
    while t<b: EV.append((t,tick(),1)); t+=0.11
voice=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',SRC,'-f','s16le','-ac','2','-ar',str(SR),'-'],capture_output=True).stdout,np.int16).astype(np.float32).reshape(-1,2)/32768
bed=np.zeros(len(voice))
for t,s,g in EV:
    a=int(t*SR); e=min(len(bed),a+len(s)); bed[a:e]+=s[:e-a]*g
bed*=10**(-24/20)
mix=np.clip(voice+bed[:,None],-1,1)
(mix*32767).astype(np.int16).tofile(WORK+'/full/mix_full.s16')
print('ok',len(voice)/SR)
