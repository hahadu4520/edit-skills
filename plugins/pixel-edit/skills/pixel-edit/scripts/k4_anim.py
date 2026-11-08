# Animated K4 "存档中": world rendered once per character pose, UI + particles per frame.
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
from world import *
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
S_=4
def build_world(py_off=0):
    sc=Scene(); sc.grass(21); d=sc.d
    sc.path([(20,170),(250,170)],7.2,'dirt',seed=3,smooth=False)
    sc.path([(135,140),(135,170)],5,'stone',seed=4,smooth=False)
    for i,(tx,ty) in enumerate([(16,70),(36,60),(250,74),(232,64),(18,214),(40,226),(236,206),(256,222),(64,212),(206,216)]): sc.tree(tx,ty,10 if i%2 else 12,i)
    sc.house(113,96,OR)
    cx,cy=186,140
    for r,c in [(19,(170,214,236)),(15,(200,232,246)),(11,(232,246,252))]: d.ellipse((cx-r,cy+14-r//3,cx+r,cy+14+r//3),fill=c)
    sc.crystal(cx,cy-4,3)
    sc.sign(62,146,'my-site'); sc.flowerbed(115,140,2); sc.flowerbed(144,140,2)
    sc.shadow(156,165)
    person(sc.im,156,142+py_off)
    return sc
def grade(sc,focus=0.45,band=0.20,bloom=0.5):
    big=sc.im.convert('RGB').resize((W*S_,H*S_),Image.NEAREST)
    img=np.array(big).astype(np.float32)/255; HH,WW=img.shape[:2]
    yy,xx=np.mgrid[0:HH,0:WW]; t=(xx/WW*0.45+yy/HH*0.55)
    img=img*np.stack([1.10-0.22*t,1.03-0.15*t,0.90-0.02*t],2)
    sat=img.max(2)-img.min(2)
    br=np.clip(img-0.86,0,1)*(sat[...,None]>0.15)
    bl=np.array(Image.fromarray((np.clip(br*3,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(14))).astype(np.float32)/255
    img=np.clip(img+bl*bloom,0,1)
    blur=np.array(Image.fromarray((img*255).astype('uint8')).filter(ImageFilter.GaussianBlur(5))).astype(np.float32)/255
    k=np.clip((np.abs(yy/HH-focus)-band)/0.12,0,1)[...,None]
    img=img*(1-k)+blur*k
    r=np.sqrt(((xx-WW/2)/(WW/2))**2+((yy-HH*0.45)/(HH/1.6))**2)
    return img, np.clip(1.08-0.32*r**2,0.55,1.1)[...,None]
def rays_layer(phase):
    HH,WW=H*S_,W*S_; yy,xx=np.mgrid[0:HH:4,0:WW:4]
    ang=np.arctan2(yy+200,xx+260); r_=np.zeros(yy.shape,np.float32)
    for c,w in [(0.62,0.035),(0.78,0.05),(0.93,0.03),(1.06,0.045)]: r_+=np.exp(-((ang-c-0.025*math.sin(phase+c*5))/w)**2)*0.9
    r_*=np.clip(1-(np.sqrt((xx+260)**2+(yy+200)**2)/1700),0,1)
    im=Image.fromarray((np.clip(r_,0,1)*255).astype('uint8')).filter(ImageFilter.GaussianBlur(4.5)).resize((WW,HH),Image.BILINEAR)
    return np.array(im).astype(np.float32)[...,None]/255*np.array([0.30,0.24,0.12])
POSES={o:grade(build_world(o)) for o in (0,-1,-2,-3,-4)}
VIG=POSES[0][1]
RAYS=[rays_layer(2*math.pi*i/24) for i in range(24)]
rnd=random.Random(7)
PARTS=[dict(x=rnd.uniform(0,W),y=rnd.uniform(40,250),v=rnd.uniform(3,7),ph=rnd.uniform(0,6.28),c=rnd.choice([(255,236,170),(255,214,226),(255,250,220)])) for _ in range(40)]
def ease_out_back(x,s=1.7): x=min(max(x,0),1); x-=1; return x*x*((s+1)*x+s)+1
def clamp(x): return min(max(x,0),1)
T_FILL=(0.35,2.75)   # bar fills while "给AI项目做存档的工具" is said (local t)
def ui_layer(t):
    sc=Scene(); u=sc.u
    # title card drops in
    a=ease_out_back(t/0.45)
    if t>0.05:
        dy=int((1-a)*-60)
        tmp=Scene(); title_card(tmp,'Git','给项目做存档的工具','就像打游戏存档'); sc.ui.alpha_composite(tmp.ui.crop((0,0,W,60)),(0,dy) if dy>=0 else (0,0)) if dy>=0 else sc.ui.alpha_composite(tmp.ui.crop((0,-dy,W,60)),(0,0))
    # save window pops in
    if t>0.25:
        k=ease_out_back((t-0.25)/0.35)
        tmp=Scene(); uu=tmp.u
        window(tmp.ui,(52,188,218,240))
        p=clamp((t-T_FILL[0])/(T_FILL[1]-T_FILL[0])); p=p*p*(3-2*p)
        done=t>=T_FILL[1]
        text(uu,(62,193),'存档完成！' if done else '存档中'+'.'*(1+int(t*4)%3),(60,140,80) if done else INK)
        text(uu,(166,193),f'{int(p*100)}%',(150,116,96))
        uu.rectangle((62,210,208,220),fill=INK); uu.rectangle((63,211,207,219),fill=(232,220,204))
        fw=int(144*p)
        if fw>0:
            col=(92,176,118) if done else OR
            uu.rectangle((63,211,63+fw,219),fill=col)
            for x in range(63,63+fw,6): uu.line([(x,211),(x+2,211)],fill=lerpc(col,(255,255,255),.4))
            uu.line([(63,219),(63+fw,219)],fill=lerpc(col,(0,0,0),.2))
        if done:
            uu.line([(63,230),(65,232),(69,227)],fill=(70,150,90),width=2); text(uu,(74,223),'存档 V3 · 首页改好了',(70,130,80))
        else: text(uu,(62,223),'存档 V3 · 首页改好了',(110,88,84))
        box=tmp.ui.crop((48,184,224,246))
        if k<0.999:
            bw,bh=box.size; nw,nh=max(1,int(bw*k)),max(1,int(bh*k)); box=box.resize((nw,nh),Image.NEAREST)
            sc.ui.alpha_composite(box,(136-nw//2,215-nh//2))
        else: sc.ui.alpha_composite(box,(48,184))
    # dialog: typewriter after save
    if t>T_FILL[1]+0.25:
        tt=t-T_FILL[1]-0.25
        l1='帮我存档！'; l2='对 Agent 说这一句就够了'
        n=int(tt*14)
        a1=l1[:n]; a2=l2[:max(0,n-len(l1)-2)]
        dialog(sc,[a1,(a2,(150,116,96))])
    return sc.ui
def frame(t,dur):
    # pose: idle bob, jump at save
    tj=t-T_FILL[1]
    if 0<=tj<0.5: off=-int(round(4*math.sin(math.pi*tj/0.5)))
    else: off=-1 if int(t*2.5)%2 else 0
    img,_=POSES[off]
    img=img+RAYS[int(t*6)%24]*(0.85+0.15*math.sin(t*1.7))
    # crystal flash on save
    if 0<=tj<0.9:
        f=math.exp(-tj*4)
        HH,WW=img.shape[:2]; cx,cy=186*S_,136*S_
        yy,xx=np.ogrid[0:HH,0:WW]; g=np.exp(-((xx-cx)**2+(yy-cy)**2)/(2*(60+tj*260)**2))
        img=img+(g*f*0.9)[...,None]*np.array([0.85,0.95,1.0])
    img=np.clip(img*VIG,0,1)
    out=Image.fromarray((img*255).astype('uint8')).convert('RGBA')
    # particles (rise faster after save)
    glow=Image.new('RGBA',out.size,(0,0,0,0)); gd=ImageDraw.Draw(glow); dr=ImageDraw.Draw(out)
    boost=1+2.5*math.exp(-max(tj,0)*1.5) if tj>=0 else 1
    for p in PARTS:
        y=(p['y']-p['v']*t*boost)%220+30; x=p['x']+3*math.sin(t*1.3+p['ph'])
        tw_=0.55+0.45*math.sin(t*3+p['ph'])
        X,Y=int(x)*S_,int(y)*S_
        gd.ellipse((X-10,Y-10,X+14,Y+14),fill=p['c']+(int(70*tw_),)); dr.rectangle((X,Y,X+S_-1,Y+S_-1),fill=p['c']+(int(255*tw_),))
    # burst sparkles around crystal after save
    if 0<=tj<1.2:
        for i in range(10):
            a=i/10*6.283+0.3; r=8+tj*40
            X=int(186+math.cos(a)*r)*S_; Y=int(136+math.sin(a)*r*0.8)*S_
            al=int(255*(1-tj/1.2))
            dr.rectangle((X,Y,X+S_-1,Y+S_-1),fill=(255,252,210,al))
            for ox,oy in ((-1,0),(1,0),(0,-1),(0,1)): dr.rectangle((X+ox*S_,Y+oy*S_,X+ox*S_+S_-1,Y+oy*S_+S_-1),fill=(255,240,160,al//2))
    out=Image.alpha_composite(out,glow.filter(ImageFilter.GaussianBlur(6)))
    # slow push-in on world
    z=1+0.04*(t/dur)
    if z>1.001:
        w,h=out.size; cw,ch=w/z,h/z; x0=(w-cw)/2; y0=(h-ch)*0.4
        out=out.resize((w,h),Image.BILINEAR,box=(x0,y0,x0+cw,y0+ch))
    out=Image.alpha_composite(out,ui_layer(t).resize((W*S_,H*S_),Image.NEAREST))
    return out.convert('RGB')
if __name__=='__main__':
    for t in (0.2,0.6,1.5,2.8,3.2,5.5):
        frame(t,7.9).save(f'{WORK}/cut/k4/t{t}.png')
