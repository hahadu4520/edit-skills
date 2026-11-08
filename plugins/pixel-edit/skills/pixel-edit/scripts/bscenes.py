# The six remaining pixel B-roll shots, animated. Times are local seconds from each shot's start.
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
from banim import *
CRs=["..o..",".oLo.","oLCDo",".oDo.","..o.."]
CRP={'o':INK,'L':(255,255,255),'C':(110,190,240),'D':(70,130,200)}
CR2=[''.join(c*2 for c in r) for r in CRs for _ in (0,1)]
def walk(x0,x1,t,t0,t1):
    k=smooth((t-t0)/(t1-t0)) if t1>t0 else 1
    return x0+(x1-x0)*k, (t0<t<t1)
def step_bob(moving,t): return -1 if moving and int(t*8)%2 else 0
def ui_title(sc,num,title,sub,t,t0=0.05):
    if t<t0: return
    tmp=Scene(); title_card(tmp,num,title,sub); el=tmp.ui.crop((0,0,W,56))
    a=eob((t-t0)/0.45); dy=int((1-a)*-56)
    if dy<0: el=el.crop((0,-dy,W,56)); dy=0
    sc.ui.alpha_composite(el,(0,dy))
# ---------------- K5 本地 → 云端 (43.70–53.60) ----------------
def k5_world(sc,t):
    d=sc.d; px=sc.px; HZ=150
    top=(150,190,240); bot=(226,238,250)
    for y in range(HZ):
        tt=y/HZ; band=int(tt*8); f=tt*8-band; c0=lerpc(top,bot,band/8); c1=lerpc(top,bot,(band+1)/8)
        d.line([(0,y),(W,y)],fill=c0)
        if f>0.5:
            for x in range(W):
                if ((x+y)%2==0 if f<0.75 else not (x%2 and y%2)): px[x,y]=c1+(255,)
    sc.grass(5,HZ,H)
    for x in range(0,W,7): r=4+(x*13)%3; d.ellipse((x-r,HZ-r-2,x+r,HZ+r-2),fill=(96,150,96))
    for x in range(3,W,7): r=3+(x*7)%3; d.ellipse((x-r,HZ-r+1,x+r,HZ+r+1),fill=(80,134,84))
    d.line([(0,HZ+3),(W,HZ+3)],fill=(100,156,84))
    def puff(x,y,w):
        for k in range(0,w,8): r=6+(k*7)%4; d.ellipse((x+k-r,y-r+2,x+k+r,y+r+2),fill=(214,224,244))
        for k in range(0,w,8): r=6+(k*7)%4; d.ellipse((x+k-r,y-r,x+k+r,y+r-1),fill=(255,255,255))
    puff(14+int(t*1.5),74,26); puff(232-int(t*1.2),96,24)
    CX,CY=170,104+int(round(math.sin(t*1.6)))
    blobs=[(-48,4,14),(-32,-4,18),(-10,-8,20),(14,-6,20),(36,-2,17),(52,6,12),(-22,8,16),(6,10,18),(30,10,15)]
    for bx,by,r in blobs: d.ellipse((CX+bx-r-1,CY+by-r+3,CX+bx+r+1,CY+by+r+4),fill=(176,186,226))
    for bx,by,r in blobs: d.ellipse((CX+bx-r,CY+by-r+1,CX+bx+r,CY+by+r+1),fill=(222,228,248))
    for bx,by,r in blobs: d.ellipse((CX+bx-r+2,CY+by-r,CX+bx+r-2,CY+by+r-4),fill=(255,255,255))
    sc.house(CX-22,CY-46,PURPLE,smoke=False)
    ARR=8.0
    for i,cx in enumerate((CX+30,CX+40,CX+50)):
        if t>=ARR+0.15*i: sprite(sc.im,cx-2,CY-10+(i%2)*3,CRs,CRP)
    sc.path([(0,214),(120,214)],6,'dirt',seed=2,smooth=False)
    sc.house(26,166,OR,smoke=False)
    for i in range(3): sprite(sc.im,78+i*8,196+(i%2)*2-(1 if int(t*3+i)%4==0 else 0),CRs,CRP)
    for i,(tx,ty) in enumerate([(12,236),(118,236),(130,170),(258,236)]): sc.tree(tx,ty,10,i+3)
    trail=catmull([(50,158),(58,136),(76,118),(116,104),(134,100)],10)
    F0,F1=5.2,ARR
    p=clamp((t-F0)/(F1-F0))
    n=int(len(trail)*p)
    for i,(x,y) in enumerate(trail[:n]):
        if i%3==0:
            x,y=int(x),int(y); d.rectangle((x-1,y-1,x+1,y+1),fill=(255,226,140)); px[x,y]=(255,255,230,255)
    FOLD=["oooooo..........","oYYYYYo.........","oYYYYYYooooooooo","oyyyyyyyyyyyyyyo","oYYYYYYYYYYYYYYo","oYYYYYYYYYYYYYYo","oYYYYYYYYYYYYYYo","oYYYYYYYYYYYYYYo","oYYYYYYYYYYYYYYo","oDDDDDDDDDDDDDDo","oooooooooooooooo"]
    if t<F1+0.1:
        if t<F0: fx,fy=40,176   # folder rests by the local house
        else:
            q=smooth(p); idx=min(len(trail)-1,int(q*(len(trail)-1))); fx,fy=trail[idx]; fx-=12; fy-=12
        if t>=1.2:
            sprite(sc.im,int(fx),int(fy),FOLD,{'o':INK,'Y':(255,206,96),'y':(255,232,160),'D':(220,160,60)})
            sprite(sc.im,int(fx)+5,int(fy)+4,CRs,CRP)
    if F0<=t<F1:
        for k in range(3): sc.sparkle(int(fx)+8+int(6*math.sin(t*9+k*2)),int(fy)+14+k*4)
    burst(d,t,ARR,CX+40,CY-8)
    for i,(vx,v) in enumerate([(176,V1),(204,V2),(232,V3)]):
        vy=196+(i%2)*6
        sc.shadow(vx,vy+22); person(sc.im,vx,vy+(-1 if t>ARR+0.6 and int(t*4+i)%2 else 0),v)
        if t>=ARR+0.5+0.25*i:
            x0,y0=vx+8,vy-4; x1,y1=CX-20+i*22,CY+16
            nn=int(max(abs(x1-x0),abs(y1-y0))/5); pk=clamp((t-ARR-0.5-0.25*i)/0.5)
            for k in range(1,int(nn*pk)):
                x=round(x0+(x1-x0)*k/nn); y=round(y0+(y1-y0)*k/nn); d.rectangle((x,y,x+1,y+1),fill=(255,255,255))
            HE=[".o.o.","oRoRo","oRRRo",".oRo.","..o.."]
            sprite(sc.im,vx+11,vy-8-int((t*3+i)%2),HE,{'o':INK,'R':(240,90,110)})
