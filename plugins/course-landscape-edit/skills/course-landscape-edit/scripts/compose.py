import json,subprocess,sys,os,numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
E=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.dirname(E)+'/src_cut.mp4'
OUT=sys.argv[1]; T0=float(sys.argv[2]); T1=float(sys.argv[3])
FPS=30;W,H=1920,1080
segs=json.load(open(E+'/segs.json'))
CLIPF=E+'/clips.json';subs=json.load(open(E+'/subs.json'));en=open(E+'/en.txt').read().split('\n')
PX,PY,PW,PH=48,112,1360,765
BW,BH=432,520;BX=W-48-BW;BY=PY+PH-BH
SW=int(1080*BW/BH);SX=600-SW//2
CH=json.load(open(E+'/chap.json'));NCH=len(CH)-1  # 章节数不固定，按 chap.json 自动算
CHN=json.load(open(E+'/chap_names.json')) if os.path.exists(E+'/chap_names.json') else None
import rules;rules.check(segs,json.load(open(CLIPF)) if os.path.exists(CLIPF) else {},CH,CHN)  # 运镜/转场/章节表不合规就直接报错
def rmask(w,h,r):
    m=np.zeros((h,w),np.uint8)
    cv2.rectangle(m,(r,0),(w-1-r,h-1),255,-1);cv2.rectangle(m,(0,r),(w-1,h-1-r),255,-1)
    for cx,cy in [(r,r),(w-1-r,r),(r,h-1-r),(w-1-r,h-1-r)]:cv2.circle(m,(cx,cy),r,255,-1,cv2.LINE_AA)
    return m
PM=rmask(PW,PH,28).astype(np.float32)[:,:,None]/255;BM=rmask(BW,BH,26).astype(np.float32)[:,:,None]/255
def paste(dst,src,x,y,m):
    h,w=src.shape[:2];r=dst[y:y+h,x:x+w].astype(np.float32);dst[y:y+h,x:x+w]=(src*m+r*(1-m)).astype(np.uint8)
def blend4(dst,src,x,y):
    h,w=src.shape[:2];a=src[:,:,3:4].astype(np.float32)/255;r=dst[y:y+h,x:x+w].astype(np.float32)
    dst[y:y+h,x:x+w]=(src[:,:,:3]*a+r*(1-a)).astype(np.uint8)
# static background
BG=np.empty((H,W,3),np.float32);BG[:]=(244,242,238)
sh=np.zeros((H,W),np.float32);sh[PY+18:PY+PH+18,PX:PX+PW]=1;sh[BY+18:BY+BH+18,BX:BX+BW]=1
sh=cv2.GaussianBlur(sh,(0,0),20)*0.13;BG=np.clip(BG*(1-sh[:,:,None])+np.array([30,30,40])*sh[:,:,None],0,255).astype(np.uint8)
LAB=[np.array(Image.open(f'{E}/kf/lab_{i}.png').convert('RGBA')) for i in range(NCH)]
# progress bar geometry (matches gen.py)
X0,X1,GAP=64,1856,8;tot=CH[-1];avail=X1-X0-GAP*(NCH-1);BARS=[];x=X0
for i in range(NCH):
    w=avail*(CH[i+1]-CH[i])/tot;BARS.append((x,w));x+=w+GAP
def bar(img,t):
    for i,(x,w) in enumerate(BARS):
        a,b=CH[i],CH[i+1];f=1 if t>=b else (max(0,(t-a)/(b-a)))
        cv2.rectangle(img,(int(x+4),40),(int(x+w-4),47),(226,226,226),-1);cv2.circle(img,(int(x+4),44),4,(226,226,226),-1,cv2.LINE_AA);cv2.circle(img,(int(x+w-4),44),4,(226,226,226),-1,cv2.LINE_AA)
        if f>0:
            xe=x+max(8,w*f)
            cv2.rectangle(img,(int(x+4),40),(int(xe-4),47),(47,107,255),-1);cv2.circle(img,(int(x+4),44),4,(47,107,255),-1,cv2.LINE_AA);cv2.circle(img,(int(xe-4),44),4,(47,107,255),-1,cv2.LINE_AA)
