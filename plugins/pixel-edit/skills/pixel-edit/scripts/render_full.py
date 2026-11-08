# Full edit v2: du's finished talking-head edit + pixel B-roll + mock screen cards + pixel overlays.
# usage: render_full.py OUT.mp4 T_START T_END
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
import os, sys, json, math, subprocess, numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from overlays import seg0, seg2, toc_layer, eob
from overlays2 import a_overlay
import k4_anim, bscenes, summary
from banim import BAnim
from subs import sub_layer
SRC=os.environ.get('SRC','input.mov')
FPS=30; W,H=1080,1440
# ---------- timeline ----------
SEG=[('A0',0,3.0),('C',3.0,13.33),('Az',13.33,20.93),('At',20.93,35.5),('B:K4',35.5,43.62),('B:K5',43.62,53.60),
 ('A',53.60,61.73),('C',61.73,74.30),('A',74.30,84.10),('C',84.10,90.10),('A',90.10,97.57),('B:K6',97.57,110.33),
 ('C',110.33,116.67),('A',116.67,131.13),('B:K7',131.13,144.57),('A',144.57,147.63),('B:K7b',147.63,152.80),
 ('A',152.80,164.33),('B:K9',164.33,176.80),('C',176.80,197.33),('A',197.33,203.27),('C',203.27,217.40),
 ('A',217.40,223.63),('C',223.63,236.57),('Ap',236.57,250.33),('B:K12',250.33,256.77),('B:K13',256.77,268.20),
 ('C',268.20,270.63),('Ap2',270.63,277.87),('S',277.87,280.93),('A',280.93,999)]
PUSH={'Ap':(241.6,250.33),'Ap2':(270.63,277.87)}
BDUR={'K4':8.1,'K5':10.0,'K6':12.8,'K7':22,'K9':12.5,'K12':6.5,'K13':11.5}
_B={}
def banim(name):
    if name not in _B:
        if name=='K4': _B[name]=None
        else: _B[name]=bscenes.make('K7' if name=='K7b' else name,BDUR['K7' if name=='K7b' else name])
    return _B[name]
def b_frame(name,t,t0):
    lt=t-t0
    if name=='K4': return k4_anim.frame(lt,8.1)
    if name=='K7b': return banim('K7b').frame(16.5+lt)
    return banim(name).frame(lt)
_S=None
def sum_frame(lt):
    global _S
    if _S is None: _S=BAnim(summary.SUMMARY['world'],summary.SUMMARY['ui'],mood='golden',push=0.02,dur=3.1)
    return _S.frame(lt)
# ---------- cards ----------
C1D=WORK+'/cut/cards/'; C2D=WORK+'/full/cards/'
M1=json.load(open(C1D+'hl.json')); M2=json.load(open(C2D+'meta.json'))
def T(a,b): return ('type',a,b)
CARDS=[('c1',3.0,6.23,[(1,3.45),(2,3.95)]),('c2',6.23,8.37,[(1,6.6)]),('c3',8.37,13.33,[(1,9.3),(2,11.5)]),
 ('c2a',61.73,69.67,T(62.3,65.6)),('c2b',69.67,74.30,[(1,70.6)]),
 ('c3a',84.10,87.50,T(84.4,86.4)),('c3b',87.50,90.10,[(1,88.3)]),
 ('c4a',110.33,114.13,[(1,112.7)]),('c4b',114.13,116.67,[(1,114.6)]),
 ('c5a',176.80,184.67,[(1,181.3)]),('c5a2',184.67,186.60,[(1,185.0)]),('c5b',186.60,193.17,T(187.3,190.6)),('c5c',193.17,197.33,[(1,194.0)]),
 ('c6a',203.27,213.0,[(1,204.9),(2,210.8)]),('c6b',213.0,217.40,[(1,213.4),(2,216.3)]),
 ('c7a',223.63,230.07,[(1,228.0)]),('c7b',230.07,234.27,[(1,232.6)]),('c7c',234.27,236.57,[(1,234.6)]),
 ('c8a',268.20,270.63,[(1,268.5)])]
NOSLIDE={'c5a2'}
FIRST={3.0,61.73,84.10,110.33,176.80,203.27,223.63,268.20}
_IMG={}
def img(path):
    if path not in _IMG:
        if len(_IMG)>60: _IMG.clear()
        _IMG[path]=Image.open(path).convert('RGB')
    return _IMG[path]
