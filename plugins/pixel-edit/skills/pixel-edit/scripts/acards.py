# C shots v3: the agent app itself, drawn with the same pixel UI kit as the B-roll
# (wood-frame windows, RPG dialog boxes with portraits, tags), plus a pixel agent mascot.
from banim import *
from pcards import seg, Lay, merge_rects
HLC=(255,226,72); MUTE=(150,116,96); UB=(52,44,70)
# original pixel mascot: a small orange agent critter
MASCOT=[
".....oooooooooo.....",
"...ooHHHHHHHHHHoo...",
"..oHHhhOOOOOOOOOOo..",
"..oHhOOOOOOOOOOOOo..",
".oOOOOOOOOOOOOOOOOo.",
".oOOOOewOOOOOOewOOo.",
"ooOOOOeeOOOOOOeeOOoo",
"oSoOOOeeOOOOOOeeOoSo",
"oSoOOPPOOOmmOOOPPoSo",
".ooOOOOOOOOOOOOOOoo.",
"..oOOOOOOOOOOOOOOo..",
"..oDDDDDDDDDDDDDDo..",
"...oDDo.oDo.oDo.oDo.".ljust(20,'.'),
"...ooo..ooo.ooo.ooo.".ljust(20,'.'),
]
MASCOT=[r[:20].ljust(20,'.') for r in MASCOT]
MP={'o':INK,'O':(226,116,80),'H':(244,150,112),'h':(255,206,170),'e':INK,'w':(255,255,255),'S':(210,100,68),'m':(140,56,44),'P':(250,150,150),'D':(186,84,56)}
MASCOT_BLINK=[(r.replace('ee','OO').replace('ew','oo') if i in (5,7) else (r.replace('ew','oo') if i==6 else r)) for i,r in enumerate(MASCOT)]
def mascot(img,x,y,s=1,blink=False,flip=False):
    rows=MASCOT_BLINK if blink else MASCOT
    if s>1: rows=[''.join(c*s for c in r) for r in rows for _ in range(s)]
    sprite(img,x,y,rows,MP,flip)
def box(img,b,fill=(255,246,226)): window(img,b,fill=fill)
def portrait(u,img,x,y,who):
    u.rectangle((x,y,x+35,y+39),fill=INK); u.rectangle((x+1,y+1,x+34,y+38),fill=(196,226,150) if who=="du" else (255,232,214))
    if who=='du': sprite(img,x+2,y+7,PORT[:32],PORT_PAL)
    elif who=='friend':
        rows,pal=V1; rows=[''.join(c*2 for c in r) for r in rows[:14] for _ in (0,1)]; sprite(img,x+2,y+10,rows,pal)
    else: mascot(img,x+8,y+14)
    u.rectangle((x+1,y+1,x+34,y+38),outline=INK)
def nametag(u,x,y,name,col):
    w=tw(name)+10; u.rectangle((x,y,x+w,y+12),fill=INK); u.rectangle((x+1,y+1,x+w-1,y+11),fill=col); text(u,(x+5,y),name,(255,255,255))
def draw_ops(u,img,L,t,hl,dy=0,typing_end=None):
    for op in L.ops:
        if op[0]=='box':
            _,x0,y0,x1,y1,f,o=op
            if o: u.rectangle((x0,y0+dy,x1,y1+dy),fill=o); u.rectangle((x0+1,y0+1+dy,x1-1,y1-1+dy),fill=f)
            else: u.rectangle((x0,y0+dy,x1,y1+dy),fill=f)
        elif op[0]=='line': u.line([(op[1],op[2]+dy),(op[3],op[2]+dy)],fill=op[4])
    lit=set()
    for key,ht in hl:
        p=smooth((t-ht)/0.28)
        if p<=0: continue
        lit.add(key)
        for (x0,y0,x1,y1) in merge_rects(L.rects.get(key,[])):
            xe=int(x0-2+(x1-x0+4)*p); u.rectangle((x0-2,y0+1+dy,xe,y1+dy),fill=HLC)
    for op in L.ops:
        k=op[0]
        if k=='t': text(u,(op[1],op[2]+dy),op[3],INK if (len(op)>5 and op[5] in lit) else op[4])
        elif k=='bigc': bigtext(img,(op[1],op[2]+dy-2),op[3],op[4],scale=2)
        elif k=='check': x,y=op[1],op[2]+dy; u.line([(x,y+4),(x+2,y+6),(x+6,y+1)],fill=(70,150,90),width=2)
        elif k=='dots':
            x,y=op[1],op[2]+dy
            for j in range(3):
                if int(op[3]*6)%4>j: u.rectangle((x+j*4,y,x+j*4+1,y+1),fill=MUTE)
        elif k=='icon': draw_icon(u,img,op[1],op[2]+dy,op[3])
        elif k=='caret':
            if typing_end is None or t<typing_end or int(t*2.5)%2==0: u.rectangle((op[1],op[2]+2+dy,op[1]+2,op[2]+26+dy),fill=OR)