def chap(t):
    for i in range(NCH):
        if t<CH[i+1]: return i
    return NCH-1
# panel sources
cache={}
CMPBG={k:np.array(Image.open(f'{E}/cmpbg/{k}.png').convert('RGB')) for k in ('both','rmiss','lmiss')}
CM=rmask(340,604,22).astype(np.float32)[:,:,None]/255
CMPF={k:np.array(Image.open(f'{E}/cmpfull/{k}.png').convert('RGB')) for k in ('both','rmiss','lmiss')}
FVW,FVH,FVY,FLX,FRX=432,768,112,468,1020;FM=rmask(FVW,FVH,24).astype(np.float32)[:,:,None]/255
CLIPS=json.load(open(CLIPF))
SF=ImageFont.truetype(E+'/fonts/SmileySans-Oblique.ttf',34)
def tagged(img,tag):
    im=Image.fromarray(img);d=ImageDraw.Draw(im);b=d.textbbox((0,0),tag,font=SF);w,h=b[2]-b[0]+40,b[3]-b[1]+24
    d.rounded_rectangle((28,28,28+w,28+h),12,fill=(229,50,45));d.text((48-b[0],40-b[1]),tag,font=SF,fill='white');return np.array(im)
def panel_static(k):
    if k in cache: return cache[k]
    s=segs[k];ty,v=s['layer'].split(':',1)
    if ty=='slide':
        p=f'{E}/slides/out/{v}.jpg';a=np.array(Image.open(p).convert('RGB'));a=cv2.resize(a,(PW,PH),interpolation=cv2.INTER_AREA)
    else:
        a=np.array(Image.open(f'{E}/{v}').convert('RGB'))[126:824,64:1304];a=cv2.resize(np.ascontiguousarray(a),(PW,PH),interpolation=cv2.INTER_LINEAR)
    if s.get('tag'): a=tagged(a,s['tag'])
    cache.clear() if len(cache)>6 else None;cache[k]=a;return a
