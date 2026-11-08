# Pixel overlays for the A shots after segment 4.
from overlays import *
def chipbar(t,T0,T1,head,items):
    c=blank()
    if t<T0 or t>=T1: return c
    out=1 if t<T1-0.2 else max(0,(T1-t)/0.2)
    im,d=lowres(); window(im,(14,14,256,70)); text(d,(24,20),head,(150,116,96))
    place(c,im,(14,14,257,71),eob((t-T0)/0.35)*out)
    x=24
    for n,lab,col,ts in items:
        im,d=lowres(); nw=tw(n)+8; w=tw(lab)+nw+10
        d.rectangle((x,40,x+w,58),fill=INK); d.rectangle((x+1,41,x+w-1,57),fill=lerpc(col,(255,255,255),.82))
        d.rectangle((x+1,41,x+nw,57),fill=col); text(d,(x+5,42),n,(255,255,255)); text(d,(x+nw+5,42),lab,INK)
        if t>=ts: place(c,im,(x,40,x+w+1,59),eob((t-ts)/0.3)*out)
        x+=w+8
    return c
def badge(t,T0,T1,num,sub,big,col=OR):
    c=blank()
    if t<T0 or t>=T1: return c
    out=1 if t<T1-0.2 else max(0,(T1-t)/0.2)
    im,d=lowres(); window(im,(34,14,236,74))
    nw=tw(num)+10; bx=48
    d.rectangle((bx,24,bx+nw,40),fill=INK); d.rectangle((bx+1,25,bx+nw-1,39),fill=col); text(d,(bx+5,25),num,(255,255,255))
    text(d,(bx+nw+8,25),sub,(150,116,96))
    bigtext(im,(bx,44),big,INK,scale=2)
    if t>0: 
        for i,(sx,sy) in enumerate([(30,12),(240,26),(232,78),(40,78)]):
            if int(t*5+i)%3: star(d,sx,sy)
    place(c,im,(26,8,246,84),eob((t-T0)/0.4)*out); return c
def choice(t,T0,T1,head,opts):
    c=blank()
    if t<T0 or t>=T1: return c
    out=1 if t<T1-0.2 else max(0,(T1-t)/0.2)
    im,d=lowres(); x0,y0,x1=150,16,258; y1=y0+22+len(opts)*15
    window(im,(x0,y0,x1,y1)); text(d,(x0+9,y0+6),head,(150,116,96))
    sel=int(max(0,t-T0-0.6)*1.6)%len(opts)
    for i,o in enumerate(opts):
        yy=y0+21+i*15
        if i==sel: d.polygon([(x0+9,yy+3),(x0+9,yy+11),(x0+13,yy+7)],fill=OR); text(d,(x0+18,yy),o,OR)
        else: text(d,(x0+18,yy),o,INK)
    place(c,im,(x0,y0,x1+1,y1+1),eob((t-T0)/0.35)*out); return c
def endcard(t,T0,T1,tfollow):
    c=blank()
    if t<T0 or t>=T1: return c
    im,d=lowres(); window(im,(14,16,150,52)); text(d,(24,22),'更多 Agent 实用教程',INK); text(d,(24,36),'下期见～',(150,116,96))
    place(c,im,(14,16,151,53),eob((t-T0)/0.35))
    if t>=tfollow:
        im,d=lowres(); bx,by=158,20
        d.rectangle((bx,by,bx+98,by+30),fill=INK); d.rectangle((bx+1,by+1,bx+97,by+29),fill=OR); d.line([(bx+1,by+1),(bx+97,by+1)],fill=(250,160,120))
        bigtext(im,(bx+14,by+2),'★关注',(255,255,255),scale=2)
        if int(t*5)%3:
            for (sx,sy) in [(bx+4,by-5),(bx+104,by+24),(bx+92,by-5)]: star(d,sx,sy)
        place(c,im,(bx-4,by-8,bx+110,by+34),eob((t-tfollow)/0.35,2.4))
    return c
A_OVERLAYS=[
 lambda t: chipbar(t,53.60,58.30,'GitHub 就像',[('1','云端网盘',PURPLE,53.75),('2','多人协作',BLUE,55.35)]),
 lambda t: chipbar(t,58.40,61.70,'接下来',[('?','怎么用 Git',OR,59.8)]),
 lambda t: chipbar(t,74.40,79.55,'Git 两个好用的地方',[('1','存档',OR,76.9),('2','分支',GREEN,78.3)]),
 lambda t: badge(t,79.75,84.05,'第1招','Git','存档'),
 lambda t: chipbar(t,90.15,97.45,'需要存很多版本的时候',[('1','迭代网站',OR,91.2),('2','写小说',PINK,93.7),('3','写长文档',BLUE,95.0)]),
 lambda t: badge(t,120.0,128.30,'第2招','Git','分支',GREEN),
 lambda t: chipbar(t,128.60,131.10,'比如',[('1','设计',OR,128.7),('2','配色',PINK,130.0)]),
 lambda t: chipbar(t,144.60,147.60,'三条支线 · 三套配色',[('A','蓝',BLUE,144.9),('B','粉',PINK,145.3),('C','绿',GREEN,145.7)]),
 lambda t: choice(t,156.50,161.90,'剧情怎么走？',['留下','离开','反转']),
 lambda t: chipbar(t,197.40,203.20,'推到 GitHub 之后',[('1','云端备份',PURPLE,200.7),('2','部署上线',OR,201.3),('3','多人协作',BLUE,201.9)]),
 lambda t: chipbar(t,217.45,223.60,'推到 GitHub 之后',[('2','部署上线',OR,218.8)]),
 lambda t: chipbar(t,236.60,250.30,'推到 GitHub 之后',[('3','多人协作',BLUE,237.4),('↓','别人下载来改',GREEN,245.9)]),
 lambda t: chipbar(t,270.70,277.85,'想把项目开源？',[('!','推到 GitHub 是必选项',PURPLE,275.2)]),
 lambda t: endcard(t,282.33,287.0,285.17),
]
def a_overlay(t):
    c=blank()
    for f in A_OVERLAYS: c.alpha_composite(f(t))
    return c