def k5_ui(sc,t):
    u=sc.u
    ui_title(sc,'Git vs GitHub','一个存本地，一个传云端','',t)
    pop_into(sc.ui,t,1.2,lambda s:tag(s.u,8,150,'Git：存档在你电脑里',OR,point='down'),(6,148,140,170))
    pop_into(sc.ui,t,4.2,lambda s:tag(s.u,150,52,'GitHub：云端网盘',PURPLE),(148,50,264,68))
    def leg_l(s):
        uu=s.u; window(s.ui,(6,248,264,302))
        uu.rectangle((14,256,22,264),fill=OR); text(uu,(28,254),'Git',INK); text(uu,(28,268),'本地文件夹 + 存档',(110,88,84)); text(uu,(28,282),'只有你能用',(170,140,120))
        uu.line([(134,256),(134,294)],fill=(214,196,170))
    def leg_r(s):
        uu=s.u; uu.rectangle((142,256,150,264),fill=PURPLE); text(uu,(156,254),'GitHub',INK); text(uu,(156,268),'传到云端的网盘',(110,88,84)); text(uu,(156,282),'多人协作、分享',(170,140,120))
    pop_into(sc.ui,t,1.6,leg_l,(6,248,265,303))
    if t>=4.6: leg_r(sc)
K5=dict(world=k5_world,ui=k5_ui,mood='day',focus=0.42,band=0.24,flash=[(8.0,210,96)])
# ---------------- K6 存档时间线 (97.57–110.33) ----------------
K6_V=[1.0,3.75,4.25,4.75]   # V1..V4 appear (cue "V1V2V3V4" at 101.20)
K6_BAD=6.4; K6_PROMPT=9.2; K6_BACK=(10.6,11.9)
def k6_world(sc,t):
    d=sc.d; sc.grass(31); RY=186
    sc.path([(-6,RY+6),(60,RY-2),(130,RY+6),(200,RY-2),(276,RY+6)],7,'dirt',seed=6)
    for i,(tx,ty) in enumerate([(14,226),(46,236),(250,228),(226,240),(130,236),(254,66),(16,62)]): sc.tree(tx,ty,10 if i%2 else 12,i+20)
    xs=[34,98,162,226]
    def thumb(s,x,y,v):
        dd=s.d
        dd.rectangle((x+20,y+34,x+22,y+52),fill=INK); dd.line([(x+21,y+34),(x+21,y+51)],fill=(150,104,66))
        dd.rectangle((x,y,x+42,y+34),fill=INK); dd.rectangle((x+1,y+1,x+41,y+33),fill=(255,252,246))
        col={'V1':(190,190,190),'V2':PINK,'V3':BLUE,'V4':(200,90,90)}[v]
        dd.rectangle((x+1,y+1,x+41,y+6),fill=col)
        if v=='V1':
            dd.line([(x+5,y+12),(x+30,y+12)],fill=(210,206,200)); dd.line([(x+5,y+16),(x+24,y+16)],fill=(210,206,200))
        elif v=='V2':
            dd.rectangle((x+5,y+10,x+26,y+13),fill=lerpc(col,(60,40,60),.25)); dd.line([(x+5,y+17),(x+34,y+17)],fill=(210,206,200))
            dd.rectangle((x+5,y+22,x+18,y+28),fill=col); dd.rectangle((x+24,y+21,x+37,y+29),fill=lerpc(col,(255,255,255),.55))
        elif v=='V3':
            dd.rectangle((x+5,y+10,x+26,y+13),fill=lerpc(col,(40,40,60),.25)); dd.line([(x+5,y+17),(x+34,y+17)],fill=(210,206,200))
            for k in range(3): dd.rectangle((x+5+k*12,y+21,x+14+k*12,y+29),fill=lerpc(col,(255,255,255),.5))
        else:
            for k in range(6):
                a=(x+4+k*6,y+10+(k*7)%14); dd.line([a,(a[0]+8,a[1]+9-(k%3)*5)],fill=(200,80,80))
            dd.rectangle((x+8,y+24,x+30,y+28),fill=(230,200,200))
        tcol={'V1':(150,140,130),'V2':OR,'V3':(150,140,130),'V4':(200,80,80)}[v]
        dd.rectangle((x-4,y-8,x+18,y+5),fill=INK); dd.rectangle((x-3,y-7,x+17,y+4),fill=tcol); text(dd,(x,y-8),v,(255,255,255))
    good=t>=K6_BACK[1]
    for i,v in enumerate(['V1','V2','V3','V4']):
        x=xs[i]; y=RY-2+(6 if i%2==0 else -2)-62
        if v=='V2' and good:
            for r,c in [(28,(255,240,196)),(24,(255,248,222))]: d.ellipse((x+21-r,y+17-r,x+21+r,y+17+r),fill=c)
        pop_world(sc,t,K6_V[i],lambda s,x=x,y=y,v=v:thumb(s,x,y,v),(x-5,y-9,x+44,y+54))
    if t>=K6_BAD: pop_world(sc,t,K6_BAD,lambda s:sprite(s.im,xs[3]+22,RY-74,X_BADGE,BADGE_PAL_X),(xs[3]+20,RY-76,xs[3]+40,RY-56))
    if good:
        pop_world(sc,t,K6_BACK[1],lambda s:sprite(s.im,xs[1]+22,RY-82,OK_BADGE,BADGE_PAL_OK),(xs[1]+20,RY-84,xs[1]+40,RY-64))
        for (sx,sy) in [(108,166),(128,170),(124,160),(92,136),(146,130)]:
            if int(t*6+sx)%3: sc.sparkle(sx,sy)
    # girl: walks right to V4 while versions appear, then rewinds to V2
    if t<K6_BACK[0]:
        gx,mv=walk(30,226,t,0.6,5.6); flip=False
    else:
        gx,mv=walk(226,112,t,*K6_BACK); flip=True
    if K6_BACK[0]-0.2<t<K6_BACK[1]+0.3:
        CH=["...oo","..oOo",".oOo.","oOo..",".oOo.","..oOo","...oo"]
        CH2=[''.join(c*2 for c in r) for r in CH for _ in (0,1)]
        for k,x in enumerate((140,152,204,216)):
            if int(t*8+k)%4!=0: sprite(sc.im,x,RY-5,CH2,{'o':INK,'O':OR})
    sc.shadow(int(gx),RY+12); person(sc.im,int(gx),RY-10+step_bob(mv,t),flip=flip)
    burst(d,t,K6_BACK[1],xs[1]+21,RY-50,n=12)