class Stack:
    """vertical stack of B-style UI blocks."""
    def __init__(s,y=54): s.y=y; s.items=[]
def draw_icon(u,img,x,y,ic):
    if ic=='check': u.line([(x+1,y+5),(x+3,y+7),(x+8,y+2)],fill=(70,150,90),width=2)
    elif ic=='dir': u.rectangle((x,y+2,x+9,y+9),fill=INK); u.rectangle((x+1,y+3,x+8,y+8),fill=(240,196,96)); u.rectangle((x,y+1,x+4,y+2),fill=INK)
    elif ic=='file': u.rectangle((x+1,y,x+8,y+9),fill=INK); u.rectangle((x+2,y+1,x+7,y+8),fill=(255,255,255)); u.line([(x+3,y+3),(x+6,y+3)],fill=MUTE); u.line([(x+3,y+5),(x+6,y+5)],fill=MUTE)
    elif ic=='floppy': sprite(img,x,y,FLOPPY,floppy_pal((120,150,200)))
    elif ic[0]=='tile':
        u.rectangle((x-1,y-1,x+10,y+10),fill=INK); u.rectangle((x,y,x+9,y+9),fill=ic[2]); text(u,(x+2,y-2),ic[1],(255,255,255))
def btn(u,x1,y,label,fill,fg=(255,255,255)):
    w=tw(label)+10; u.rectangle((x1-w,y,x1,y+13),fill=INK); u.rectangle((x1-w+1,y+1,x1-1,y+12),fill=fill); u.line([(x1-w+1,y+1),(x1-1,y+1)],fill=lerpc(fill,(255,255,255),.3))
    text(u,(x1-w+5,y),label,fg); return x1-w
