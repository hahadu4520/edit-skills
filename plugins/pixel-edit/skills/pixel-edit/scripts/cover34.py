"""3:4 封面：在视频里截的一帧上，人物一侧空处加 3 行得意黑短句。
样式（定稿）：一种字色、一种字号，深色字 + 白描边 + 轻阴影，右对齐，行距 1.55 倍。
usage: python3 cover34.py 底图.png 输出.jpg "第一行|第二行|第三行" [字号=60] [首行顶部y=640] [右边x=W-40] [left]
  例：python3 cover34.py frame.png cover.jpg "0 基础也能懂|Vibe Coding 必备|存档·协作·上线" 60
  字不要压到脸上方，放在嘴巴到肩膀之间的高度；写在左边空处时最后加 left。"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fonts','SmileySans-Oblique.ttf')
a=sys.argv[1:]; src,out,lines=a[0],a[1],a[2].split('|')
im=Image.open(src).convert('RGBA'); W,H=im.size
S=int(a[3]) if len(a)>3 else 60; Y=int(a[4]) if len(a)>4 else 640
left='left' in a; X=int(a[5]) if len(a)>5 and a[5]!='left' else (40 if left else W-40)
f=ImageFont.truetype(FONT,S)
txt=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(txt)
for i,t in enumerate(lines):
    d.text((X,Y+i*int(S*1.55)),t,font=f,fill=(43,29,34),anchor='la' if left else 'ra',stroke_width=7,stroke_fill=(255,255,255))
sh=Image.new('RGBA',im.size,(0,0,0,0)); sh.paste((0,0,0,60),mask=txt.split()[3])
sh=sh.transform(im.size,Image.AFFINE,(1,0,-4,0,1,-6)).filter(ImageFilter.GaussianBlur(6))
Image.alpha_composite(Image.alpha_composite(im,sh),txt).convert('RGB').save(out,quality=95)
print('ok',out)
