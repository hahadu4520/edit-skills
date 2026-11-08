"""横版封面：从 16:9 成片的某一帧出 YouTube 16:9、B 站 16:10 和 B 站首页 4:3 三张封面。
画面内容不动，比例不够的地方用同一套像素草地在上下补出来（不裁内容）。
usage: SRC=原片.mov python3 cover_wide.py 时间(秒) 输出目录 [--nosub]"""
import os, sys, importlib.util, numpy as np
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
t=float(sys.argv[1]); out=sys.argv[2]; nosub='--nosub' in sys.argv; os.makedirs(out,exist_ok=True)
import r16
src=r16.src_at(t); base=r16.base(r16.seg_at(t),t,src)
base=(base if isinstance(base,Image.Image) else Image.fromarray(np.asarray(base))).convert('RGB')
sub=base.convert('RGBA')
if not nosub: r16.subs(sub,t)
sub=sub.convert('RGB')
sub.resize((1280,720),Image.LANCZOS).save(f'{out}/cover-youtube-16x9.jpg',quality=93)

def tall_bg(pad_grid,extra_trees):
    """把 r16 的草地画布在上下各加 pad_grid 格（×4 像素），只渲染背景。"""
    s=open(os.path.join(HERE,'r16.py'),encoding='utf-8').read()
    LH=270+2*pad_grid
    s=s.replace("WW,WH=1920,1080; LW,LH=480,270",f"WW,WH=1920,{LH*4}; LW,LH=480,{LH}",1)
    a=s.index('def meadow(sc,t):'); b=s.index('\n',s.index('sc.flowerbed(110,14,4)'))
    body=s[a:b]
    body=body.replace("sc.grass(41,0,LH)",f"O={pad_grid}\n    sc.grass(41,0,LH)")
    body=body.replace("(-6,236),(90,230),(200,238),(320,230),(486,236)","(-6,236+O),(90,230+O),(200,238+O),(320,230+O),(486,236+O)")
    body=body.replace("sc.tree(tx,ty,r,i+40)","sc.tree(tx,ty+O,r,i+40)")
    body=body.replace("sc.flowerbed(110,14,4); sc.flowerbed(190,22,3); sc.flowerbed(330,8,4)",
        "sc.flowerbed(110,14+O,4); sc.flowerbed(190,22+O,3); sc.flowerbed(330,8+O,4)\n"
        f"    for i,(tx,ty,r) in enumerate({extra_trees}): sc.tree(tx,ty,r,i+70)")
    s=s[:a]+body+s[b:]
    p=os.path.join(HERE,f'_r16_pad{pad_grid}.py'); open(p,'w',encoding='utf-8').write(s)
    spec=importlib.util.spec_from_file_location(f'_r16_pad{pad_grid}',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    im=m.WAnim(m.meadow,lambda sc,t:None,static=True).frame(t)
    os.remove(p)
    return (im if isinstance(im,Image.Image) else Image.fromarray(np.asarray(im))).convert('RGB')

d=(np.abs(np.asarray(sub,int)-np.asarray(base,int)).sum(2)>0)
submask=Image.fromarray((d*255).astype('uint8'))
def compose(bg,off,F):
    m=np.ones((1080,),np.float32); r=np.linspace(0,1,F); m[:F]=r; m[-F:]=r[::-1]
    bg.paste(base,(0,off),Image.fromarray((np.repeat(m[:,None],1920,1)*255).astype('uint8')))
    bg.paste(sub,(0,off),submask); return bg
# 16:10：上下各补 60px
compose(tall_bg(15,[]),60,60).save(f'{out}/cover-bilibili-16x10.jpg',quality=93)
# 4:3：上下各补 180px，补出来的草地上加几棵树，再缩到 1440×1080
trees=[(90,16,12),(200,10,11),(300,18,12),(400,8,11),(30,345,12),(170,350,11),(300,343,12),(430,352,11)]
compose(tall_bg(45,trees),180,80).resize((1440,1080),Image.LANCZOS).save(f'{out}/cover-bilibili-4x3.jpg',quality=93)
print('ok',out)