def k6_ui(sc,t):
    ui_title(sc,'第1招','哪版不满意，随时回去','Git · 存档',t)
    if t<K6_PROMPT:
        if t>0.3:
            dialog(sc,typed(['帮我存档！',('V1、V2、V3、V4 都会存下来',(150,116,96))],t,0.3))
    else:
        tmp_k=eob((t-K6_PROMPT)/0.3)
        def pc(s):
            n=int(max(0,t-K6_PROMPT-0.3)*12); prompt_card(s,(6,252,264,300),'对 Agent 说',['回到 V2 那个版本。'[:n]])
        pop_into(sc.ui,t,K6_PROMPT,pc,(6,252,268,304))
K6=dict(world=k6_world,ui=k6_ui,mood='golden',flash=[(K6_BACK[1],119,150)])
# ---------------- K7 开分支 (131.13–144.57) + 合并 (147.63–152.77 → local 16.5+) ----------------
RY7=152; FORK=(52,RY7); MERGE=(222,RY7)
PA=catmull([FORK,(46,128),(58,110),(90,106),(106,106)],12)
PB=catmull([FORK,(78,136),(130,134),(172,134),(204,138),MERGE],12)
PB_IN=[p for p in PB if p[0]<=170]; PB_OUT=[p for p in PB if p[0]>=170]
PC=catmull([FORK,(56,178),(78,206),(124,220),(140,220)],12)
def _pathlayer(pts,r,cols,seed):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); m=dist_mask(pts,r); paint_mask(im,m,*cols,seed=seed)
    P=np.array(pts); a=np.zeros((H,W),np.float32)
    ys,xs=np.nonzero(np.array(m))
    if len(xs):
        dd=(xs[:,None]-P[None,:,0])**2+(ys[:,None]-P[None,:,1])**2; a[ys,xs]=dd.argmin(1)/(len(P)-1)
    return im,a
_STC=(STONE,STONEE,STONEH,(STONEE,.06)); _PKC=((248,214,222),(206,140,160),(255,236,240),((224,170,186),.07))
_L=None
def _layers():
    global _L
    if _L is None:
        _L=dict(A=_pathlayer(PA,4.2,_STC,1),C=_pathlayer(PC,4.2,_STC,2),B=_pathlayer(PB_IN,4.6,_PKC,5),BO=_pathlayer(PB_OUT,4.6,_PKC,6))
    return _L
