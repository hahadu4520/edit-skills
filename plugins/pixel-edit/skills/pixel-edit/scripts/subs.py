from PIL import Image,ImageDraw,ImageFont
import os; F=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fonts','SourceHanSansSC-Heavy.otf')
def sub_layer(text,W=1080,H=1440,size=54,cy=1124,stroke=7):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    f=ImageFont.truetype(F,size)
    d.text((W//2,cy),text,font=f,fill=(255,255,255,255),anchor='mm',stroke_width=stroke,stroke_fill=(0,0,0,255))
    return im