def render_blocks(sc,blocks,t,hl=(),typing=None,full=False):
    u=sc.u; img=sc.ui; y=6
    for b in blocks:
        k=b[0]
        if k=='title':   # app header: mascot logo instead of any product wording
            x0,y0=6,y; window(img,(x0,y0,200,y0+40))
            u.rectangle((x0+8,y0+6,x0+31,y0+21),fill=INK); u.rectangle((x0+9,y0+7,x0+30,y0+20),fill=(255,232,214))
            mascot(img,x0+10,y0+7)
            text(u,(x0+38,y0+7),b[3],MUTE); text(u,(x0+8,y0+24),b[2],INK); y+=48
        elif k in ('you','agent'):
            who='du' if k=='you' else 'Claude'
            L=Lay(); L.y=y+18; x0=50
            for part in b[1]:
                if isinstance(part,str): L.text_flow(seg(part),x0,254); L.y+=2
                elif part[0]=='term':
                    y0=L.y; L.y+=4
                    for ln in part[1]: L.text_flow(seg(ln),x0+5,252,(232,226,244),(255,236,150))
                    L.ops.insert(0,('box',x0,y0,254,L.y+2,(43,38,52),None)); L.y+=6
                elif part[0]=='link':
                    y0=L.y; L.y+=3; L.text_flow(seg(part[1]),x0+16,250)
                    L.ops.insert(0,('box',x0,y0,254,L.y+2,(255,255,255),(214,196,170))); L.ops.append(('box',x0+4,y0+4,x0+12,y0+12,(36,41,47),None)); L.y+=6
                elif part[0]=='checks':   # optional reveal: ('checks', items, t0, dt)
                    for i,c in enumerate(part[1]):
                        if len(part)>2 and not full and t<part[2]+i*part[3]:
                            (L.ops.append(('dots',x0,L.y+6,t)) if t>=part[2]+(i-1)*part[3] else None); L.y+=15; continue
                        L.ops.append(('check',x0,L.y+3)); L.text_flow(seg(c),x0+10,254)
                elif part[0]=='bar':      # progress bar: ('bar', label, frac0, frac1, t0, t1)
                    _,lab,f0,f1,ta,tb=part; f=f1 if full else f0+(f1-f0)*smooth((t-ta)/(tb-ta))
                    L.ops.append(('box',x0,L.y+2,254,L.y+11,(230,214,196),INK)); L.ops.append(('box',x0+1,L.y+3,x0+1+int(202*f),L.y+10,(110,190,120),None))
                    L.y+=14; L.text_flow(seg(lab.format(n=int(round(f*20)))),x0,254,MUTE); L.y+=2
            h=max(L.y-y+4,50)
            box(img,(6,y,264,y+h))
            spk=(b[2] if len(b)>2 else 'du') if k=='you' else 'bot'
            portrait(u,img,13,y+7,spk)
            nametag(u,50,y+4,{'du':'du','friend':'朋友','bot':'Agent'}[spk],{'du':OR,'friend':BLUE,'bot':(222,112,78)}[spk])
            draw_ops(u,img,L,t,hl)
            y+=h+6
        elif k=='prompt':
            ptxt=b[1]; N=sum(len(x) for x,_ in seg(ptxt))
            n=N if typing is None else int(round(N*clamp((t-typing[0])/(typing[1]-typing[0]))))
            L=Lay(); L.y=y+20
            x,yy=L.text_flow(seg(ptxt),16,254,(255,255,255),(200,180,255),n=n,sc=2,lh=28)
            if typing is not None: L.ops.append(('caret',x+1,yy))
            h=max(L.y-y+24,96)
            u.rectangle((9,y+3,267,y+h+3),fill=(40,30,50,120))
            u.rectangle((6,y,264,y+h),fill=INK); u.rectangle((7,y+1,263,y+h-1),fill=UB)
            u.rectangle((7,y+1,263,y+13),fill=(74,62,100))
            for kk,c in enumerate([(240,96,96),(250,200,90),(110,200,120)]): u.rectangle((11+kk*7,y+5,15+kk*7,y+9),fill=c)
            text(u,(34,y+1),b[2],(214,206,240))
            u.rectangle((224,y+h-18,258,y+h-5),fill=INK); u.rectangle((225,y+h-17,257,y+h-6),fill=OR); text(u,(229,y+h-18),'发送',(255,255,255))
            draw_ops(u,img,L,t,hl,typing_end=typing[1] if typing else None)
            y+=h+8
        elif k=='slots':   # save-slot list like the B-roll HUD
            rows=b[2]; h=22+len(rows)*17
            box(img,(6,y,264,y+h)); text(u,(16,y+5),b[1],INK)
            L=Lay()
            for i,(v,lab,when,cur) in enumerate(rows):
                yy=y+21+i*17
                u.rectangle((14,yy,256,yy+14),fill=INK); u.rectangle((15,yy+1,255,yy+13),fill=(255,216,176) if cur else (250,236,214))
                sprite(img,17,yy+3,FLOPPY,floppy_pal(OR if cur else (120,150,200)))
                text(u,(29,yy+1),v,OR if cur else (130,100,84))
                L.y=yy+1; L.text_flow(seg(lab),47,210)
                text(u,(254-tw(when),yy+1),when,(170,140,120))
            draw_ops(u,img,L,t,hl)
            y+=h+6
        elif k=='rows':   # generic panel: dict(head, sub, rows=[(icon,label,right)], reveal=(t0,dt), btn=(label,fill))
            P=b[1]; L=Lay(); L.y=y+6; yy=y+6
            if P.get('head'): L.ops.append(('t',16,yy,P['head'],INK)); yy+=15
            if P.get('sub'): L.y=yy; L.text_flow(seg(P['sub']),16,254,MUTE); yy+=15
            yy+=2; rv=P.get('reveal')
            for i,(ic,lab,right) in enumerate(P['rows']):
                hid=rv and not full and t<rv[0]+i*rv[1]
                L.ops.append(('box',14,yy,256,yy+15,(250,236,214),INK))
                if hid:
                    if t>=rv[0]+(i-1)*rv[1]: L.ops.append(('dots',22,yy+7,t))
                else:
                    L.ops.append(('icon',19,yy+3,ic)); L.y=yy+1; L.text_flow(seg(lab),33,200)
                    if right:
                        if isinstance(right,str):
                            segs=seg(right); w=sum(tw(a) for a,_ in segs); L.y=yy+1; L.text_flow(segs,252-w,256,(170,140,120))
                        else:   # ('btn', label, fill, fg) -- label may carry [hl] markup
                            segs=seg(right[1]); w=sum(tw(a) for a,_ in segs)+10
                            L.ops.append(('box',252-w,yy+1,252,yy+14,right[2],INK)); L.y=yy+1; L.text_flow(segs,257-w,256,right[3])
                yy+=18
            if P.get('btn'):
                lab,fill=P['btn']; segs=seg(lab); w=sum(tw(a) for a,_ in segs)+12
                L.ops.append(('box',256-w,yy+2,256,yy+17,fill,INK)); L.y=yy+3; L.text_flow(segs,262-w,262,(255,255,255)); yy+=20
            h=yy-y+4; box(img,(6,y,264,y+h)); draw_ops(u,img,L,t,hl); y+=h+6
        elif k=='diff':   # dict(head, sub, lines=[(sign,text)])
            P=b[1]; L=Lay(); yy=y+6
            if P.get('head'): L.ops.append(('t',16,yy,P['head'],INK)); yy+=15
            if P.get('sub'): L.ops.append(('t',16,yy,P['sub'],MUTE)); yy+=15
            y0=yy+2; yy=y0+4
            for sg,ln in P['lines']:
                bgc={'-':(92,44,56),'+':(40,84,60)}.get(sg)
                if bgc: L.ops.append(('box',15,yy-1,255,yy+13,bgc,None))
                L.y=yy; L.text_flow(seg(ln),20,252,{'-':(255,170,170),'+':(170,240,180)}.get(sg,(220,214,232)),(255,236,150)); yy+=15
            L.ops.insert(0,('box',14,y0,256,yy+3,(43,38,52),None)); yy+=6
            h=yy-y+2; box(img,(6,y,264,y+h)); draw_ops(u,img,L,t,hl); y+=h+6
        elif k=='page':   # a little website in a browser-ish panel: dict(url, narrow)
            P=b[1]; nar=P.get('narrow'); x0,x1=(62,208) if nar else (6,264); h=160 if nar else 136
            box(img,(x0,y,x1,y+h))
            L=Lay(); u.rectangle((x0+6,y+5,x1-6,y+18),fill=INK); u.rectangle((x0+7,y+6,x1-7,y+17),fill=(255,255,255))
            L.y=y+6; L.text_flow(seg(P['url']),x0+12,x1-8,(110,90,80))
            px0,py0=x0+6,y+22; px1,py1=x1-6,y+h-6
            u.rectangle((px0,py0,px1,py1),fill=(255,236,240)); u.rectangle((px0,py0,px1,py0+5),fill=PINK)
            bigtext(img,(px0+8,py0+14),"Hi, I'm",(70,44,40),scale=2); bigtext(img,(px0+8,py0+40),'du.',(70,44,40),scale=2)
            text(u,(px0+8,py0+68),'AI tools for creators.',(130,96,86)) if not nar else text(u,(px0+8,py0+68),'AI tools for',(130,96,86))
            by=py0+(104 if nar else 88); bw=tw('Get started')+8; u.rectangle((px0+8,by,px0+8+bw,by+13),fill=INK); u.rectangle((px0+9,by+1,px0+7+bw,by+12),fill=OR); text(u,(px0+12,by),'Get started',(255,255,255))
            if not nar:
                for k2 in range(3): u.rectangle((px1-62+k2*20,py0+20,px1-48+k2*20,py0+48),fill=lerpc(PINK,(255,255,255),.4+k2*.15))
            draw_ops(u,img,L,t,hl); y+=h+6
        elif k=='toast':
            L=Lay(); segs=seg(b[1]); w=sum(tw(a) for a,_ in segs)+26; x0=135-w//2
            u.rectangle((x0,y,x0+w,y+17),fill=INK); u.rectangle((x0+1,y+1,x0+w-1,y+16),fill=(222,244,228))
            draw_icon(u,img,x0+5,y+4,'check'); L.y=y+2; L.text_flow(segs,x0+18,x0+w,(46,124,74)); draw_ops(u,img,L,t,hl); y+=23
        elif k=='frame':   # wood frame for a real screenshot; the image is pasted at full res by the caller
            box(img,(6,y,264,y+b[1])); FRAMES.append(y); y+=b[1]+6
        elif k=='gap': y+=b[1]
    return y