def _reveal(sc,key,p):
    if p<=0: return
    im,a=_layers()[key]
    if p>=1: sc.im.alpha_composite(im); return
    m=((a<=p)&(np.asarray(im)[...,3]>0)).astype(np.uint8)*255
    sc.im.paste(im,(0,0),Image.fromarray(m))
K7_HOUSES=2.2; K7_OPEN=2.7; K7_P2=16.5   # part 2 starts at local 16.5 (=147.63)
def k7_world(sc,t):
    d=sc.d; px=sc.px; sc.grass(3)
    p2=t-K7_P2
    _reveal(sc,'A',smooth((t-K7_OPEN)/1.6)); _reveal(sc,'C',smooth((t-K7_OPEN-0.3)/1.6)); _reveal(sc,'B',smooth((t-K7_OPEN-0.15)/1.6))
    _reveal(sc,'BO',smooth((p2-3.0)/0.9))
    sc.path([(-4,RY7),(W+4,RY7)],7.2,'dirt',seed=7,smooth=False)
    for i,(tx,ty) in enumerate([(14,70),(30,58),(248,98),(262,120),(240,196),(258,214),(12,222),(30,234),(186,212),(210,228)]): sc.tree(tx,ty,10 if i%2 else 12,i)
    dimA=p2>=0.3; dimC=p2>=0.6
    for key,(hx,hy,col,dim,lab,lx,ly,dl) in dict(A=(84,62,BLUE,dimA,'A',68,84,0),B=(150,92,PINK,False,'B',134,112,0.15),C=(118,174,GREEN,dimC,'C',100,190,0.3)).items():
        def dr(s,hx=hx,hy=hy,col=col,dim=dim,lab=lab,lx=lx,ly=ly):
            s.house(hx,hy,col,dim=dim); label(s.d,lx,ly,lab,col)
        pop_world(sc,t,K7_HOUSES+dl,dr,(lx-1,hy-18,hx+46,max(hy+44,ly+15)))
    if dimA: pop_world(sc,t,K7_P2+0.3,lambda s:sprite(s.im,122,58,X_BADGE,BADGE_PAL_X),(120,56,140,76))
    if dimC: pop_world(sc,t,K7_P2+0.6,lambda s:sprite(s.im,156,170,X_BADGE,BADGE_PAL_X),(154,168,174,188))
    if p2>=1.1: pop_world(sc,t,K7_P2+1.1,lambda s:sprite(s.im,190,80,OK_BADGE,BADGE_PAL_OK),(188,78,208,98))
    for fx in range(2,42,8): d.rectangle((fx,184,fx+2,196),fill=INK); d.rectangle((fx+1,185,fx+1,195),fill=(196,146,96))
    d.rectangle((0,187,36,189),fill=INK); d.line([(0,188),(36,188)],fill=(214,166,112)); d.rectangle((0,192,36,194),fill=INK); d.line([(0,193),(36,193)],fill=(214,166,112))
    for (rx,ry) in [(70,234),(100,238),(150,236)]: d.ellipse((rx,ry,rx+7,ry+5),fill=INK); d.ellipse((rx+1,ry+1,rx+6,ry+4),fill=(176,176,170))
    cx,cy=MERGE[0]+8,RY7-24
    CR=["....o....","...oLo...","..oLlCo..",".oLlCCCo.","oLlCCCCDo",".oCCCCDo.","..oCCDo..","...oDo...","....o...."]
    CRb=[''.join(c*2 for c in r) for r in CR for _ in (0,1)]
    sprite(sc.im,cx-9,cy+int(round(math.sin(t*2))),CRb,{'o':INK,'L':(255,255,255),'l':(210,240,255),'C':(110,190,240),'D':(70,130,200)})
    # main road pulse at "不影响主干" (local 11.24)
    if 11.2<=t<13.4 and int(t*4)%2==0:
        for x in range(4,W-4,10): d.point([(x,RY7),(x+1,RY7)],fill=(255,248,210))
    # sparkles travelling along branches while "三条支线" is said
    if 7.9<=t<11.2:
        for P,off in ((PA,0),(PB_IN,0.33),(PC,0.66)):
            q=((t-7.9)*0.45+off)%1; x,y=P[int(q*(len(P)-1))]; sc.sparkle(int(x),int(y),(255,252,220))
    # merge sparkle runs along B → main
    if 3.0<=p2<4.2:
        q=smooth((p2-3.0)/1.0); P=PB_IN+PB_OUT; x,y=P[int(q*(len(P)-1))]
        for k in range(3): sc.sparkle(int(x)-k*4,int(y)+(k%2))
    burst(d,t,K7_P2+4.0,cx,cy+8,n=12)
    # girl at the fork
    d.ellipse((20,RY7+7,36,RY7+11),fill=(186,148,100))
    sprite(sc.im,20,RY7-14+(-1 if int(t*2.5)%2 else 0),GIRL,GIRL_PAL)
    if t<K7_OPEN+1.5:
        bx,by,bw=6,RY7-40,52
        d.rectangle((bx,by,bx+bw,by+17),fill=INK); d.rectangle((bx+1,by+1,bx+bw-1,by+16),fill=(255,255,255)); d.line([(bx+1,by+16),(bx+bw-1,by+16)],fill=(214,206,214))
        d.polygon([(bx+18,by+17),(bx+24,by+17),(bx+20,by+22)],fill=INK); d.polygon([(bx+19,by+16),(bx+23,by+16),(bx+20,by+20)],fill=(255,255,255))
        text(d,(bx+5,by+2),'试试看!',INK)
