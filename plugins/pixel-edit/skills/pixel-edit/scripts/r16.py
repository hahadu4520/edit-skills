# 16:9 edit of the Git / GitHub video. Same timeline, audio and pixel kit as the 3:4 final-v3;
# the vertical 270x360 kit is reused as-is and staged inside a 480x270 (x4 = 1920x1080) world.
# usage: r16.py OUT.mp4 T0 T1        (or: r16.py --still OUT.png T)
import sys, os, json, math, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import lib, world
# lighter grass (du: background too dark) -- must happen before any world is drawn / cached
world.GR=(156,204,116); world.GD=(136,186,102); world.GL=(184,222,140); world.GDD=(122,172,94)
import banim, bscenes, k4_anim, summary, acards, ccards, overlays2
from bscenes import *          # window, text, tw, bigtext, tag, sprite, eob, smooth, clamp, colours, Scene ...
from overlays2 import A_OVERLAYS
SRC=os.environ.get('SRC','input.mov')
FPS=30; WW,WH=1920,1080; LW,LH=480,270; S4=4; DX=105
FONTS=os.path.join(HERE,'..','fonts')
# ---------------------------------------------------------------- geometry switch (vertical kit <-> wide stage)
KIT=['lib','assets','world','banim','bscenes','k4_anim','summary','acards','pcards','ccards','overlays','overlays2']
class geometry:
    def __init__(s,w,h): s.w,s.h=w,h
    def __enter__(s):
        s.saved={n:(sys.modules[n].W,sys.modules[n].H) for n in KIT if n in sys.modules and hasattr(sys.modules[n],'W')}
        for n in s.saved: sys.modules[n].W,sys.modules[n].H=s.w,s.h
        s.dm=lib.dist_mask.__defaults__; lib.dist_mask.__defaults__=(s.w,s.h)
        s.gr=world.Scene.grass.__defaults__; world.Scene.grass.__defaults__=(3,0,s.h)
        g=globals(); s.mine=(g.get('W'),g.get('H')); g['W'],g['H']=s.w,s.h
    def __exit__(s,*a):
        for n,(w,h) in s.saved.items(): sys.modules[n].W,sys.modules[n].H=w,h
        lib.dist_mask.__defaults__=s.dm; world.Scene.grass.__defaults__=s.gr
        globals()['W'],globals()['H']=s.mine
V=lambda: geometry(270,360); WIDE=lambda: geometry(LW,LH)
# trees cut by the vertical canvas edge are re-drawn whole on the wide stage
STAGE={'on':False,'defer':[]}
_tree=world.Scene.tree
def _tree_staged(s,x,y,r=11,seed=0):
    if STAGE['on'] and (x-r-3<0 or x+r+3>270): STAGE['defer'].append((x,y,r,seed)); return
    _tree(s,x,y,r,seed)
