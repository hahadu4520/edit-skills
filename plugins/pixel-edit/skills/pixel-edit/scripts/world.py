from assets import *
import numpy as np
from PIL import ImageFilter
GR=(118,174,90); GD=(98,152,76); GL=(150,198,108); GDD=(84,134,68)
OR=(232,98,62); BLUE=(96,150,216); PINK=(236,120,156); GREEN=(92,176,118); PURPLE=(140,110,210)
DIRT=(220,184,128); DIRTE=(176,132,86); DIRTH=(236,206,156); PEB=(198,160,108)
STONE=(232,222,200); STONEE=(170,156,134); STONEH=(248,242,226)
WHITE=(255,255,255)
class Scene:
    def __init__(s,bg=GR):
        s.im,s.d=new(bg); s.px=s.im.load()
        s.ui=Image.new('RGBA',(W,H),(0,0,0,0)); s.u=ImageDraw.Draw(s.ui); s.u.fontmode='1'
    def grass(s,seed=3,y0=0,y1=H):
        rnd=random.Random(seed); px=s.px; d=s.d
        d.rectangle((0,y0,W,y1),fill=GR)
        for _ in range(int(520*(y1-y0)/H)):
            x,y=rnd.randrange(W),rnd.randrange(y0,y1); c=rnd.random()
            pts=[(0,0),(2,0),(1,1)] if c<.55 else ([(0,0),(1,-1)] if c<.85 else [(0,0)])
            col=GD if c<.55 else (GL if c<.85 else GDD)
            for dx,dy in pts:
                if 0<=x+dx<W and y0<=y+dy<y1: px[x+dx,y+dy]=col+(255,)
        for _ in range(int(30*(y1-y0)/H)):
            x,y=rnd.randrange(6,W-6),rnd.randrange(y0+3,y1-3); c=rnd.choice([(255,240,150),(255,206,214),(255,255,255),(200,220,255)])
            for (dx,dy) in [(0,-1),(-1,0),(1,0),(0,1)]: px[x+dx,y+dy]=c+(255,)
            px[x,y]=(236,170,60,255)
    def path(s,pts,r,kind='dirt',seed=1,smooth=True):
        p=catmull(pts,12) if smooth and len(pts)>2 else pts
        m=dist_mask(p,r)
        cols={'dirt':(DIRT,DIRTE,DIRTH,(PEB,.08)),'stone':(STONE,STONEE,STONEH,(STONEE,.06)),
              'pink':((248,214,222),(206,140,160),(255,236,240),((224,170,186),.07))}[kind]
        paint_mask(s.im,m,*cols,seed)
    def tree(s,x,y,r=11,seed=0):
        d,px=s.d,s.px; rr=random.Random(seed)
        LEAF=(70,140,78); LD=(50,108,64); LH=(112,180,96); LHH=(150,206,120)
        d.ellipse((x-r+2,y+r-3,x+r+2,y+r+4),fill=(84,130,66))
        d.rectangle((x-2,y+r-6,x+2,y+r+2),fill=INK); d.rectangle((x-1,y+r-6,x+1,y+r+1),fill=(130,88,58))
        d.ellipse((x-r-1,y-r-1,x+r+1,y+r-1),fill=INK); d.ellipse((x-r,y-r,x+r,y+r-2),fill=LEAF)
        for yy in range(y-r,y+r-1):
            for xx in range(x-r,x+r+1):
                if 0<=xx<W and 0<=yy<H and px[xx,yy][:3]==LEAF:
                    v=(xx-x)*.6+(yy-y)
                    if v>r*.45: px[xx,yy]=LD+(255,)
                    elif v<-r*.55: px[xx,yy]=LH+(255,)
        for _ in range(6):
            a=rr.uniform(3.6,5.2); k=rr.uniform(.35,.7); cx,cy=int(x+math.cos(a)*r*k),int(y+math.sin(a)*r*k)
            for (dx,dy) in [(0,0),(1,0),(0,1),(-1,0)]:
                if 0<=cx+dx<W and 0<=cy+dy<H: px[cx+dx,cy+dy]=LHH+(255,)
    def house(s,x,y,roof,dim=False,smoke=True,wall=(252,240,216)):
        d,px=s.d,s.px
        wallS=lerpc(wall,(150,120,90),.25); timber=(136,92,62)
        r0=roof; rD=lerpc(roof,(40,30,50),.32); rH=lerpc(roof,(255,255,255),.35)
        def C(c): return lerpc(c,(176,176,168),.55) if dim else c
        d.rectangle((x+2,y+40,x+44,y+43),fill=(84,130,66))
        d.rectangle((x+3,y+18,x+41,y+40),fill=INK); d.rectangle((x+4,y+19,x+40,y+39),fill=C(wall)); d.rectangle((x+4,y+36,x+40,y+39),fill=C(wallS))
        for tx in (x+4,x+40): d.line([(tx,y+19),(tx,y+39)],fill=C(timber))
        d.line([(x+4,y+19),(x+40,y+19)],fill=C(timber))
        d.rectangle((x+17,y+26,x+27,y+40),fill=INK); d.rectangle((x+18,y+27,x+26,y+40),fill=C(rD))
        d.line([(x+22,y+27),(x+22,y+40)],fill=C(lerpc(rD,(0,0,0),.25))); px[x+24,y+34]=C((250,214,110))+(255,)
        for wx in (x+7,x+31):
            d.rectangle((wx,y+24,wx+7,y+31),fill=INK); d.rectangle((wx+1,y+25,wx+6,y+30),fill=C((150,206,236)))
            d.line([(wx+1,y+25),(wx+3,y+25)],fill=C((230,246,255))); d.line([(wx+1,y+27),(wx+6,y+27)],fill=INK); d.line([(wx+3,y+25),(wx+3,y+30)],fill=INK)
            d.rectangle((wx,y+32,wx+7,y+33),fill=C(r0)); d.point([(wx+2,y+31),(wx+5,y+31)],fill=C((255,170,190)))
        d.polygon([(x,y+20),(x+6,y+2),(x+38,y+2),(x+44,y+20)],fill=INK); d.polygon([(x+1,y+19),(x+7,y+3),(x+37,y+3),(x+43,y+19)],fill=C(r0))
        for ry in range(y+6,y+19,4):
            d.line([(x+2+(y+19-ry)//3,ry),(x+42-(y+19-ry)//3,ry)],fill=C(rD))
            for k in range(x+6,x+40,6): px[k+((ry//4)%2)*3,ry-1]=C(rD)+(255,)
        d.line([(x+7,y+3),(x+37,y+3)],fill=C(rH)); d.line([(x+7,y+4),(x+36,y+4)],fill=C(rH)); d.line([(x+1,y+19),(x+43,y+19)],fill=C(rD))
        d.rectangle((x+31,y-4,x+37,y+5),fill=INK); d.rectangle((x+32,y-3,x+36,y+5),fill=C((200,120,96))); d.line([(x+32,y-3),(x+36,y-3)],fill=C((226,160,130)))
        if smoke and not dim:
            for k,(sx,sy) in enumerate([(x+34,y-8),(x+37,y-12),(x+35,y-16)]):
                d.ellipse((sx-1-k//2,sy-1-k//2,sx+1+k//2,sy+1+k//2),fill=(248,248,248))
    def crystal(s,cx,cy,big=2):
        d,px=s.d,s.px
        CR=["....o....","...oLo...","..oLlCo..",".oLlCCCo.","oLlCCCCDo",".oCCCCDo.","..oCCDo..","...oDo...","....o...."]
        CRb=[''.join(c*big for c in r) for r in CR for _ in range(big)]
        n=9*big; sprite(s.im,cx-n//2,cy-n//2,CRb,{'o':INK,'L':(255,255,255),'l':(210,240,255),'C':(110,190,240),'D':(70,130,200)})
        for (sx,sy) in [(cx-n//2-4,cy-2),(cx+n//2+3,cy+2),(cx+n//2,cy-n//2-2)]:
            d.point([(sx,sy-1),(sx-1,sy),(sx+1,sy),(sx,sy+1)],fill=(255,252,200)); px[sx,sy]=(255,255,255,255)
    def sign(s,x,y,t):
        d=s.d; w=tw(t)+8
        d.rectangle((x+w//2-1,y+12,x+w//2+1,y+22),fill=INK); d.line([(x+w//2,y+12),(x+w//2,y+21)],fill=(150,104,66))
        d.rectangle((x,y,x+w,y+13),fill=INK); d.rectangle((x+1,y+1,x+w-1,y+12),fill=(196,146,96)); d.line([(x+1,y+1),(x+w-1,y+1)],fill=(226,180,126)); d.line([(x+1,y+12),(x+w-1,y+12)],fill=(150,104,66))
        text(d,(x+4,y),t,(255,246,226))
    def flowerbed(s,x,y,n=5,cols=((255,120,140),(255,220,110),(255,255,255))):
        d=s.d
        d.rectangle((x,y,x+n*6+2,y+6),fill=INK); d.rectangle((x+1,y+1,x+n*6+1,y+5),fill=(150,100,70))
        for i in range(n):
            c=cols[i%len(cols)]; fx=x+3+i*6
            d.point([(fx,y-1),(fx-1,y),(fx+1,y),(fx,y+1)],fill=c); d.point((fx,y),fill=(240,180,60)); d.point((fx,y+2),fill=(80,150,70))
    def sparkle(s,x,y,c=(255,252,210)):
        d=s.d; d.point([(x,y-2),(x,y-1),(x-2,y),(x-1,y),(x+1,y),(x+2,y),(x,y+1),(x,y+2)],fill=c); d.point((x,y),fill=(255,255,255))
    def shadow(s,x,y,w=16):
        s.d.ellipse((x,y,x+w,y+4),fill=(84,130,66))
# --- generic drawing helpers (work on any draw) ---
def label(d,x,y,t,col):
    d.rectangle((x,y,x+13,y+13),fill=INK); d.rectangle((x+1,y+1,x+12,y+12),fill=col)
    d.line([(x+1,y+1),(x+12,y+1)],fill=lerpc(col,(255,255,255),.35)); d.line([(x+1,y+12),(x+12,y+12)],fill=lerpc(col,(0,0,0),.3))
    text(d,(x+4,y),t,(255,255,255))
def tag(d,x,y,t,col,point=None,fg=(255,255,255)):
    w=tw(t)+8
    d.rectangle((x,y,x+w,y+14),fill=INK); d.rectangle((x+1,y+1,x+w-1,y+13),fill=col); d.line([(x+1,y+13),(x+w-1,y+13)],fill=lerpc(col,(0,0,0),.25))
    if point=='up': d.polygon([(x+w//2-3,y),(x+w//2+3,y),(x+w//2,y-4)],fill=INK)
    if point=='down': d.polygon([(x+w//2-3,y+14),(x+w//2+3,y+14),(x+w//2,y+18)],fill=INK)
    text(d,(x+4,y+1),t,fg); return w
def bubble(d,x,y,t,tail='down'):
    w=tw(t)+10
    d.rectangle((x,y,x+w,y+17),fill=INK); d.rectangle((x+1,y+1,x+w-1,y+16),fill=(255,255,255)); d.line([(x+1,y+16),(x+w-1,y+16)],fill=(214,206,214))
    if tail=='down':
        d.polygon([(x+8,y+17),(x+14,y+17),(x+10,y+22)],fill=INK); d.polygon([(x+9,y+16),(x+13,y+16),(x+10,y+20)],fill=(255,255,255))
    text(d,(x+5,y+2),t,INK); return w
def uiwindow(img,b,**k): window(img,b,**k)
def title_card(sc,num,title,sub,b=(6,6,178,48)):
    u=sc.u; window(sc.ui,b)
    x0,y0=b[0],b[1]
    w=tw(num)+8
    u.rectangle((x0+8,y0+7,x0+8+w,y0+21),fill=INK); u.rectangle((x0+9,y0+8,x0+7+w,y0+20),fill=OR); u.line([(x0+9,y0+8),(x0+7+w,y0+8)],fill=(250,150,110))
    text(u,(x0+12,y0+7),num,(255,255,255)); text(u,(x0+w+14,y0+7),sub,(150,116,96))
    text(u,(x0+8,y0+24),title,INK)
def dialog(sc,lines,name='du',portrait=None,b=(6,248,264,302),opts=None):
    u=sc.u; window(sc.ui,b); x0,y0,x1,y1=b
    tx=x0+10
    if portrait is not False:
        u.rectangle((x0+7,y0+7,x0+42,y0+46),fill=INK); u.rectangle((x0+8,y0+8,x0+41,y0+45),fill=(196,226,150))
        rows,pal=(PORT,PORT_PAL) if portrait is None else portrait
        sprite(sc.ui,x0+9,y0+14,rows[:32],pal); u.rectangle((x0+8,y0+8,x0+41,y0+45),outline=INK)
        tx=x0+50
        u.rectangle((tx-4,y0+4,tx-4+tw(name)+10,y0+16),fill=INK); u.rectangle((tx-3,y0+5,tx-5+tw(name)+10,y0+15),fill=OR); text(u,(tx+1,y0+4),name,(255,255,255))
    for i,l in enumerate(lines):
        if isinstance(l,tuple): text(u,(tx,y0+20+i*14),l[0],l[1])
        else: text(u,(tx,y0+20+i*14),l,INK)
    u.polygon([(x1-12,y1-8),(x1-6,y1-8),(x1-9,y1-5)],fill=OR)
def prompt_card(sc,b,label_txt,msg_lines):
    # pixel chat input: what to type to the agent
    u=sc.u; x0,y0,x1,y1=b
    u.rectangle((x0+3,y0+3,x1+3,y1+3),fill=(40,30,50,120))
    u.rectangle(b,fill=INK); u.rectangle((x0+1,y0+1,x1-1,y1-1),fill=(52,44,70))
    u.rectangle((x0+1,y0+1,x1-1,y0+13),fill=(74,62,100))
    for k,c in enumerate([(240,96,96),(250,200,90),(110,200,120)]): u.rectangle((x0+5+k*7,y0+5,x0+9+k*7,y0+9),fill=c)
    text(u,(x0+28,y0+1),label_txt,(214,206,240))
    for i,l in enumerate(msg_lines): text(u,(x0+8,y0+18+i*14),l,(255,255,255))
    cy=y0+18+len(msg_lines)*14-14
    u.rectangle((x1-38,y1-18,x1-6,y1-5),fill=INK); u.rectangle((x1-37,y1-17,x1-7,y1-6),fill=OR); text(u,(x1-34,y1-18),'发送',(255,255,255))
# villagers: palette variants of GIRL / a short-hair BOY
BOY=[
"................",
"....oooooooo....",
"...oHHHHHHHHo...",
"..oHHHhhHHHHHo..",
"..oHHhHHHHHhHo..",
"..oHSSSSSSSSHo..",
"..oSSSSSSSSSSo..",
"..oSeSSSSSSeSo..",
"..oSeSSSSSSeSo..",
"..oSrSSSSSSrSo..",
"..oSSSSssSSSSo..",
"...ooSSSSSSoo...",
"..oBBoSSSSoBBo..",
".oBBBBBBBBBBBBo.",
".oBBBBBBBBBBBBo.",
".oBcBBBBBBBBcBo.",
".oSoBBBBBBBBoSo.",
".oooBBBBBBBBooo.",
"...obbbbbbbbo...",
"...oPPPooPPPo...",
"...oPPPooPPPo...",
"...oPPo..oPPo...",
"...oKKo..oKKo...",
"...ooo....ooo...",
]
def pal_variant(hair,shirt,pants=(74,64,80)):
    p=dict(GIRL_PAL_H); p['H']=hair; p['h']=lerpc(hair,(255,255,255),.25)
    p['B']=shirt; p['b']=lerpc(shirt,(0,0,0),.25); p['c']=lerpc(shirt,(255,255,255),.5); p['T']=lerpc(shirt,(255,255,255),.35); p['t']=shirt; p['P']=pants
    return p
V1=(BOY,pal_variant((120,72,44),(90,140,210)))
V2=(GIRL_H,pal_variant((200,120,60),(236,150,90)))
V3=(BOY,pal_variant((40,40,48),(110,180,120)))
def person(img,x,y,v=None,flip=False):
    rows,pal=(GIRL,GIRL_PAL) if v is None else v
    sprite(img,x,y,rows,pal,flip)
def hd2d(sc,path,focus=0.45,band=0.20,mood='golden',rays=True,bloom=0.5):
    S_=4; mp=sc.im.convert('RGB')
    big=mp.resize((W*S_,H*S_),Image.NEAREST)
    img=np.array(big).astype(np.float32)/255; HH,WW=img.shape[:2]
    yy,xx=np.mgrid[0:HH,0:WW]; t=(xx/WW*0.45+yy/HH*0.55)
    if mood=='golden': warm=np.stack([1.10-0.22*t,1.03-0.15*t,0.90-0.02*t],2); rc=np.array([0.30,0.24,0.12])
    elif mood=='day': warm=np.stack([1.04-0.12*t,1.04-0.10*t,1.0-0.02*t],2); rc=np.array([0.22,0.22,0.18])
    elif mood=='dusk': warm=np.stack([1.0-0.25*t,0.92-0.25*t,1.0-0.1*t],2); rc=np.array([0.26,0.16,0.20])
    img=img*warm
    if rays:
        ang=np.arctan2(yy+200,xx+260); r_=np.zeros((HH,WW),np.float32)
        for c,w in [(0.62,0.035),(0.78,0.05),(0.93,0.03),(1.06,0.045)]: r_+=np.exp(-((ang-c)/w)**2)*0.9
        r_*=np.clip(1-(np.sqrt((xx+260)**2+(yy+200)**2)/1700),0,1)
        r_=np.array(Image.fromarray((np.clip(r_,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(18))).astype(np.float32)/255
        img=img+r_[...,None]*rc
    sat=img.max(2)-img.min(2)
    br=np.clip(img-0.86,0,1)*(sat[...,None]>0.15)
    bl=np.array(Image.fromarray((np.clip(br*3,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
    img=np.clip(img+bl*bloom,0,1)
    blur=np.array(Image.fromarray((img*255).astype('uint8')).filter(ImageFilter.GaussianBlur(5))).astype(np.float32)/255
    k=np.clip((np.abs(yy/HH-focus)-band)/0.12,0,1)[...,None]
    img=img*(1-k)+blur*k
    r=np.sqrt(((xx-WW/2)/(WW/2))**2+((yy-HH*0.45)/(HH/1.6))**2)
    img=img*np.clip(1.08-0.32*r**2,0.55,1.1)[...,None]
    out=Image.fromarray((np.clip(img,0,1)*255).astype('uint8')).convert('RGBA')
    rnd=random.Random(4); glow=Image.new('RGBA',out.size,(0,0,0,0)); gd=ImageDraw.Draw(glow); dr=ImageDraw.Draw(out)
    for _ in range(34):
        x=rnd.randrange(0,W)*S_; y=rnd.randrange(50,240)*S_; c=rnd.choice([(255,236,170),(255,214,226),(255,250,220)])
        gd.ellipse((x-10,y-10,x+14,y+14),fill=c+(70,)); dr.rectangle((x,y,x+S_-1,y+S_-1),fill=c+(255,))
    out=Image.alpha_composite(out,glow.filter(ImageFilter.GaussianBlur(6)))
    out=Image.alpha_composite(out,sc.ui.resize((W*S_,H*S_),Image.NEAREST)).convert('RGB')
    g=ImageDraw.Draw(out,'RGBA')
    for x in range(150,930,24):
        g.line([(x,1225),(x+12,1225)],fill=(255,255,255,170),width=2); g.line([(x,1321),(x+12,1321)],fill=(255,255,255,170),width=2)
    out.save(path); return out