def k7_ui(sc,t):
    u=sc.u
    ui_title(sc,'第2招','开分支：同时试 3 套配色','Git · 分支',t)
    def hud(s):
        uu=s.u; window(s.ui,(184,6,264,74)); text(uu,(193,10),'存档栏',INK)
        for i,(v,tt) in enumerate([('V1','首页'),('V2','导航'),('V3','配色')]):
            yy=26+i*15; cur=i==2
            uu.rectangle((192,yy,256,yy+12),fill=INK); uu.rectangle((193,yy+1,255,yy+11),fill=(255,216,176) if cur else (250,236,214))
            sprite(s.ui,195,yy+2,FLOPPY,floppy_pal((232,98,62) if cur else (120,150,200)))
            text(uu,(207,yy),v,(232,98,62) if cur else (130,100,84)); text(uu,(225,yy),tt,INK)
    pop_into(sc.ui,t,0.4,hud,(184,6,265,75))
    pop_into(sc.ui,t,K7_OPEN,lambda s:tag(s.u,30,RY7+12,'开分支',OR,point='up'),(30,RY7+7,80,RY7+27))
    p2=t-K7_P2
    if p2>=3.0: pop_into(sc.ui,t,K7_P2+3.0,lambda s:tag(s.u,190,RY7+12,'合并回主线',(86,170,104),point='up'),(190,RY7+7,262,RY7+27))
    if t>0.3:
        window(sc.ui,(6,248,264,302)); u=sc.u
        u.rectangle((13,255,48,294),fill=INK); u.rectangle((14,256,47,293),fill=(196,226,150))
        sprite(sc.ui,15,262,PORT[:32],PORT_PAL); u.rectangle((14,256,47,293),outline=INK)
        u.rectangle((52,252,78,264),fill=INK); u.rectangle((53,253,77,263),fill=OR); text(u,(57,252),'du',(255,255,255))
        if p2<0: text(u,(56,268),typed(['要试哪套配色？'],t,0.3)[0],INK)
        else: text(u,(56,268),typed(['B 最好看，合并回主线！'],t,K7_P2+1.1)[0] or '要试哪套配色？',INK)
        sel=2 if p2>=1.1 else int(max(0,t-K7_OPEN)*1.2)%3
        for i,(tt,c) in enumerate([('A 蓝',BLUE),('B 粉',PINK),('C 绿',GREEN)]):
            if t<K7_HOUSES+0.15*i: continue
            x=66+i*64; y=284
            u.rectangle((x-1,y+2,x+7,y+10),fill=INK); u.rectangle((x,y+3,x+6,y+9),fill=c); text(u,(x+11,y+1),tt,INK)
        if t>=K7_HOUSES:
            ci=[0,1,2][sel] if p2<1.1 else 1
            cx=56+ci*64; u.polygon([(cx,286),(cx,294),(cx+4,290)],fill=OR)
