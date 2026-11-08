# Pixel overlays for the A shots (title, "一头雾水？", contents list), drawn on the 270x360 grid and upscaled x4.
from world import *
from PIL import Image, ImageDraw
import math, random
def eob(x,s=1.9):
    x=min(max(x,0),1); x-=1; return x*x*((s+1)*x+s)+1
def place(canvas,el,box,k):
    # paste low-res element (cropped by box) at scale k about its centre, nearest-neighbour, on final-res canvas
    x0,y0,x1,y1=box; e=el.crop(box).resize(((x1-x0)*4,(y1-y0)*4),Image.NEAREST)
    if k<=0.02: return
    if abs(k-1)>1e-3:
        w,h=e.size; e=e.resize((max(1,int(w*k)),max(1,int(h*k))),Image.NEAREST)
    cx,cy=(x0+x1)*2,(y0+y1)*2
    canvas.alpha_composite(e,(int(cx-e.width/2),int(cy-e.height/2)))
def blank(): return Image.new('RGBA',(1080,1440),(0,0,0,0))
def lowres():
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); d.fontmode='1'; return im,d
def star(d,x,y,c=(255,246,200)):
    d.point([(x,y-2),(x,y-1),(x-2,y),(x-1,y),(x+1,y),(x+2,y),(x,y+1),(x,y+2)],fill=c); d.point((x,y),fill=(255,255,255))
# ---- seg 0: title ----
def title_el(t):
    im,d=lowres()
    window(im,(8,16,262,70))
    t1=Image.new('RGBA',(W,H),(0,0,0,0)); wa=bigtext(t1,(0,0),'Git',OR,scale=3,shadow=(150,60,40))
    t2=Image.new('RGBA',(W,H),(0,0,0,0)); wb=bigtext(t2,(0,0),'vs',(150,116,96),scale=2)
    t3=Image.new('RGBA',(W,H),(0,0,0,0)); wc=bigtext(t3,(0,0),'GitHub',PURPLE,scale=3,shadow=(80,60,140))
    t1=t1.crop(t1.getbbox()); t2=t2.crop(t2.getbbox()); t3=t3.crop(t3.getbbox())
    tot=t1.width+t2.width+t3.width+16; x=135-tot//2; y=28
    im.alpha_composite(t1,(x,y)); x+=t1.width+8; im.alpha_composite(t2,(x,y+t1.height-t2.height)); x+=t2.width+8; im.alpha_composite(t3,(x,y))
    return im
def seg0(t):
    c=blank()
    if t<0.08 or t>3.0: return c
    k=eob((t-0.08)/0.35) if t<2.8 else max(0,1-(t-2.8)/0.2)
    el=title_el(t)
    bob=int(round(math.sin(t*3.2)))  # 1 low-res px float
    if bob: el=el.transform(el.size,Image.AFFINE,(1,0,0,0,1,-bob))
    if t>0.5 and t<2.8:
        d=ImageDraw.Draw(el)
        for i,(sx,sy) in enumerate([(6,12),(264,28),(256,74),(16,74)]):
            if int(t*5+i)%3: star(d,sx,sy)
    place(c,el,(2,6,268,80),k); return c
# ---- seg 2: 一头雾水？ ----
def fog_el(t):
    im,d=lowres()
    x0,y0,x1,y1=128,26,264,62
    d.rounded_rectangle((x0,y0,x1,y1),radius=10,fill=INK); d.rounded_rectangle((x0+1,y0+1,x1-1,y1-1),radius=9,fill=(255,255,255))
    d.line([(x0+8,y1-2),(x1-8,y1-2)],fill=(220,214,224))
    for (cx,cy,r) in [(140,70,4),(132,79,3),(126,86,2)]:
        d.ellipse((cx-r-1,cy-r-1,cx+r+1,cy+r+1),fill=INK); d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,255,255))
    t1=Image.new('RGBA',(W,H),(0,0,0,0)); w=bigtext(t1,(0,0),'一头雾水',INK,scale=2)
    t2=Image.new('RGBA',(W,H),(0,0,0,0)); w2=bigtext(t2,(0,0),'?',OR,scale=2,shadow=(150,60,40))
    x=(x0+x1)//2-(w+w2)//2; im.alpha_composite(t1,(x,32)); im.alpha_composite(t2,(x+w,32))
    return im
def qmark(d,x,y,col):
    rows=[".ooo.","o...o","....o","...o.","..o..",".....","..o.."]
    for j,r in enumerate(rows):
        for i,ch in enumerate(r):
            if ch=='o': d.rectangle((x+2*i,y+2*j,x+2*i+1,y+2*j+1),fill=col)
def seg2(t,T0=17.53,T1=20.93):
    c=blank()
    if t<T0 or t>=T1: return c
    tt=t-T0
    k=eob(tt/0.3) if t<T1-0.15 else max(0,(T1-t)/0.15)
    place(c,fog_el(tt),(118,22,266,92),k)
    # floating question marks pop in one by one
    for i,(x,y,col,dl) in enumerate([(30,96,OR,0.35),(56,70,PURPLE,0.6),(20,130,BLUE,0.85)]):
        if tt<dl: continue
        im,d=lowres(); fy=y+int(round(math.sin((tt-dl)*4+i)*1.5))
        for dx in (-1,0,1):
            for dy in (-1,0,1): qmark(d,x+dx,fy+dy,INK)
        qmark(d,x,fy,col)
        place(c,im,(x-2,fy-2,x+13,fy+17),eob((tt-dl)/0.25)*(1 if t<T1-0.15 else max(0,(T1-t)/0.15)))
    return c
# ---- seg 3: contents ----
CH=[('1','是什么',OR,26.2),('2','有什么用',BLUE,28.53),('3','怎么用',GREEN,31.7)]
def toc_layer(t,T0=24.53,T1=33.5):
    c=blank()
    if t<T0 or t>=T1: return c
    out=1 if t<T1-0.2 else max(0,(T1-t)/0.2)
    im,d=lowres()
    window(im,(14,14,256,70))
    text(d,(24,20),'今天 3 分钟讲清楚',(150,116,96))
    place(c,im,(14,14,257,71),eob((t-T0)/0.35)*out)
    x=24
    for n,lab,col,ts in CH:
        im,d=lowres()
        w=tw(lab)+22
        d.rectangle((x,40,x+w,58),fill=INK); d.rectangle((x+1,41,x+w-1,57),fill=lerpc(col,(255,255,255),.82))
        d.rectangle((x+1,41,x+14,57),fill=col); text(d,(x+5,42),n,(255,255,255)); text(d,(x+18,42),lab,INK)
        if t>=ts: place(c,im,(x,40,x+w+1,59),eob((t-ts)/0.3)*out)
        x+=w+8
    return c