world.Scene.tree=_tree_staged
# ---------------------------------------------------------------- wide HD-2D grade (BAnim, re-done at 1920x1080)
_yy,_xx=np.mgrid[0:WH,0:WW]
_T=(_xx/WW*0.45+_yy/WH*0.55).astype(np.float32)
_VIG=np.clip(1.04-0.12*(((_xx-WW/2)/(WW/2))**2+((_yy-WH*0.45)/(WH/1.6))**2),0.85,1.05)[...,None].astype(np.float32)
SOFT=(np.stack([1.05-0.05*_T,1.04-0.04*_T,1.0+0*_T],2),np.array([0.16,0.15,0.10],np.float32))
def _rays(phase):
    yy,xx=np.mgrid[0:WH:4,0:WW:4]
    ang=np.arctan2(yy+200,xx+260); r_=np.zeros(yy.shape,np.float32)
    for c,w in [(0.62,0.035),(0.78,0.05),(0.93,0.03),(1.06,0.045)]: r_+=np.exp(-((ang-c-0.025*math.sin(phase+c*5))/w)**2)*0.9
    r_*=np.clip(1-(np.sqrt((xx+260)**2+(yy+200)**2)/2000),0,1)
    im=Image.fromarray((np.clip(r_,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(4.5)).resize((WW,WH),Image.BILINEAR)
    return (np.asarray(im,np.float32)[...,None]/255)*SOFT[1]
RAYS=None
class WAnim:
    """world(sc,t) draws a 480x270 Scene; ui(sc,t) draws its ui layer. Graded once per distinct world image."""
    def __init__(s,world_fn,ui_fn,focus=0.45,band=0.6,bloom=0.2,push=0.0,dur=8,flash=None,seed=7,parts=True,static=False):
        s.world,s.ui,s.bloom,s.push,s.dur,s.flash=world_fn,ui_fn,bloom,push,dur,flash or []
        s.static=static; s.baked={}
        s.cache={}; s.key=None
        k=np.clip((np.abs(_yy/WH-focus)-band)/0.12,0,1)[...,None].astype(np.float32); s.k=k if k.max()>0 else None
        rnd=random.Random(seed)
        s.parts=[dict(x=rnd.uniform(0,LW),y=rnd.uniform(30,230),v=rnd.uniform(3,7),ph=rnd.uniform(0,6.28),c=rnd.choice([(255,236,170),(255,214,226),(255,250,220)])) for _ in range(48)] if parts else []
    def grade(s,im):
        import hashlib
        key=hashlib.md5(im.tobytes()).hexdigest()
        if key in s.cache: return s.cache[key]
        img=np.asarray(im.convert('RGB').resize((WW,WH),Image.NEAREST),np.float32)/255
        img=img*SOFT[0]
        sat=img.max(2)-img.min(2); br=np.clip(img-0.86,0,1)*(sat[...,None]>0.15)
        bq=Image.fromarray((np.clip(br*3,0,1)*255).astype('uint8')).resize((WW//4,WH//4),Image.BILINEAR).filter(ImageFilter.GaussianBlur(3.5))
        bl=np.asarray(bq.resize((WW,WH),Image.BILINEAR),np.float32)/255
        img=np.clip(img+bl*s.bloom,0,1)
        if s.k is not None:
            blur=np.asarray(Image.fromarray((img*255).astype('uint8')).filter(ImageFilter.GaussianBlur(5)),np.float32)/255
            img=img*(1-s.k)+blur*s.k
        if len(s.cache)>6: s.cache.clear()
        s.cache[key]=img; return img
    def frame(s,t):
        global RAYS
        if RAYS is None: RAYS=[_rays(2*math.pi*i/24) for i in range(24)]
        ri=int(t*6)%24
        if s.static and ri in s.baked: out=s.baked[ri].copy()
        else: out=s._bg(t,ri)
        return s._finish(out,t)
    def _bg(s,t,ri):
        if s.static and 'world' in s.baked: im=s.baked['world']
        else:
            with WIDE():
                sc=Scene(); s.world(sc,t)
            im=sc.im
            if s.static: s.baked['world']=im
        img=s.grade(im)+RAYS[ri]*(0.85 if s.static else (0.85+0.15*math.sin(t*1.7)))
        for (ft,fx,fy) in s.flash:
            tj=t-ft
            if 0<=tj<0.9:
                f=math.exp(-tj*4); cx,cy=fx*S4,fy*S4
                y0,y1=max(0,cy-500),min(WH,cy+500); x0,x1=max(0,cx-500),min(WW,cx+500)
                yy,xx=np.ogrid[y0:y1,x0:x1]; g=np.exp(-((xx-cx)**2+(yy-cy)**2)/(2*(60+tj*260)**2))
                img=img.copy(); img[y0:y1,x0:x1]+=(g*f*0.9)[...,None]*np.array([0.85,0.95,1.0],np.float32)
        img=np.clip(img*_VIG,0,1)
        out=Image.fromarray((img*255).astype('uint8')).convert('RGBA')
        if s.static and not s.flash: s.baked[ri]=out.copy()
        return out
    def _finish(s,out,t):
        if s.parts:
            glow=Image.new('RGBA',(WW//4,WH//4),(0,0,0,0)); gd=ImageDraw.Draw(glow); dr=ImageDraw.Draw(out)
            for p in s.parts:
                y=(p['y']-p['v']*t)%200+30; x=p['x']+3*math.sin(t*1.3+p['ph']); tw_=0.55+0.45*math.sin(t*3+p['ph'])
                X,Y=int(x)*S4,int(y)*S4
                gd.ellipse((X//4-2,Y//4-2,X//4+3,Y//4+3),fill=p['c']+(int(70*tw_),)); dr.rectangle((X,Y,X+3,Y+3),fill=p['c']+(int(255*tw_),))
            out=Image.alpha_composite(out,glow.filter(ImageFilter.GaussianBlur(1.5)).resize((WW,WH),Image.BILINEAR))
        z=1+s.push*clamp(t/s.dur)
        if z>1.001:
            cw,ch=WW/z,WH/z; x0=(WW-cw)/2; y0=(WH-ch)*0.4
            out=out.resize((WW,WH),Image.BILINEAR,box=(x0,y0,x0+cw,y0+ch))
        with WIDE():
            ui=Scene(); s.ui(ui,t)
        out=Image.alpha_composite(out,ui.ui.resize((WW,WH),Image.NEAREST))
        return out.convert('RGB')
# ---------------------------------------------------------------- wide grass stage
SIDE_TREES=[(22,84,12),(70,110,11),(16,138,12),(66,170,11),(24,206,12),(80,236,10),(8,256,11),
            (404,82,11),(458,104,12),(414,136,12),(466,160,11),(402,192,12),(452,222,11),(420,252,12),(472,250,10)]
def side_world(seed,paths=(),avoid=(),flowers=((44,150,3),(424,170,3))):
    def f(sc,t):
        sc.grass(seed,0,LH)
        for (x0,x1,y,r,kind,sd) in paths: sc.path([(x0,y),(x1,y)],r,kind,seed=sd,smooth=False)
        ys=[p[2] for p in paths]+list(avoid)
        for i,(x,y,r) in enumerate(SIDE_TREES):
            if all(abs(y-py)>r+10 for py in ys): sc.tree(x,y,r,seed+i)
        for (x,y,n) in flowers:
            if all(abs(y-py)>12 for py in ys): sc.flowerbed(x,y,n)
    return f
def full_path(y,r,kind='dirt',sd=1): return [(-6,DX+12,y,r,kind,sd),(DX+258,486,y,r,kind,sd)]
def stage(world_v,bg):
    cache={}
    def f(scw,t):
        with V():
            STAGE['on']=True; STAGE['defer']=[]
            scv=Scene(); r=world_v(scv,t); scv=r or scv
            STAGE['on']=False; deferred=list(STAGE['defer'])
        if 'bg' not in cache:
            bg(scw,t); cache['bg']=scw.im.copy()
        else: scw.im.paste(cache['bg'])
        scw.im.paste(scv.im.crop((0,0,270,LH)),(DX,0))
        for (x,y,r_,sd) in deferred: scw.tree(x+DX,y,r_,sd)
    return f
def clear(im,box): ImageDraw.Draw(im).rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=(0,0,0,0))
def stage_ui(ui_v,moves=(),title_box=(0,0,184,51),dialog_box=(0,244,270,308),dlg_to=(208,0),shift_all=False):
    def f(uiw,t):
        with V():
            s=Scene(); ui_v(s,t); L=s.ui
        if shift_all: uiw.ui.alpha_composite(L.crop((0,0,270,LH)),(DX,0)); return
        rest=L.copy(); pieces=[]
        for box,dst in list(moves)+[(title_box,title_box[:2]),(dialog_box,dlg_to)]:
            pieces.append((L.crop(box),dst)); clear(rest,box)
        uiw.ui.alpha_composite(rest.crop((0,0,270,LH)),(DX,0))
        for p,dst in pieces: uiw.ui.alpha_composite(p,dst)
    return f
# ---------------------------------------------------------------- B shots
def k4_world(sc,t):
    tj=t-k4_anim.T_FILL[1]
    off=-int(round(4*math.sin(math.pi*tj/0.5))) if 0<=tj<0.5 else (-1 if int(t*2.5)%2 else 0)
    w=k4_anim.build_world(off); burst(w.d,t,k4_anim.T_FILL[1],186,140,n=10)
    return w
def k4_ui(sc,t): sc.ui.alpha_composite(k4_anim.ui_layer(t))
def _cfg(name):
    B=bscenes.SCENES
    if name=='K4': return dict(w=k4_world,u=k4_ui,bg=side_world(21),flash=[(k4_anim.T_FILL[1],186,136)],push=0.03)
    if name=='K5':
        def bg(sc,t):
            d=sc.d; px=sc.px; HZ=150; top=(150,190,240); bot=(226,238,250)
            for y in range(HZ):
                tt=y/HZ; bd=int(tt*8); f=tt*8-bd; c0=lerpc(top,bot,bd/8); c1=lerpc(top,bot,(bd+1)/8)
                d.line([(0,y),(LW,y)],fill=c0)
                if f>0.5:
                    for x in range(LW):
                        if ((x+y)%2==0 if f<0.75 else not (x%2 and y%2)): px[x,y]=c1+(255,)
            sc.grass(5,HZ,LH)
            for x in range(0,LW,7): r=4+(x*13)%3; d.ellipse((x-r,HZ-r-2,x+r,HZ+r-2),fill=(96,150,96))
            for x in range(3,LW,7): r=3+(x*7)%3; d.ellipse((x-r,HZ-r+1,x+r,HZ+r+1),fill=(80,134,84))
            d.line([(0,HZ+3),(LW,HZ+3)],fill=(100,156,84))
            for (cx,cy,w_) in [(36,60,30),(392,40,26),(436,112,20)]:
                for k in range(0,w_,8): r=6+(k*7)%4; d.ellipse((cx+k-r,cy-r+2,cx+k+r,cy+r+2),fill=(214,224,244))
                for k in range(0,w_,8): r=6+(k*7)%4; d.ellipse((cx+k-r,cy-r,cx+k+r,cy+r-1),fill=(255,255,255))
            sc.path([(-6,214),(DX+12,214)],6,'dirt',seed=2,smooth=False)
            for i,(x,y,r) in enumerate([(30,180,11),(70,240,10),(420,190,12),(462,236,11),(400,250,10),(10,236,11)]): sc.tree(x,y,r,i+80)
            sc.flowerbed(440,166,3)
        return dict(w=B['K5']['world'],u=B['K5']['ui'],bg=bg,flash=[(8.0,210+DX,96)],push=0.03,moves=[((146,50,268,72),(DX+146,122))])
    if name=='K6': return dict(w=B['K6']['world'],u=B['K6']['ui'],bg=side_world(31,full_path(192,7,'dirt',6)),flash=[(f[0],f[1]+DX,f[2]) for f in B['K6']['flash']],push=0.03)
    if name in('K7','K7b'):
        def bg(sc,t):
            side_world(3,full_path(bscenes.RY7,7.2,'dirt',7),avoid=(190,))(sc,t)
            d=sc.d   # continue the little fence that runs off the left edge
            for fx in range(DX-40,DX+2,8): d.rectangle((fx,184,fx+2,196),fill=INK); d.rectangle((fx+1,185,fx+1,195),fill=(196,146,96))
            d.rectangle((DX-42,187,DX,189),fill=INK); d.line([(DX-42,188),(DX,188)],fill=(214,166,112)); d.rectangle((DX-42,192,DX,194),fill=INK); d.line([(DX-42,193),(DX,193)],fill=(214,166,112))
        return dict(w=B['K7']['world'],u=B['K7']['ui'],bg=bg,flash=[(f[0],f[1]+DX,f[2]) for f in B['K7']['flash']],push=0.03,moves=[((184,4,268,78),(394,64))])
    if name=='K9': return dict(w=B['K9']['world'],u=B['K9']['ui'],bg=side_world(41),flash=[(f[0],f[1]+DX,f[2]) for f in B['K9']['flash']],push=0.03)
    if name=='K12': return dict(w=B['K12']['world'],u=B['K12']['ui'],bg=side_world(51,full_path(200,7,'dirt',8)),flash=[],push=0.03)
    if name=='K13': return dict(w=B['K13']['world'],u=B['K13']['ui'],bg=side_world(61,full_path(206,7,'dirt',9)),flash=[(f[0],f[1]+DX,f[2]) for f in B['K13']['flash']],push=0.03)
    if name=='S':
        return dict(w=summary.SUMMARY['world'],u=summary.SUMMARY['ui'],bg=side_world(71,[(-6,DX+12,224,6,'dirt',11)]),flash=[],push=0.02,shift_all=True)
_B={}
BDUR={'K4':8.1,'K5':10.0,'K6':12.8,'K7':22,'K7b':22,'K9':12.5,'K12':6.5,'K13':11.5,'S':3.1}
def banim16(name):
    if name not in _B:
        c=_cfg(name)
        u=stage_ui(c['u'],moves=c.get('moves',()),shift_all=c.get('shift_all',False))
        _B[name]=WAnim(stage(c['w'],c['bg']),u,push=c['push'],dur=BDUR[name],flash=c['flash'])
    return _B[name]
def b_frame(name,lt): return banim16(name).frame(16.5+lt if name=='K7b' else lt)
# ---------------------------------------------------------------- A / C background
def meadow(sc,t):
    sc.grass(41,0,LH)
    sc.path([(-6,236),(90,230),(200,238),(320,230),(486,236)],8,'dirt',seed=9)
    for i,(tx,ty,r) in enumerate([(10,12,13),(44,2,11),(150,6,11),(236,10,12),(476,30,12),(470,90,11),(6,70,11),(4,140,12),(474,160,12),(250,262,12),(120,262,11),(380,264,12),(60,258,11),(470,250,11)]):
        sc.tree(tx,ty,r,i+40)
    sc.flowerbed(110,14,4); sc.flowerbed(190,22,3); sc.flowerbed(330,8,4)
BOARD=(20,25,336,225)
def a_ui(sc,t): window(sc.ui,BOARD)
def c_ui(sc,t):
    m,b=c_mood(t); x,y=398,186
    bob=-1 if int(t*2.5)%2 else 0
    if m=='happy': bob=-int(abs(math.sin(t*6))*3)
    u=sc.u; u.ellipse((x+4,y+38,x+56,y+46),fill=(90,140,70,150)); acards.mascot(sc.ui,x,y+bob,3,blink=(int(t*10)%37==0))
    if b:
        w=tw(b)+10; bx,by=min(x+30-w//2,474-w),y-24
        u.rectangle((bx,by,bx+w,by+16),fill=INK); u.rectangle((bx+1,by+1,bx+w-1,by+15),fill=(255,255,255))
        u.polygon([(x+24,by+16),(x+32,by+16),(x+28,by+21)],fill=INK); text(u,(bx+5,by+2),b,INK)
    if m=='happy':
        for i,(sx,sy) in enumerate([(x-4,y+6),(x+64,y+30),(x+56,y-4)]):
            if int(t*6+i)%3: u.point([(sx,sy-2),(sx,sy-1),(sx-2,sy),(sx-1,sy),(sx+1,sy),(sx+2,sy),(sx,sy+1),(sx,sy+2)],fill=(255,240,160))
A_BG=WAnim(meadow,a_ui,static=True); C_BG=WAnim(meadow,c_ui,static=True)
C_BG.baked=A_BG.baked   # same meadow
# ---------------------------------------------------------------- A: pixel board content (drawn on a 205x128 grid, x6)
CW,CH,KB=205,128,6
MUTE=(150,116,96)
def cv():
    im=Image.new('RGBA',(CW,CH),(0,0,0,0)); d=ImageDraw.Draw(im); d.fontmode='1'; return im,d
def chip(d,x,y,n,lab,col):
    nw=tw(n)+8; w=tw(lab)+nw+10
    d.rectangle((x,y,x+w,y+18),fill=INK); d.rectangle((x+1,y+1,x+w-1,y+17),fill=lerpc(col,(255,255,255),.82))
    d.rectangle((x+1,y+1,x+nw,y+17),fill=col); text(d,(x+5,y+2),n,(255,255,255)); text(d,(x+nw+5,y+2),lab,INK)
def el_head(s,col=MUTE):
    im,d=cv()
    if (tw(s)+4)*2<=CW-4: bigtext(im,(2,0),s,col,scale=2)   # big header: the board is not empty while chips wait for their cue
    else: text(d,(2,2),s,col)
    return im
def el_tag(s,sub,col=OR):
    im,d=cv(); w=tw(s)+10; d.rectangle((2,2,2+w,18),fill=INK); d.rectangle((3,3,1+w,17),fill=col); text(d,(7,3),s,(255,255,255)); text(d,(w+10,3),sub,MUTE); return im
def el_big(s,y,col=INK,scale=3,x=2):
    while scale>2 and (tw(s)+4)*scale>CW-x-2: scale-=1
    im,_=cv(); bigtext(im,(x,y),s,col,scale=scale); return im
def el_chip(i,n,lab,col,y0=40,step=26):
    im,d=cv(); chip(d,2,y0+i*step,n,lab,col); return im
def el_title():
    im,_=cv()
    t1=Image.new('RGBA',(CW,CH),(0,0,0,0)); bigtext(t1,(0,0),'Git',OR,scale=3,shadow=(150,60,40))
    t2=Image.new('RGBA',(CW,CH),(0,0,0,0)); bigtext(t2,(0,0),'vs',MUTE,scale=2)
    t3=Image.new('RGBA',(CW,CH),(0,0,0,0)); bigtext(t3,(0,0),'GitHub',PURPLE,scale=3,shadow=(80,60,140))
    t1,t2,t3=[x.crop(x.getbbox()) for x in (t1,t2,t3)]
    tot=t1.width+t2.width+t3.width+12; x=(CW-tot)//2; y=44
    im.alpha_composite(t1,(x,y)); x+=t1.width+6; im.alpha_composite(t2,(x,y+t1.height-t2.height)); x+=t2.width+6; im.alpha_composite(t3,(x,y))
    return im
def qmark(d,x,y,col):
    rows=[".ooo.","o...o","....o","...o.","..o..",".....","..o.."]
    for j,r in enumerate(rows):
        for i,ch in enumerate(r):
            if ch=='o': d.rectangle((x+3*i,y+3*j,x+3*i+2,y+3*j+2),fill=col)
def el_q(x,y,col,t):
    im,d=cv(); fy=y+int(round(math.sin(t*4+x)*1.5))
    for dx in (-1,0,1):
        for dy in (-1,0,1): qmark(d,x+dx,fy+dy,INK)
    qmark(d,x,fy,col); return im
def el_follow():
    im,d=cv(); bx,by=2,82
    d.rectangle((bx,by,bx+98,by+30),fill=INK); d.rectangle((bx+1,by+1,bx+97,by+29),fill=OR); d.line([(bx+1,by+1),(bx+97,by+1)],fill=(250,160,120))
    bigtext(im,(bx+14,by+2),'★关注',(255,255,255),scale=2); return im
def el_choice(opts,sel):
    im,d=cv()
    for i,o in enumerate(opts):
        y=30+i*26
        if i==sel: d.polygon([(2,y+3),(2,y+15),(8,y+9)],fill=OR); bigtext(im,(14,y-2),o,OR,scale=2)
        else: bigtext(im,(14,y-2),o,INK,scale=2)
    return im
# sections shown when no overlay is active (what the board says between beats)
SECTIONS=[(0,'Git vs GitHub',None),(61.73,'第1招','存档'),(116.67,'第2招','分支'),(161.97,'GitHub','光有 Git 还不够'),
          (197.33,'GitHub','推上去之后'),(270.63,'GitHub','开源必选项'),(280.93,'今天就到这','')]
def board_els(t):
    """[(lowres element, appear time)] for the board at time t."""
    if t<13.33: return [(el_title(),0.08)]
    if t<17.53: return [(el_title(),0)]
    if t<20.93:
        return [(el_head('零基础、文科生'),17.53),(el_big('一头雾水',40,INK,3),17.53),(el_big('?',40,OR,3,x=150),17.8)]+\
               [(el_q(x,y,c,t),17.53+d_) for (x,y,c,d_) in [(150,92,OR,0.35),(178,96,PURPLE,0.6),(124,100,BLUE,0.85)]]
    if t<24.53: return [(el_head('别怕'),20.93),(el_big('一点都不复杂',40,INK,3),21.0)]
    if t<35.5:
        return [(el_head('今天 3 分钟讲清楚'),24.53)]+[(el_chip(i,n,lab,col),ts) for i,(n,lab,col,ts) in enumerate(CH_TOC)]
    return overlay_els(t)
def overlay_els(t):
    # the vertical A overlays, rebuilt big for the board
    O=[(53.60,58.30,'chip','GitHub 就像',[('1','云端网盘',PURPLE,53.75),('2','多人协作',BLUE,55.35)]),
       (58.40,61.70,'chip','接下来',[('?','怎么用 Git',OR,59.8)]),
       (74.40,79.55,'chip','Git 两个好用的地方',[('1','存档',OR,76.9),('2','分支',GREEN,78.3)]),
       (79.75,84.05,'badge','第1招','存档',OR),
       (90.15,97.45,'chip','需要存很多版本的时候',[('1','迭代网站',OR,91.2),('2','写小说',PINK,93.7),('3','写长文档',BLUE,95.0)]),
       (120.0,128.30,'badge','第2招','分支',GREEN),
       (128.60,131.10,'chip','比如',[('1','设计',OR,128.7),('2','配色',PINK,130.0)]),
       (144.60,147.60,'chip','三条支线 · 三套配色',[('A','蓝',BLUE,144.9),('B','粉',PINK,145.3),('C','绿',GREEN,145.7)]),
       (156.50,161.90,'choice','剧情怎么走？',['留下','离开','反转']),
       (197.40,203.20,'chip','推到 GitHub 之后',[('1','云端备份',PURPLE,200.7),('2','部署上线',OR,201.3),('3','多人协作',BLUE,201.9)]),
       (217.45,223.60,'chip','推到 GitHub 之后',[('1','云端备份',PURPLE,217.45),('2','部署上线',OR,218.8)]),
       (236.60,250.30,'chip','推到 GitHub 之后',[('3','多人协作',BLUE,237.4),('↓','别人下载来改',GREEN,245.9)]),
       (270.70,277.85,'chip','想把项目开源？',[('!','推到 GitHub 是必选项',PURPLE,275.2)]),
       (282.33,999,'end',285.17)]
    for o in O:
        a,b,kind=o[0],o[1],o[2]
        if not (a<=t<b): continue
        if kind=='chip': return [(el_head(o[3]),a)]+[(el_chip(i,n,lab,col),ts) for i,(n,lab,col,ts) in enumerate(o[4])]
        if kind=='badge': return [(el_tag(o[3],'Git',o[5]),a),(el_big(o[4],34,INK,5),a+0.1)]
        if kind=='choice':
            sel=int(max(0,t-a-0.6)*1.6)%len(o[4]); return [(el_head(o[3]),a),(el_choice(o[4],sel),a+0.1)]
        if kind=='end': return [(el_head('更多 Agent 实用教程'),a),(el_big('下期见～',30,INK,3),a+0.1),(el_follow(),o[3])]
    sec=[s for s in SECTIONS if s[0]<=t][-1]
    if sec[0]==0: return [(el_title(),0)]
    if sec[2] is None or sec[2]=='': return [(el_big(sec[1],40,INK,3),sec[0])]
    col=GREEN if sec[1]=='第2招' else (PURPLE if sec[1]=='GitHub' else OR)
    return [(el_tag(sec[1],'Git' if '招' in sec[1] else '',col),sec[0]),(el_big(sec[2],34,INK,4),sec[0])]
CH_TOC=[('1','是什么',OR,26.2),('2','有什么用',BLUE,28.53),('3','怎么用',GREEN,31.7)]
BX0,BY0=(BOARD[0]+5)*S4,(BOARD[1]+5)*S4
def draw_board(out,t):
    els=board_els(t); boxes=[e.getbbox() for e,_ in els if e.getbbox()]
    top=min(b[1] for b in boxes); bot=max(b[3] for b in boxes); lft=min(b[0] for b in boxes); rgt=max(b[2] for b in boxes)
    oy=((BOARD[3]-BOARD[1]-10)*S4-(bot-top)*KB)//2-top*KB-8   # centre the block on the board
    ox=((BOARD[2]-BOARD[0]-10)*S4-(rgt-lft)*KB)//2-lft*KB-16
    for el,ts in els:
        if t<ts: continue
        bb=el.getbbox()
        if not bb: continue
        k=eob((t-ts)/0.35)
        piece=el.crop(bb); w,h=piece.width*KB,piece.height*KB; piece=piece.resize((w,h),Image.NEAREST)
        cx,cy=BX0+(bb[0]+bb[2])*KB//2+16+ox,BY0+(bb[1]+bb[3])*KB//2+8+oy
        if k<0.999: piece=piece.resize((max(1,int(w*k)),max(1,int(h*k))),Image.NEAREST)
        out.alpha_composite(piece,(cx-piece.width//2,cy-piece.height//2))
# ---------------------------------------------------------------- person card (3:4, no frame)
CROP=(135,0,945,1080)
PC_A=(1484,420,360); PC_C=(1568,48,312)
_SH={}
def person(out,src,x,y,w):
    h=w*4//3; r=20
    key=(x,y,w)
    if key not in _SH:
        sh=Image.new('L',(WW,WH),0); ImageDraw.Draw(sh).rounded_rectangle((x,y+10,x+w,y+h+10),r,fill=90)
        m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),r,fill=255)
        if len(_SH)>40: _SH.clear()
        _SH[key]=(sh.filter(ImageFilter.GaussianBlur(16)),m)
    sh,m=_SH[key]
    out.paste((40,70,30),(0,0),sh)
    out.paste(src.crop(CROP).resize((w,h),Image.LANCZOS),(x,y),m)
def lerp_pc(a,b,k): return tuple(int(round(a[i]+(b[i]-a[i])*k)) for i in range(3))
# ---------------------------------------------------------------- C: agent cards (vertical kit, upscaled x5 on the left)
def c_entry(t):
    for cid,a,b,hl in ccards.SCHED:
        if a<=t<b: return cid,a,b,hl
    return ccards.SCHED[-1]
def c_mood(t):
    cid,a,b,hl=c_entry(t); blocks,bub=ccards.C[cid]; mood,tx=bub[0][1],bub[0][2]
    for tb,m,x in bub:
        if t>=tb: mood,tx=m,x
    return mood,tx
from types import SimpleNamespace
def card_img(t):
    cid,a,b,hl=c_entry(t); blocks,_=ccards.C[cid]
    typing=(hl[1],hl[2]) if isinstance(hl,tuple) else None; hls=[] if typing else hl
    enter=1.0 if (a in ccards.FIRST or cid in ccards.NOSLIDE) else clamp((t-a)/0.22)
    with V():
        if cid in ccards.SHOTS:
            shot=ccards.shot_img(cid,t,hls)
            title=[bl for bl in blocks if bl[0]=='title']
            lay=Image.new('RGBA',(270,360),(0,0,0,0)); fk=SimpleNamespace(ui=lay,u=ImageDraw.Draw(lay)); fk.u.fontmode='1'
            y=6
            if title: y=acards.render_blocks(fk,title[:1],t)
            tl=lay.crop(lay.getbbox()) if title else None
            return ('shot',tl,shot,enter)
        lay=Image.new('RGBA',(270,360),(0,0,0,0)); fk=SimpleNamespace(ui=lay,u=ImageDraw.Draw(lay)); fk.u.fontmode='1'
        acards.render_blocks(fk,blocks,t,hls,typing)
    return ('pix',lay.crop(lay.getbbox()),None,enter)
CARD_X,CARD_Y0,CARD_Y1,CARD_WMAX=40,40,930,1460
def draw_card(out,t):
    kind,lo,shot,enter=card_img(t)
    if kind=='pix':
        k=max(3,min(5,(CARD_Y1-CARD_Y0)//lo.height,CARD_WMAX//lo.width))
        im=lo.resize((lo.width*k,lo.height*k),Image.NEAREST)
    else:
        # title bar (x5) + real screenshot in a wood frame, sized to fit
        tl=None; th=0   # the chat window already names the project; the space goes to the screenshot
        sw=1300; sh_=shot.height*sw/shot.width
        if sh_>CARD_Y1-CARD_Y0-th-40: sh_=CARD_Y1-CARD_Y0-th-40; sw=shot.width*sh_/shot.height
        sw,sh_=int(sw),int(sh_)
        fw,fh=-(-(sw+40)//4),-(-(sh_+40)//4)
        fr=Image.new('RGBA',(fw,fh),(0,0,0,0)); window(fr,(0,0,fw-1,fh-1)); fr=fr.resize((fw*4,fh*4),Image.NEAREST)
        fr.paste(shot.convert('RGB').resize((sw,sh_),Image.LANCZOS),((fw*4-sw)//2,(fh*4-sh_)//2))
        im=Image.new('RGBA',(max(fr.width,tl.width if tl is not None else 0),fr.height+th),(0,0,0,0))
        if tl is not None: im.alpha_composite(tl,(0,0))
        im.alpha_composite(fr,(0,th))
    y=CARD_Y0+(CARD_Y1-CARD_Y0-im.height)//2+int(round((1-smooth(enter))*40))
    if enter<1:
        a=np.asarray(im).copy(); a[...,3]=(a[...,3]*smooth(enter)).astype(np.uint8); im=Image.fromarray(a)
    out.alpha_composite(im,(CARD_X,max(CARD_Y0-20,y)))
# ---------------------------------------------------------------- subtitles (zh + en)
ZH=ImageFont.truetype(os.path.join(FONTS,'SourceHanSansSC-Heavy.otf'),50)
EN=ImageFont.truetype(os.path.join(FONTS,'Inter-SemiBold.otf'),34)
CUES=[tuple(c) for c in json.load(open(os.path.join(HERE,'cues_bi.json')))]
_SUB={}
def sub_layer(i):
    if i not in _SUB:
        if len(_SUB)>8: _SUB.clear()
        a,b,zh,en=CUES[i]; im=Image.new('RGBA',(WW,170),(0,0,0,0)); d=ImageDraw.Draw(im)
        d.text((WW//2,56),zh,font=ZH,fill=(255,255,255),anchor='mm',stroke_width=6,stroke_fill=(0,0,0))
        d.text((WW//2,110),en,font=EN,fill=(255,255,255),anchor='mm',stroke_width=5,stroke_fill=(0,0,0))
        _SUB[i]=im
    return _SUB[i]
def subs(out,t):
    for i,c in enumerate(CUES):
        if c[0]<=t<c[1]: out.alpha_composite(sub_layer(i),(0,930)); return
# ---------------------------------------------------------------- timeline (same as 3:4 final-v3)
SEG=[('A0',0,3.0),('C',3.0,13.33),('Az',13.33,20.93),('At',20.93,35.5),('B:K4',35.5,43.62),('B:K5',43.62,53.60),
 ('A',53.60,61.73),('C',61.73,74.30),('A',74.30,84.10),('C',84.10,90.10),('A',90.10,97.57),('B:K6',97.57,110.33),
 ('C',110.33,116.67),('A',116.67,131.13),('B:K7',131.13,144.57),('A',144.57,147.63),('B:K7b',147.63,152.80),
 ('A',152.80,164.33),('B:K9',164.33,176.80),('C',176.80,197.33),('A',197.33,203.27),('C',203.27,217.40),
 ('A',217.40,223.63),('C',223.63,236.57),('Ap',236.57,250.33),('B:K12',250.33,256.77),('B:K13',256.77,268.20),
 ('C',268.20,270.63),('Ap2',270.63,277.87),('B:S',277.87,280.93),('A',280.93,999)]
def seg_at(t):
    for i,(k,a,b) in enumerate(SEG):
        if a<=t<b: return i
    return len(SEG)-1
GRID=24; ORDER=np.random.default_rng(3).random((WH//GRID,WW//GRID))
def mosaic(im,b): return im if b<=1 else im.resize((WW//b,WH//b),Image.BILINEAR).resize((WW,WH),Image.NEAREST)
def dissolve(a,b,p):
    a2=mosaic(a,int(1+p*30)); b2=mosaic(b,int(1+(1-p)*30))
    m=np.kron((ORDER<p).astype(np.uint8)*255,np.ones((GRID,GRID),np.uint8))
    return Image.composite(b2,a2,Image.fromarray(m))
def pc_pos(i,t):
    """person card (x,y,w) for segment i, with a 0.35s glide between the A and C positions."""
    k,a,b=SEG[i]; home=PC_C if k=='C' else PC_A
    if i>0:
        pk=SEG[i-1][0]; prev=PC_C if pk=='C' else (PC_A if pk[0]=='A' or pk=='B:S' else None)
        if prev and prev!=home and t-a<0.35: return lerp_pc(prev,home,smooth((t-a)/0.35))
        if prev is None and t-a<0.45:   # coming out of a B shot: slide in from the right
            q=eob((t-a-0.1)/0.35,1.2); return (home[0]+int((1-q)*(WW-home[0]+20)),home[1],home[2])
    return home
def base(i,t,src):
    k,a,b=SEG[i]
    if k.startswith('B:'):
        f=b_frame(k[2:],t-a)
        if k=='B:S': person(f,src,*pc_pos(i,t))
        return f
    if k=='C':
        out=C_BG.frame(t).convert('RGBA'); draw_card(out,t)
        cid,ca,cb,_=c_entry(t)
        if t-a<0.35 and i>0:
            prev=base(i-1,t,src); kk=eob((t-a)/0.35,1.4)
            bg=Image.blend(prev,Image.new('RGB',(WW,WH),(30,24,28)),0.45)
            cw,ch=max(2,int(WW*(0.55+0.45*kk))),max(2,int(WH*(0.55+0.45*kk)))
            bg.paste(out.convert('RGB').resize((cw,ch),Image.BICUBIC),((WW-cw)//2,(WH-ch)//2)); out=bg
        else: out=out.convert('RGB')
        person(out,src,*pc_pos(i,t)); return out
    out=A_BG.frame(t).convert('RGBA'); draw_board(out,t); out=out.convert('RGB')
    person(out,src,*pc_pos(i,t)); return out
def render(t,src):
    i=seg_at(t); k,a,b=SEG[i]; out=base(i,t,src)
    if k.startswith('B:') and t-a<0.3 and i>0:
        out=dissolve(base(i-1,t,src),out,(t-a)/0.3)
    if i>0 and SEG[i-1][0].startswith('B:') and not k.startswith('B:') and k!='C' and t-a<0.3:
        out=dissolve(base(i-1,t,src),out,(t-a)/0.3)
    out=out.convert('RGBA'); subs(out,t); return out.convert('RGB')
def src_at(t):
    raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',SRC,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    return Image.frombytes('RGB',(1080,1440),raw)
if __name__=='__main__':
    if sys.argv[1]=='--still':
        OUT=sys.argv[2]
        for j,tt in enumerate(sys.argv[3:]):
            t=float(tt); render(t,src_at(t)).save(OUT.replace('%',str(tt)) if '%' in OUT else OUT)
        sys.exit()
    OUT=sys.argv[1]; T0=float(sys.argv[2]); T1=float(sys.argv[3])
    n0=int(round(T0*FPS)); n1=int(round(T1*FPS)); SW,SH=1080,1440
    dec=subprocess.Popen(['ffmpeg','-v','error','-ss',f'{n0/FPS:.4f}','-i',SRC,'-frames:v',str(n1-n0),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{WW}x{WH}','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',OUT],stdin=subprocess.PIPE)
    for fi in range(n0,n1):
        raw=dec.stdout.read(SW*SH*3)
        if len(raw)<SW*SH*3: break
        t=fi/FPS
        enc.stdin.write(render(t,Image.frombytes('RGB',(SW,SH),raw)).tobytes())
        if (fi-n0)%150==0: print(f'{t:.1f}s',flush=True)
    enc.stdin.close(); enc.wait(); dec.kill(); print('done',flush=True)