K7=dict(world=k7_world,ui=k7_ui,mood='golden',flash=[(K7_P2+4.0,230,136)])
# ---------------- K9 推到 GitHub (164.33–176.73) ----------------
K9_WALK=(2.6,5.0); K9_KNOCK=5.3; K9_PUSH=9.6
def k9_world(sc,t):
    d=sc.d; px=sc.px; sc.grass(41)
    for i,(tx,ty) in enumerate([(16,70),(34,60),(252,150),(20,150),(14,232),(258,234),(40,240)]): sc.tree(tx,ty,10 if i%2 else 12,i+40)
    sc.path([(135,176),(135,250)],6,'dirt',seed=4,smooth=False)
    YX0,YY0,YX1,YY1=78,92,192,172
    d.rectangle((YX0,YY0,YX1,YY1),fill=(126,182,96)); sc.house(113,104,OR)
    for (x,y) in [(90,150),(176,150)]: sc.flowerbed(x-6,y,2)
    def post(x,y): d.rectangle((x,y-10,x+3,y+2),fill=INK); d.rectangle((x+1,y-9,x+2,y+1),fill=(214,166,112))
    def rail(x0,y,x1):
        d.rectangle((x0,y-7,x1,y-5),fill=INK); d.line([(x0,y-6),(x1,y-6)],fill=(226,180,126)); d.rectangle((x0,y-2,x1,y),fill=INK); d.line([(x0,y-1),(x1,y-1)],fill=(206,156,102))
    rail(YX0,YY0,YX1)
    for x in range(YX0,YX1+1,10): post(x,YY0)
    for y in range(YY0+10,YY1,10): post(YX0,y); post(YX1-3,y)
    rail(YX0,YY1,124); rail(146,YY1,YX1)
    for x in list(range(YX0,124,10))+list(range(150,YX1+1,10)): post(x,YY1)
    d.rectangle((124,YY1-12,146,YY1+1),fill=INK)
    for x in range(126,145,4): d.rectangle((x,YY1-11,x+2,YY1),fill=(196,146,96))
    LOCK=["...oooooo...","..oo....oo..","..o......o..","..o......o..","oooooooooooo","oYYYYYYYYYYo","oYyyyyyyyyYo","oYYYYooYYYYo","oYYYYooYYYYo","oYYYYYoYYYYo","oDDDDDDDDDDo","oooooooooooo"]
    LOCK2=[''.join(c*2 for c in r) for r in LOCK for _ in (0,1)]
    shake=1 if K9_KNOCK<=t<K9_KNOCK+0.6 and int(t*16)%2 else 0
    sprite(sc.im,123+shake,YY1-22,LOCK2,{'o':INK,'Y':(255,206,72),'y':(255,240,170),'D':(214,150,40)})
    vs=[(92,198,V1),(150,206,V2),(184,196,V3)]
    for i,(vx,vy,v) in enumerate(vs):
        yy,mv=walk(vy+70,vy,t,K9_WALK[0]+0.3*i,K9_WALK[1]+0.3*i)
        if yy<H-10: sc.shadow(vx,int(yy)+22); person(sc.im,vx,int(yy)+step_bob(mv,t),v)
    QB=["oooooooo","oWWWWWWo","oWWooWWo","oWWWoWWo","oWWoWWWo","oWWWWWWo","oWWoWWWo","oooooooo","..oo....","..o....."]
    QB2=[''.join(c*2 for c in r) for r in QB for _ in (0,1)]
    for k,(vx,vy,v) in enumerate(vs[::2]):
        pop_world(sc,t,K9_KNOCK+0.5+0.3*k,lambda s,vx=vx,vy=vy:sprite(s.im,vx+10,vy-24,QB2,{'o':INK,'W':(255,255,255)}),(vx+9,vy-25,vx+27,vy-4))
    if t>=K9_KNOCK: pop_world(sc,t,K9_KNOCK,lambda s:bubble(s.d,138,182,'咚咚!'),(136,180,180,206))
    if t>=K9_PUSH:
        CX,CY=214,74+int(round(math.sin(t*1.6)))
        def cloud(s):
            dd=s.d
            for bx,by,r in [(-18,2,10),(-4,-4,13),(12,-2,12),(24,4,8)]: dd.ellipse((CX+bx-r,CY+by-r+3,CX+bx+r,CY+by+r+3),fill=(214,222,244))
            for bx,by,r in [(-18,2,10),(-4,-4,13),(12,-2,12),(24,4,8)]: dd.ellipse((CX+bx-r,CY+by-r,CX+bx+r,CY+by+r-1),fill=(255,255,255))
            dd.rectangle((CX-8,CY-10,CX+8,CY+2),fill=INK); dd.rectangle((CX-7,CY-9,CX+7,CY+1),fill=(252,240,216)); dd.polygon([(CX-10,CY-9),(CX,CY-17),(CX+10,CY-9)],fill=INK); dd.polygon([(CX-8,CY-10),(CX,CY-16),(CX+8,CY-10)],fill=PURPLE); dd.rectangle((CX-2,CY-5,CX+2,CY+1),fill=PURPLE)
        pop_world(sc,t,K9_PUSH,cloud,(CX-30,CY-18,CX+34,CY+15))
        trail=catmull([(160,100),(176,92),(190,84)],8); n=int(len(trail)*clamp((t-K9_PUSH-0.3)/0.8))
        for i,(x,y) in enumerate(trail[:n]):
            if i%3==0: x,y=int(x),int(y); d.rectangle((x-1,y-1,x+1,y+1),fill=(255,226,140)); px[x,y]=(255,255,230,255)
        burst(d,t,K9_PUSH+1.1,214,70,n=10,dur=1.0)
def k9_ui(sc,t):
    ui_title(sc,'GitHub','光有 Git 还不够','为什么要推上去',t)
    pop_into(sc.ui,t,K9_KNOCK+0.2,lambda s:tag(s.u,30,176,'别人进不来',(200,80,80)),(30,176,104,191))
    pop_into(sc.ui,t,K9_PUSH+0.4,lambda s:tag(s.u,176,96,'推送到 GitHub',PURPLE,point='up'),(176,91,266,111))
    if t>0.6:
        l2=[('想给别人用，就推到 GitHub',(150,116,96))]
        lines=typed(['存档只在我自己电脑上，'],t,0.6)+ (typed(l2,t,K9_PUSH) if t>=K9_PUSH else [])
        dialog(sc,lines)