def card_frame(t):
    for cid,a,b,hl in CARDS:
        if a<=t<b: break
    if isinstance(hl,tuple):
        n=M2[cid]['type']; k=int(round(n*min(max((t-hl[1])/(hl[2]-hl[1]),0),1)))
        if t>hl[2]+0.15 and int((t-hl[2])*2.2)%2: k=n  # caret blinks via frame _n vs same
        im=img(f'{C2D}{cid}_{k:02d}.png').copy(); rects=[]
    else:
        im=img((C1D if cid in ('c1','c2','c3') else C2D)+cid+'.png').copy()
        M=M1[cid] if cid in ('c1','c2','c3') else M2[cid]['hl']
        mk=Image.new('RGB',im.size,(255,255,255)); md=ImageDraw.Draw(mk); any_=False
        for k,ht in hl:
            p=min(max((t-ht)/0.28,0),1)
            if p<=0: continue
            for h in M:
                if h['k']!=k: continue
                for (x0,y0,x1,y1) in h['r']:
                    xe=x0-8+(x1-x0+16)*(p*p*(3-2*p)); md.rounded_rectangle((x0-8,y0+8,xe,y1-4),radius=8,fill=(255,224,64)); any_=True
        if any_: im=Image.fromarray((np.asarray(im,np.float32)*np.asarray(mk,np.float32)/255).astype('uint8'))
    z=1+0.035*min(max((t-a)/(b-a),0),1)
    cw,ch=W/z,H/z; x0=(W-cw)/2; y0=(H-ch)*0.3
    im=im.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+cw,y0+ch))
    if a not in FIRST and cid not in NOSLIDE and t-a<0.18:
        k=(t-a)/0.18; off=int((1-k)**2*70)
        if off:
            bg=Image.new('RGB',(W,H),(247,245,240)); bg.paste(im.crop((0,0,W,H-off)),(0,off)); im=bg
    return im,a