def bg_world(sc,t):
    sc.grass(41)
    sc.path([(-6,268),(70,262),(150,270),(220,262),(276,268)],8,'dirt',seed=9)
    for i,(tx,ty,r) in enumerate([(12,14,13),(44,4,11),(240,10,13),(266,40,11),(4,60,11),(262,96,12),(8,128,12),(264,170,11),(6,196,11),(150,300,12),(100,318,11),(196,326,12),(130,352,13),(60,348,11),(236,350,12)]):
        sc.tree(tx,ty,r,i+40)
    sc.flowerbed(110,14,4); sc.flowerbed(176,30,3)
def mascot_layer(sc,t,mood='idle',bubble=None):
    x,y=20,226; bob=-1 if int(t*2.5)%2 else 0
    if mood=='happy': bob=-int(abs(math.sin(t*6))*3)
    u=sc.u
    u.ellipse((x+4,y+38,x+56,y+46),fill=(70,116,58,170))
    mascot(sc.ui,x,y+bob,3,blink=(int(t*10)%37==0))
    if bubble:
        bx,by=x+64,y+2; w=tw(bubble)+10
        u.rectangle((bx,by,bx+w,by+16),fill=INK); u.rectangle((bx+1,by+1,bx+w-1,by+15),fill=(255,255,255))
        u.polygon([(bx,by+10),(bx-6,by+14),(bx,by+14)],fill=INK)
        text(u,(bx+5,by+2),bubble,INK)
    if mood=='happy':
        for i,(sx,sy) in enumerate([(x-4,y+6),(x+64,y+30),(x+56,y-4)]):
            if int(t*6+i)%3:
                u.point([(sx,sy-2),(sx,sy-1),(sx-2,sy),(sx-1,sy),(sx+1,sy),(sx+2,sy),(sx,sy+1),(sx,sy+2)],fill=(255,240,160))