K9=dict(world=k9_world,ui=k9_ui,mood='golden',flash=[(K9_PUSH+1.1,214,70)])
# ---------------- K12 互相覆盖 (250.33–256.77) ----------------
K12_BANG=2.6
def k12_world(sc,t):
    d=sc.d; sc.grass(51)
    for i,(tx,ty) in enumerate([(16,70),(36,62),(254,70),(236,62),(16,226),(36,238),(254,226),(232,238)]): sc.tree(tx,ty,10 if i%2 else 12,i+50)
    sc.path([(-4,200),(274,200)],7,'dirt',seed=8,smooth=False)
    sh=(1 if int(t*18)%2 else -1) if K12_BANG<=t<K12_BANG+0.5 else 0
    BX0,BY0,BX1,BY1=86+sh,92,184+sh,164
    for lx in (BX0+10,BX1-12): d.rectangle((lx,BY1,lx+3,BY1+30),fill=INK); d.line([(lx+1,BY1),(lx+1,BY1+29)],fill=(150,104,66))
    d.rectangle((BX0-3,BY0-3,BX1+3,BY1+3),fill=INK); d.rectangle((BX0-2,BY0-2,BX1+2,BY1+2),fill=(170,118,74)); d.line([(BX0-2,BY0-2),(BX1+2,BY0-2)],fill=(206,156,102))
    d.rectangle((BX0,BY0,BX1,BY1),fill=INK); d.rectangle((BX0+1,BY0+1,BX1-1,BY1-1),fill=(255,250,238))
    d.rectangle((BX0+1,BY0+1,BX1-1,BY0+12),fill=(236,226,206)); text(d,(BX0+5,BY0),'index.html',(120,96,84))
    for k in range(5): d.line([(BX0+8,BY0+20+k*8),(BX0+60+(k*13)%30,BY0+20+k*8)],fill=(206,200,192))
    def hatch(x0,y0,x1,y1,col,step,seed,p):
        r=random.Random(seed); up=True; pts=[]; x=x0
        while x<x1: pts.append((x,y0+r.randint(0,4) if up else y1-r.randint(0,4))); x+=step+r.randint(0,2); up=not up
        n=int((len(pts)-1)*clamp(p))
        for a_,b_ in zip(pts[:n],pts[1:n+1]): d.line([a_,b_],fill=col,width=2)
    hatch(BX0+8,BY0+18,BX0+66,BY0+44,OR,5,1,(t-0.4)/1.0)
    hatch(BX0+36,BY0+30,BX1-8,BY0+56,BLUE,5,2,(t-0.7)/1.0)
    hatch(BX0+14,BY0+46,BX0+60,BY1-8,OR,6,3,(t-1.3)/0.9)
    hatch(BX0+50,BY0+16,BX1-12,BY0+34,BLUE,6,4,(t-1.5)/0.9)
    if t>=K12_BANG:
        text(d,(BX0+60,BY0+38),'??',(200,60,60))
        for k,(x,y,r) in enumerate([(170,86,8),(182,78,6),(160,78,6),(190,90,5),(96,88,6),(86,80,5)]):
            yy=y-int((t-K12_BANG)*4)%6
            d.ellipse((x-r,yy-r+1,x+r,yy+r+1),fill=(150,146,150)); d.ellipse((x-r,yy-r,x+r,yy+r-1),fill=(206,204,208))
        def bang(s):
            cx,cy=196,96; dd=s.d; pts=[]
            for k in range(16):
                a=k*math.pi/8; r=20 if k%2==0 else 10; pts.append((cx+r*math.cos(a),cy+r*math.sin(a)*0.85))
            dd.polygon(pts,fill=INK); dd.polygon([(cx+(p[0]-cx)*0.84,cy+(p[1]-cy)*0.84) for p in pts],fill=(255,214,80))
            dd.polygon([(cx+(p[0]-cx)*0.5,cy+(p[1]-cy)*0.5) for p in pts],fill=(255,246,190)); text(dd,(cx-9,cy-7),'砰',(200,60,50))
        pop_world(sc,t,K12_BANG,bang,(174,76,218,116),dur=0.25)
    # the two writers lean in while scribbling
    lean=1 if 0.4<t<2.4 and int(t*6)%2 else 0
    sc.shadow(60,184); person(sc.im,60+lean,162)
    sc.shadow(196,184); person(sc.im,196-lean,162,V1,flip=True)
    PEN=["......oo",".....oPo","....oPPo","...oYPo.","..oYYo..",".oSYo...","oSSo....","ooo....."]
    pp={'o':INK,'P':(240,120,120),'Y':(255,206,96),'S':(250,220,190)}
    sprite(sc.im,74+lean,160-lean,PEN,pp); sprite(sc.im,186-lean,160-lean,[r[::-1] for r in PEN],pp)
    if t>=K12_BANG:
        SW=[".o.","oWo","oWo",".o."]
        for (x,y) in [(58,158),(214,158)]: sprite(sc.im,x,y+int((t*6)%3),SW,{'o':(60,110,170),'W':(170,220,255)})
def k12_ui(sc,t):
    ui_title(sc,'GitHub','最怕互相覆盖','多人协作',t)
    pop_into(sc.ui,t,0.3,lambda s:tag(s.u,14,140,'du 改配色',OR,point='down'),(14,140,80,159))
    pop_into(sc.ui,t,0.6,lambda s:tag(s.u,190,140,'朋友改文案',BLUE,point='down'),(190,140,266,159))
    if t>0.4: dialog(sc,typed(['两个人同时改同一个文件，',('后存的会把先存的覆盖掉',(150,116,96))],t,0.4,16))