from ccards import card_frame   # v2: pixel agent-app cards replace the HTML screenshots
R=340; PX,PY=W-R-40,1200-R
CM=Image.new('L',(R,R),0); ImageDraw.Draw(CM).ellipse((0,0,R-1,R-1),fill=255)
RIM=Image.new('L',(R+10,R+10),0); ImageDraw.Draw(RIM).ellipse((0,0,R+9,R+9),outline=255,width=5)
SH=Image.new('L',(W,H),0); SH.paste(CM,(PX,PY+10)); SH=SH.filter(ImageFilter.GaussianBlur(22)).point(lambda v:v*110//255)
def pip(base,src,slide):
    face=src.crop((60,110,1020,1070)).resize((R,R),Image.LANCZOS)
    dx=int((1-slide)*(R+80))
    if dx:
        sh=Image.new('L',(W,H),0); sh.paste(SH.crop((0,0,W-dx,H)),(dx,0)); base.paste((30,20,30),(0,0),sh)
    else: base.paste((30,20,30),(0,0),SH)
    base.paste(face,(PX+dx,PY),CM); base.paste((255,255,255),(PX-5+dx,PY-5),RIM)
def popin(card,bgframe,t,c0):
    k=eob((t-c0)/0.35,1.4); bg=Image.blend(bgframe,Image.new('RGB',(W,H),(30,24,28)),0.45)
    cw,ch=max(2,int(W*(0.55+0.45*k))),max(2,int(H*(0.55+0.45*k)))
    bg.paste(card.resize((cw,ch),Image.BICUBIC),((W-cw)//2,(H-ch)//2)); return bg
def zoom(src,z,ax=540,ay=1124):
    cw,ch=W/z,H/z; x0=ax-ax/z; y0=ay-ay/z
    return src.resize((W,H),Image.BICUBIC,box=(x0,y0,x0+cw,y0+ch))
GRID=24; ORDER=np.random.default_rng(3).random((H//GRID,W//GRID))
def mosaic(im,b): return im if b<=1 else im.resize((W//b,H//b),Image.BILINEAR).resize((W,H),Image.NEAREST)
def dissolve(a,b,p):
    a2=mosaic(a,int(1+p*30)); b2=mosaic(b,int(1+(1-p)*30))
    m=np.kron((ORDER<p).astype(np.uint8)*255,np.ones((GRID,GRID),np.uint8))
    return Image.composite(b2,a2,Image.fromarray(m))
# ---------- subtitles (retyped on B / C / summary) ----------
CUES=[(3.03,4.67,'大家在开始用AI做coding'),(4.67,6.23,'或者做工作流项目的时候'),(6.23,8.37,'肯定都会遇到过这两个名词'),
      (8.37,11.27,'它们是我们用agent做长任务'),(11.27,13.33,'复杂任务必备的两个工具'),
      (35.63,37.23,'那Git其实就是我们给AI'),(37.23,38.43,'项目做存档的工具'),(38.43,40.77,'跟我最近打星露谷物语的时候点'),(40.77,43.6,'的那个存档的作用是一模一样的')]
CUES+=[tuple(c) for c in json.load(open(WORK+'/full/cues.json'))]
_SUB={}
def subimg(s):
    if s not in _SUB: _SUB[s]=sub_layer(s,cy=1272)
    return _SUB[s]
def seg_at(t):
    for i,(k,a,b) in enumerate(SEG):
        if a<=t<b: return i
    return len(SEG)-1
def base(i,t,src):
    """Frame for segment i at time t (no subtitles)."""
    k,a,b=SEG[i]
    if k=='A0':
        o=src.convert('RGBA'); o.alpha_composite(seg0(t)); return o.convert('RGB')
    if k=='Az':
        z=1+0.08*((t-a)/(b-a))**1.1; o=zoom(src,z).convert('RGBA'); o.alpha_composite(seg2(t)); return o.convert('RGB')
    if k=='At':
        o=src.convert('RGBA'); o.alpha_composite(toc_layer(t)); return o.convert('RGB')
    if k.startswith('A'):
        f=src
        if k in PUSH:
            p0,p1=PUSH[k]; z=1+0.06*min(max((t-p0)/(p1-p0),0),1)**1.2
            if z>1.001: f=zoom(src,z)
        o=f.convert('RGBA'); o.alpha_composite(a_overlay(t)); return o.convert('RGB')
    if k.startswith('B:'): return b_frame(k[2:],t,a)
    if k=='S':
        f=sum_frame(t-a); pip(f,src,eob((t-a-0.1)/0.35,1.2)); return f
    if k=='C':
        card,ca=card_frame(t)
        if t-a<0.35 and i>0:
            card=popin(card,base(i-1,t,src),t,a)
        pip(card,src,eob((t-a-0.1)/0.35,1.2) if a in FIRST else 1)
        return card
def render(t,src):
    i=seg_at(t); k,a,b=SEG[i]; out=base(i,t,src)
    retype=k[0] in 'BCS'
    # pixel dissolve into B (from previous segment) and out of B (into the next one)
    if k.startswith('B:') and t-a<0.3 and i>0:
        p=(t-a)/0.3; out=dissolve(base(i-1,t,src),out,p); retype=p>0.5
    if i>0 and SEG[i-1][0].startswith('B:') and not k.startswith('B:') and k!='C' and t-a<0.3:
        p=(t-a)/0.3; out=dissolve(base(i-1,t,src),out,p); retype=retype or p<0.5
    if retype:
        for c0,c1,s in CUES:
            if c0<=t<c1:
                o=out.convert('RGBA'); o.alpha_composite(subimg(s)); out=o.convert('RGB'); break
    return out
if __name__=='__main__':
    OUT=sys.argv[1]; T0=float(sys.argv[2]); T1=float(sys.argv[3])
    n0=int(round(T0*FPS)); n1=int(round(T1*FPS))
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',SRC,'-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',OUT],stdin=subprocess.PIPE)
    for fi in range(n0,n1):
        raw=dec.stdout.read(W*H*3)
        if len(raw)<W*H*3: break
        t=fi/FPS
        enc.stdin.write(render(t,Image.frombytes('RGB',(W,H),raw)).tobytes())
        if (fi-n0)%150==0: print(f'{t:.1f}s',flush=True)
    enc.stdin.close(); enc.wait(); dec.kill()
    print('done',flush=True)