nfr={};VM={}
def panel(k,t):
    s=segs[k];ty,v=s['layer'].split(':',1)
    if ty=='cmp':
        C=s['cmp'];lt=t-s['t0'];v='both' if all(q[0] for q in C) else ('rmiss' if C[0][0] else 'lmiss')
        a=CMPBG[v].copy()
        for j,(name,st) in enumerate(C):
            if not name: continue
            d=f'{E}/cmp/{name}';n=nfr.setdefault(d,len(os.listdir(d)));i=min(int((st+lt)*FPS),n-1)
            f=cv2.cvtColor(cv2.imread(f'{d}/{i+1:05d}.jpg'),cv2.COLOR_BGR2RGB);f=cv2.resize(f,(340,604),interpolation=cv2.INTER_AREA)
            paste(a,f,300 if j==0 else 720,110,CM)
        return a
    if ty=='vid':
        d=f'{E}/cmp/{v}';n=nfr.setdefault(d,len(os.listdir(d)));lt=t-s['t0'];i=min(int((s.get('vstart',0)+lt)*FPS),n-1)
        f=cv2.cvtColor(cv2.imread(f'{d}/{i+1:05d}.jpg'),cv2.COLOR_BGR2RGB)
        bg=cv2.resize(f,(PW,int(PW*f.shape[0]/f.shape[1])));y0=(bg.shape[0]-PH)//2;bg=bg[y0:y0+PH]
        bg=(cv2.GaussianBlur(bg,(0,0),40).astype(np.float32)*0.55).astype(np.uint8)
        vh=PH-60;vw=int(vh*f.shape[1]/f.shape[0]);fv=cv2.resize(f,(vw,vh),interpolation=cv2.INTER_AREA)
        m=VM.setdefault((vw,vh),rmask(vw,vh,20).astype(np.float32)[:,:,None]/255)
        paste(bg,fv,(PW-vw)//2,30,m);return bg
    if ty=='clips':
        CLP=CLIPS[v];lt=t-s['t0']
        cl=next((q for q in CLP if lt<q[1]),CLP[-1]);a0,a1,d,b0,b1=cl[:5];zs=cl[5] if len(cl)>5 else 0.5
        n=nfr.setdefault(d,len(os.listdir(E+'/'+d)));i=min(max(int((lt-a0)*FPS),0),n-1)
        a=cv2.cvtColor(cv2.imread(f'{E}/{d}/{i+1:05d}.jpg'),cv2.COLOR_BGR2RGB)
        u=min(1,max(0,(lt-a0-zs)/0.6)) if b0[2]!=b1[2] else min(1,max(0,(lt-a0)/(a1-a0)));u=u*u*(3-2*u);x,y,w=[b0[q]+(b1[q]-b0[q])*u for q in range(3)];h=w*PH/PW
        x=min(max(0,x),a.shape[1]-w);y=min(max(0,y),a.shape[0]-h)
        M=np.float32([[PW/w,0,-x*PW/w],[0,PH/h,-y*PH/h]])
        return cv2.warpAffine(a,M,(PW,PH),flags=cv2.INTER_AREA,borderMode=cv2.BORDER_REPLICATE)
    if ty=='rec':
        d=f'{E}/rec/{v}';n=nfr.setdefault(v,len(os.listdir(d)));lt=t-s['t0'];i=min(int(lt*FPS),n-1)
        a=cv2.cvtColor(cv2.imread(f'{d}/{i+1:05d}.jpg'),cv2.COLOR_BGR2RGB);Z=s['zoom']
        for j in range(len(Z)-1):
            if lt<Z[j+1][0]: break
        a0,a1=Z[j],Z[min(j+1,len(Z)-1)];u=0 if a1[0]==a0[0] else min(1,max(0,(lt-a0[0])/(a1[0]-a0[0])));u=u*u*(3-2*u)
        x,y,w=[a0[q]+(a1[q]-a0[q])*u for q in (1,2,3)];h=w*PH/PW
        x=min(max(0,x),a.shape[1]-w);y=min(max(0,y),a.shape[0]-h)
        M=np.float32([[PW/w,0,-x*PW/w],[0,PH/h,-y*PH/h]])
        return cv2.warpAffine(a,M,(PW,PH),flags=cv2.INTER_AREA,borderMode=cv2.BORDER_REPLICATE)
    if ty!='anim': return panel_static(k)
    d=f'{E}/anim/fr_{v}';n=nfr.setdefault(v,len(os.listdir(d)));i=min(int(round((t-s['t0'])*FPS)),n-1)
    a=cv2.cvtColor(cv2.imread(f'{d}/{i:05d}.jpg'),cv2.COLOR_BGR2RGB)[126:824,64:1304]
    return cv2.resize(np.ascontiguousarray(a),(PW,PH),interpolation=cv2.INTER_LINEAR)
def full_cmp(k,t):
    s=segs[k];C=s['cmp'];lt=t-s['t0'];v='both' if all(q[0] for q in C) else ('rmiss' if C[0][0] else 'lmiss')
    a=CMPF[v].copy()
    for j,(name,st) in enumerate(C):
        if not name: continue
        d=f'{E}/cmp/{name}';n=nfr.setdefault(d,len(os.listdir(d)));i=min(int((st+lt)*FPS),n-1)
        f=cv2.cvtColor(cv2.imread(f'{d}/{i+1:05d}.jpg'),cv2.COLOR_BGR2RGB);f=cv2.resize(f,(FVW,FVH),interpolation=cv2.INTER_CUBIC)
        paste(a,f,FLX if j==0 else FRX,FVY,FM)
    return a
def seg_at(t):
    for k,s in enumerate(segs):
        if s['t0']<=t<s['t1']:return k
    return len(segs)-1
fcn=ImageFont.truetype(E+'/fonts/SmileySans-Oblique.ttf',54);fen=ImageFont.truetype(E+'/fonts/SmileySans-Oblique.ttf',30)
subcache={}
def sub_img(i):
    if i in subcache:return subcache[i]
    cn=subs[i][2];e=en[i] if i<len(en) else ''
    tmp=ImageDraw.Draw(Image.new('RGBA',(10,10)))
    bc=tmp.textbbox((0,0),cn,font=fcn);be=tmp.textbbox((0,0),e,font=fen)
    w=max(bc[2]-bc[0],be[2]-be[0])+64;h=(bc[3]-bc[1])+(be[3]-be[1])+50
    im=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,w-1,h-1),16,fill=(16,17,20,184))
    d.text(((w-(bc[2]-bc[0]))/2-bc[0],16-bc[1]),cn,font=fcn,fill=(255,255,255,255))
    d.text(((w-(be[2]-be[0]))/2-be[0],16+(bc[3]-bc[1])+12-be[1]),e,font=fen,fill=(225,227,232,255))
    a=np.array(im);subcache[i]=a;return a