K12=dict(world=k12_world,ui=k12_ui,mood='golden')
# ---------------- K13 Pull request (256.77–268.20) ----------------
K13_ENV=5.3; K13_TAG=7.5; K13_BOSS=8.6; K13_STAMP=(9.9,10.5)
def k13_world(sc,t):
    d=sc.d; px=sc.px; sc.grass(61)
    for i,(tx,ty) in enumerate([(16,70),(36,60),(16,226),(38,238),(254,226),(232,238),(254,150)]): sc.tree(tx,ty,10 if i%2 else 12,i+60)
    sc.path([(-4,206),(274,206)],7,'dirt',seed=9,smooth=False)
    sc.path([(196,112),(196,206)],5,'stone',seed=3,smooth=False)
    sc.house(174,68,OR)
    fx,mv=walk(20,70,t,0.4,2.4)
    sc.shadow(int(fx),170); person(sc.im,int(fx),148+step_bob(mv,t),V1)
    sc.shadow(142,170); person(sc.im,142,148+(-1 if int(t*2.5)%2 else 0),flip=True)
    ex,ey=94,128
    if t>=K13_ENV:
        k=smooth((t-K13_ENV)/0.6); eyy=int(ey+(1-k)*20); exx=int(ex-(1-k)*16)
        def env(s,ex=exx,ey=eyy):
            dd=s.d
            dd.rectangle((ex,ey,ex+40,ey+26),fill=INK); dd.rectangle((ex+1,ey+1,ex+39,ey+25),fill=(255,246,226))
            dd.polygon([(ex+1,ey+1),(ex+20,ey+14),(ex+39,ey+1)],fill=(236,222,196)); dd.line([(ex+1,ey+1),(ex+20,ey+14),(ex+39,ey+1)],fill=INK)
            dd.line([(ex+1,ey+25),(ex+14,ey+15)],fill=(214,200,176)); dd.line([(ex+39,ey+25),(ex+26,ey+15)],fill=(214,200,176))
        env(sc)
        scx,scy=ex+28,ey+17
        if t>=K13_STAMP[1]:
            d.ellipse((scx-11,scy-9,scx+11,scy+9),fill=(70,160,96)); d.ellipse((scx-9,scy-7,scx+9,scy+7),fill=(255,246,226)); d.ellipse((scx-8,scy-6,scx+8,scy+6),fill=(70,160,96))
            sprite(sc.im,scx-4,scy-3,["......ww","......ww",".....ww.","ww..ww..",".wwww...","..ww...."],{'w':(255,255,255)})
        if K13_STAMP[0]<=t<K13_STAMP[1]+0.4:
            q=clamp((t-K13_STAMP[0])/(K13_STAMP[1]-K13_STAMP[0])); sy=int(ey-34+20*q*q)
            STP=["..oooo..","..oHHo..","..oHHo..",".oooooo.","oGGGGGGo","oooooooo"]
            sprite(sc.im,scx-8,sy,[''.join(c*2 for c in r) for r in STP for _ in (0,1)],{'o':INK,'H':(150,104,66),'G':(70,160,96)})
        if t>=K13_STAMP[1]+0.2:
            trail=catmull([(136,130),(156,108),(178,100),(194,104)],8); n=int(len(trail)*clamp((t-K13_STAMP[1]-0.2)/0.5))
            for i,(x,y) in enumerate(trail[:n]):
                if i%3==0: x,y=int(x),int(y); d.rectangle((x-1,y-1,x+1,y+1),fill=(150,230,160)); px[x,y]=(240,255,240,255)
        burst(d,t,K13_STAMP[1],scx,scy,col=(200,255,210),n=10,dur=0.9,spd=30)
    if t>=K13_STAMP[1]+0.7: pop_world(sc,t,K13_STAMP[1]+0.7,lambda s:sprite(s.im,212,58,OK_BADGE,BADGE_PAL_OK),(210,56,230,76))
def k13_ui(sc,t):
    ui_title(sc,'GitHub','改动先申请，同意才生效','Pull request',t)
    pop_into(sc.ui,t,0.4,lambda s:tag(s.u,62,180,'朋友',BLUE,point='up'),(62,175,100,195))
    pop_into(sc.ui,t,K13_BOSS,lambda s:tag(s.u,126,180,'负责人',OR,point='up'),(126,175,176,195))
    pop_into(sc.ui,t,K13_TAG,lambda s:tag(s.u,40,96,'修改申请 Pull request',PURPLE,point='down'),(40,96,172,115))
    pop_into(sc.ui,t,K13_STAMP[1]+0.6,lambda s:tag(s.u,200,124,'合并进项目',(86,170,104)),(200,124,266,139))
    if t>0.5:
        l=typed(['改动先装进"修改申请"，'],t,0.5)
        if t>=K13_BOSS: l+=typed([('负责人点了同意，才会合并',(150,116,96))],t,K13_BOSS)
        dialog(sc,l)
K13=dict(world=k13_world,ui=k13_ui,mood='golden',flash=[(K13_STAMP[1],122,145)])
SCENES=dict(K5=K5,K6=K6,K7=K7,K9=K9,K12=K12,K13=K13)
def make(name,dur):
    c=dict(SCENES[name]); return BAnim(c.pop('world'),c.pop('ui'),dur=dur,**c)
if __name__=='__main__':
    import sys
    tests=dict(K5=(9.9,[0.6,3,6.5,9.5]),K6=(12.8,[2,5,9.8,12.3]),K7=(21.7,[1.5,4.5,9,19.5]),K9=(12.4,[1,6,10.5,12]),K12=(6.4,[1,2.8,4,6]),K13=(11.4,[2,6,9.2,11.2]))
    for name in (sys.argv[1:] or tests):
        dur,ts=tests[name]; a=make(name,dur)
        row=Image.new('RGB',(270*len(ts),360))
        for i,t in enumerate(ts): row.paste(a.frame(t).resize((270,360)),(i*270,0))
        row.save(f'{WORK}/full/test_{name}.jpg',quality=85)