BOTTOM=212
FRAMES=[]; OFF=[0]
_BG=None
def bg():
    global _BG
    if _BG is None: _BG=BAnim(bg_world,lambda sc,t:None,mood='golden',focus=0.45,band=0.6,bloom=0.2,push=0,dur=10,rays=True)
    return _BG
def scene_image(blocks,t,hl=(),typing=None,mood='idle',bubble=None,enter=1.0):
    B=bg()
    def ui(sc,tt):
        # bottom-anchor the stack so it always sits just above the mascot / PiP row
        from types import SimpleNamespace
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); fk=SimpleNamespace(ui=lay,u=ImageDraw.Draw(lay)); fk.u.fontmode='1'
        end=render_blocks(fk,blocks,t,(),None,full=True)-6; FRAMES.clear()
        lay=Image.new('RGBA',(W,H),(0,0,0,0)); fk=SimpleNamespace(ui=lay,u=ImageDraw.Draw(lay)); fk.u.fontmode='1'
        render_blocks(fk,blocks,t,hl,typing)
        if enter<1:
            a=np.asarray(lay).copy(); a[...,3]=(a[...,3]*smooth(enter)).astype(np.uint8); lay=Image.fromarray(a)
        OFF[0]=max(0,BOTTOM-end)+int(round((1-smooth(enter))*10))
        sc.ui.alpha_composite(lay,(0,OFF[0]))
        mascot_layer(sc,t,mood,bubble)
    B.ui=ui
    return B.frame(t)

def shot_scene(shot,t,mood='idle',bubble=None,title=None,enter=1.0):
    """pixel scene with a real (full-res) screenshot inside a wood frame."""
    sw=1000; sh=round(shot.height*sw/shot.width); hl=-(-sh//4)+8
    blocks=([title] if title else [])+[('frame',hl)]
    FRAMES.clear(); f=scene_image(blocks,t,(),None,mood,bubble,enter)
    y=(FRAMES[0]+4+OFF[0])*4
    f.paste(shot.convert('RGB').resize((sw,sh),Image.LANCZOS),(40,y)); return f
