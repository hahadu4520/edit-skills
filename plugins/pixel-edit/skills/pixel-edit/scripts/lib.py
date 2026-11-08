from PIL import Image, ImageDraw, ImageFont
import random, math
W,H,S=270,360,4
import os; FONT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fonts','fusion-pixel.ttf')
def font(px=12): return ImageFont.truetype(FONT,px)
F12=font(12)
def new(bg=(0,0,0)):
    im=Image.new('RGBA',(W,H),bg+(255,)); d=ImageDraw.Draw(im); d.fontmode='1'; return im,d
def sprite(im,x,y,rows,pal,flip=False):
    px=im.load()
    for j,row in enumerate(rows):
        if flip: row=row[::-1]
        for i,ch in enumerate(row):
            if ch in pal and pal[ch] is not None:
                xx,yy=x+i,y+j
                if 0<=xx<im.width and 0<=yy<im.height: px[xx,yy]=pal[ch]+(255,) if len(pal[ch])==3 else pal[ch]
def text(d,xy,s,fill,f=F12,shadow=None,outline=None):
    x,y=xy
    if outline:
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx or dy: d.text((x+dx,y+dy),s,font=f,fill=outline)
    if shadow: d.text((x+1,y+1),s,font=f,fill=shadow)
    d.text((x,y),s,font=f,fill=fill)
def tw(s,f=F12):
    return int(f.getlength(s))
def bigtext(im,xy,s,fill,scale=2,outline=None,shadow=None,f=F12):
    # render at 12px then scale integer -> chunky pixel title
    w=tw(s,f)+4; h=16
    t=Image.new('RGBA',(w,h),(0,0,0,0)); td=ImageDraw.Draw(t); td.fontmode='1'
    td.text((1,0),s,font=f,fill=fill)
    t=t.resize((w*scale,h*scale),Image.NEAREST)
    x,y=xy
    if outline or shadow:
        a=t.split()[3]
        if shadow:
            sh=Image.new('RGBA',t.size,shadow+(255,)); 
            for dx,dy in shadow_offsets(scale): im.paste(sh,(x+dx,y+dy),a)
        if outline:
            o=Image.new('RGBA',t.size,outline+(255,))
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if dx or dy: im.paste(o,(x+dx,y+dy),a)
    im.paste(t,(x,y),t)
    return w*scale
def shadow_offsets(scale): return [(0,1),(1,1),(0,2),(1,2)] if scale>1 else [(1,1)]
def rect(d,b,fill): d.rectangle(b,fill=fill)
def finish(im,path,guide=True):
    big=im.convert('RGB').resize((W*S,H*S),Image.NEAREST)
    if guide:
        g=ImageDraw.Draw(big,'RGBA')
        for x in range(150,930,24):
            g.line([(x,1225),(x+12,1225)],fill=(255,255,255,170),width=2); g.line([(x,1321),(x+12,1321)],fill=(255,255,255,170),width=2)
    big.save(path); return big
def lerpc(a,b,t): return tuple(int(round(a[i]+(b[i]-a[i])*t)) for i in range(3))
def catmull(pts,n=20):
    P=[pts[0]]+pts+[pts[-1]]; out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1],P[i],P[i+1],P[i+2]
        for k in range(n):
            t=k/n; t2=t*t; t3=t2*t
            out.append(tuple(0.5*((2*p1[j])+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in range(2)))
    out.append(pts[-1]); return out
def dist_mask(pts,r,w=W,h=H):
    # boolean mask of pixels within r of polyline
    m=[[False]*w for _ in range(h)]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    x0,x1=max(0,int(min(xs)-r-2)),min(w-1,int(max(xs)+r+2)); y0,y1=max(0,int(min(ys)-r-2)),min(h-1,int(max(ys)+r+2))
    segs=list(zip(pts[:-1],pts[1:]))
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            cx,cy=x+0.5,y+0.5; best=1e9
            for (ax,ay),(bx,by) in segs:
                dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
                t=0 if L==0 else max(0,min(1,((cx-ax)*dx+(cy-ay)*dy)/L))
                ex,ey=ax+t*dx-cx,ay+t*dy-cy; dd=ex*ex+ey*ey
                if dd<best: best=dd
            if best<=r*r: m[y][x]=True
    return m
def paint_mask(im,m,fill,edge=None,hl=None,tex=None,seed=1):
    px=im.load(); rnd=random.Random(seed); h=len(m); w=len(m[0])
    for y in range(h):
        for x in range(w):
            if not m[y][x]: continue
            nb=[m[y+dy][x+dx] if 0<=y+dy<h and 0<=x+dx<w else False for dx,dy in((1,0),(-1,0),(0,1),(0,-1))]
            c=fill
            if edge and not all(nb):
                c=edge
            elif hl and not (m[y-1][x] if y>0 else False):
                c=hl
            elif tex and rnd.random()<tex[1]: c=tex[0]
            px[x,y]=c+(255,)