def sub_at(t):
    for i in range(len(subs)-1,-1,-1):
        if subs[i][0]<=t:
            end=min(subs[i][1]+0.25,subs[i+1][0] if i+1<len(subs) else 1e9)
            return i if t<end else None
    return None
XF=0.3;ease=lambda x:1-(1-x)**3;SUBY=(PY+PH+H)//2+2
dec=subprocess.Popen(['ffmpeg','-loglevel','error','-ss',str(T0),'-i',SRC,'-t',str(T1-T0),'-f','rawvideo','-pix_fmt','rgb24','-r',str(FPS),'-'],stdout=subprocess.PIPE)
enc=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(FPS),'-i','-','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p',OUT],stdin=subprocess.PIPE)
n=0;fs=1440*1080*3
while True:
    buf=dec.stdout.read(fs)
    if len(buf)<fs:break
    src=np.frombuffer(buf,np.uint8).reshape(1080,1440,3)
    t=T0+n/FPS;k=seg_at(t);s=segs[k];lt=t-s['t0']
    def comp(kk,tt):
        if segs[kk]['layer'].startswith('cmp'): return full_cmp(kk,tt)
        o=BG.copy();paste(o,panel(kk,tt),PX,PY,PM)
        im=cv2.resize(src[:,SX:SX+SW],(BW,BH),interpolation=cv2.INTER_AREA);paste(o,im,BX,BY,BM);return o
    out=comp(k,t)
    if k>0 and lt<XF and segs[k].get('trans','dissolve')!='cut':
        pk=k-1;fullx=segs[k]['layer'].startswith('cmp') or segs[pk]['layer'].startswith('cmp')
        e=ease(lt/XF)
        if fullx: q=comp(pk,segs[pk]['t1']-0.001);out=(q.astype(np.float32)*(1-e)+out.astype(np.float32)*e).astype(np.uint8)
        else:
            q=panel(pk,segs[pk]['t1']-0.001);p=panel(k,t);p=(q.astype(np.float32)*(1-e)+p.astype(np.float32)*e).astype(np.uint8);paste(out,p,PX,PY,PM)
    bar(out,t);blend4(out,LAB[chap(t)],0,0)
    si=sub_at(t)
    if si is not None:
        a=sub_img(si);h,w=a.shape[:2];blend4(out,a,(W-w)//2,SUBY-h//2)
    enc.stdin.write(out.tobytes());n+=1
    if n%900==0:print('t',round(t,1),flush=True)
enc.stdin.close();enc.wait();print('done',n)
