# Generic animator for the HD-2D pixel B-roll: the world is drawn per frame on the 270x360 grid,
# graded once per distinct world image (cached), then rays/particles/push-in/UI are layered on top.
from world import *
import numpy as np, math, random, hashlib
from PIL import Image, ImageDraw, ImageFilter
S_=4
MOODS={'golden':(lambda t:np.stack([1.10-0.22*t,1.03-0.15*t,0.90-0.02*t],2),np.array([0.30,0.24,0.12])),
       'day':(lambda t:np.stack([1.04-0.12*t,1.04-0.10*t,1.0-0.02*t],2),np.array([0.22,0.22,0.18])),
       'dusk':(lambda t:np.stack([1.0-0.25*t,0.92-0.25*t,1.0-0.1*t],2),np.array([0.26,0.16,0.20]))}
_HH,_WW=H*S_,W*S_
_yy,_xx=np.mgrid[0:_HH,0:_WW]
_T=(_xx/_WW*0.45+_yy/_HH*0.55)
_VIG=np.clip(1.08-0.32*(((_xx-_WW/2)/(_WW/2))**2+((_yy-_HH*0.45)/(_HH/1.6))**2),0.55,1.1)[...,None].astype(np.float32)
def _rays(phase):
    yy,xx=np.mgrid[0:_HH:4,0:_WW:4]
    ang=np.arctan2(yy+200,xx+260); r_=np.zeros(yy.shape,np.float32)
    for c,w in [(0.62,0.035),(0.78,0.05),(0.93,0.03),(1.06,0.045)]: r_+=np.exp(-((ang-c-0.025*math.sin(phase+c*5))/w)**2)*0.9
    r_*=np.clip(1-(np.sqrt((xx+260)**2+(yy+200)**2)/1700),0,1)
    im=Image.fromarray((np.clip(r_,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(4.5)).resize((_WW,_HH),Image.BILINEAR)
    return np.array(im).astype(np.float32)[...,None]/255
RAYS=None
def eob(x,s=1.7):
    x=min(max(x,0),1); x-=1; return x*x*((s+1)*x+s)+1
def clamp(x): return min(max(x,0),1)
def smooth(x): x=clamp(x); return x*x*(3-2*x)
def pop_into(dst,t,t0,draw,box,dur=0.3):
    """draw(sc) onto a temp Scene's ui; paste region box into dst (RGBA lowres) with pop scale."""
    if t<t0: return
    tmp=Scene(); draw(tmp); el=tmp.ui.crop(box)
    k=eob((t-t0)/dur)
    if k<0.999:
        w,h=el.size; nw,nh=max(1,int(w*k)),max(1,int(h*k)); el=el.resize((nw,nh),Image.NEAREST)
        cx,cy=(box[0]+box[2])//2,(box[1]+box[3])//2; dst.alpha_composite(el,(cx-nw//2,cy-nh//2))
    else: dst.alpha_composite(el,(box[0],box[1]))
def pop_world(sc,t,t0,draw,box,dur=0.3):
    if t<t0: return
    tmp=Scene(); tmp.im=Image.new('RGBA',(W,H),(0,0,0,0)); tmp.d=ImageDraw.Draw(tmp.im); tmp.d.fontmode='1'; tmp.px=tmp.im.load()
    draw(tmp); el=tmp.im.crop(box); k=eob((t-t0)/dur)
    if k<0.999:
        w,h=el.size; nw,nh=max(1,int(w*k)),max(1,int(h*k)); el=el.resize((nw,nh),Image.NEAREST)
        cx,cy=(box[0]+box[2])//2,(box[1]+box[3])//2; sc.im.alpha_composite(el,(cx-nw//2,cy-nh//2))
    else: sc.im.alpha_composite(el,(box[0],box[1]))
def typed(lines,t,t0,cps=14):
    n=int(max(0,t-t0)*cps); out=[]
    for l in lines:
        s,c=(l if isinstance(l,tuple) else (l,None))
        k=min(len(s),n); n-=len(s)+2
        out.append((s[:k],c) if c else s[:k])
    return out
class BAnim:
    def __init__(s,world,ui,mood='golden',focus=0.45,band=0.20,bloom=0.5,push=0.04,dur=8,seed=7,rays=True,flash=None):
        s.world,s.ui,s.mood,s.focus,s.band,s.bloom,s.push,s.dur,s.rays=world,ui,mood,focus,band,bloom,push,dur,rays
        s.flash=flash or []   # list of (t, x, y) low-res glow bursts
        s.cache={}
        rnd=random.Random(seed)
        s.parts=[dict(x=rnd.uniform(0,W),y=rnd.uniform(40,250),v=rnd.uniform(3,7),ph=rnd.uniform(0,6.28),c=rnd.choice([(255,236,170),(255,214,226),(255,250,220)])) for _ in range(36)]
        k=np.clip((np.abs(_yy/_HH-focus)-band)/0.12,0,1)[...,None].astype(np.float32); s.k=k
    def grade(s,im):
        key=hashlib.md5(im.tobytes()).hexdigest()
        if key in s.cache: return s.cache[key]
        big=im.convert('RGB').resize((_WW,_HH),Image.NEAREST)
        img=np.asarray(big,np.float32)/255
        img=img*MOODS[s.mood][0](_T)
        sat=img.max(2)-img.min(2)
        br=np.clip(img-0.86,0,1)*(sat[...,None]>0.15)
        bl=np.asarray(Image.fromarray((np.clip(br*3,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(14)),np.float32)/255
        img=np.clip(img+bl*s.bloom,0,1)
        blur=np.asarray(Image.fromarray((img*255).astype('uint8')).filter(ImageFilter.GaussianBlur(5)),np.float32)/255
        img=img*(1-s.k)+blur*s.k
        if len(s.cache)>8: s.cache.clear()
        s.cache[key]=img; return img
    def frame(s,t):
        global RAYS
        if RAYS is None: RAYS=[_rays(2*math.pi*i/24) for i in range(24)]
        sc=Scene(); s.world(sc,t)
        img=s.grade(sc.im)
        if s.rays: img=img+RAYS[int(t*6)%24]*(0.85+0.15*math.sin(t*1.7))*MOODS[s.mood][1]
        for (ft,fx,fy) in s.flash:
            tj=t-ft
            if 0<=tj<0.9:
                f=math.exp(-tj*4); cx,cy=fx*S_,fy*S_
                y0,y1=max(0,cy-500),min(_HH,cy+500); x0,x1=max(0,cx-500),min(_WW,cx+500)
                yy,xx=np.ogrid[y0:y1,x0:x1]; g=np.exp(-((xx-cx)**2+(yy-cy)**2)/(2*(60+tj*260)**2))
                img=img.copy(); img[y0:y1,x0:x1]+= (g*f*0.9)[...,None]*np.array([0.85,0.95,1.0],np.float32)
        img=np.clip(img*_VIG,0,1)
        out=Image.fromarray((img*255).astype('uint8')).convert('RGBA')
        glow=Image.new('RGBA',out.size,(0,0,0,0)); gd=ImageDraw.Draw(glow); dr=ImageDraw.Draw(out)
        for p in s.parts:
            y=(p['y']-p['v']*t)%220+30; x=p['x']+3*math.sin(t*1.3+p['ph']); tw_=0.55+0.45*math.sin(t*3+p['ph'])
            X,Y=int(x)*S_,int(y)*S_
            gd.ellipse((X-10,Y-10,X+14,Y+14),fill=p['c']+(int(70*tw_),)); dr.rectangle((X,Y,X+S_-1,Y+S_-1),fill=p['c']+(int(255*tw_),))
        out=Image.alpha_composite(out,glow.filter(ImageFilter.GaussianBlur(6)))
        z=1+s.push*clamp(t/s.dur)
        if z>1.001:
            w,h=out.size; cw,ch=w/z,h/z; x0=(w-cw)/2; y0=(h-ch)*0.4
            out=out.resize((w,h),Image.BILINEAR,box=(x0,y0,x0+cw,y0+ch))
        ui=Scene(); s.ui(ui,t)
        out=Image.alpha_composite(out,ui.ui.resize((_WW,_HH),Image.NEAREST))
        return out.convert('RGB')
def burst(d,t,t0,cx,cy,col=(255,252,210),n=10,dur=1.2,spd=40):
    tj=t-t0
    if not (0<=tj<dur): return
    for i in range(n):
        a=i/n*6.283+0.3; r=8+tj*spd
        x=int(cx+math.cos(a)*r); y=int(cy+math.sin(a)*r*0.8)
        if (tj/dur)<0.75 or int(tj*20)%2: d.point([(x,y),(x-1,y),(x+1,y),(x,y-1),(x,y+1)],fill=col); d.point((x,y),fill=(255,255,255))
