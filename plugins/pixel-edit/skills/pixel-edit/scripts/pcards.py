# Pixel-style "screen recording" cards for the C shots: a pixel OS window over the HD-2D world,
# laid out on the 270x360 grid. Highlights sweep in, prompts type out character by character.
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
from banim import *
WX0,WY0,WX1,WY1=20,30,250,206        # window (stays clear of the PiP circle and subtitle line)
CX0=WX0+7; CX1=WX1-7               # content box
LH=15
PAPER=(255,248,234); BAR=(64,52,86); MUTE=(150,128,116); HLC=(255,226,72)
UB=(52,44,70)
def seg(s):
    """'text [hl1] more {hl2}' -> segments; [x]=key1, {x}=key2."""
    out=[]; i=0; cur=''; 
    while i<len(s):
        ch=s[i]
        if ch in '[〔':
            if cur: out.append((cur,0)); cur=''
            j=s.index(']' if ch=='[' else '〕',i); out.append((s[i+1:j],1 if ch=='[' else 2)); i=j+1; continue
        cur+=ch; i+=1
    if cur: out.append((cur,0))
    return out
class Lay:
    def __init__(s): s.ops=[]; s.rects={}; s.y=WY0+20
    def text_flow(s,segs,x0,x1,col=INK,hcol=None,lh=LH,n=None,sc=1):
        """lay out segments with wrapping; returns list of draw ops and records key rects."""
        x=x0; y=s.y; cnt=0
        for txt,k in segs:
            for ch in txt:
                if n is not None and cnt>=n: break
                w=tw(ch)*sc
                if x+w>x1 and ch not in '，。、：；！？」': x=x0; y+=lh
                c=(hcol or col) if k else col
                s.ops.append(('t',x,y,ch,c,k) if sc==1 else ('bigc',x,y+2,ch,c)); 
                if k: s.rects.setdefault(k,[]).append((x,y,x+w,y+12*sc))
                x+=w; cnt+=1
        s.y=y+lh; return x,y
def merge_rects(rs):
    rows={}
    for x0,y0,x1,y1 in rs: rows.setdefault(y0,[]).append((x0,x1))
    return [(min(a for a,_ in v),y,max(b for _,b in v),y+12) for y,v in sorted(rows.items())]
def build(card,typed_n=None):
    L=Lay(); u=[]
    for b in card['blocks']:
        k=b[0]
        if k=='hint': L.ops.append(('t',CX0,L.y,b[1],MUTE)); L.y+=LH+4
        elif k=='user':
            segs=seg(b[1]); w=sum(tw(t) for t,_ in segs)
            bw=min(CX1-CX0-30,w)+12; x0=CX1-bw
            L2=Lay(); L2.y=L.y+4; L2.text_flow(segs,x0+6,CX1-6,(255,255,255),(255,226,140))
            h=L2.y-L.y+2
            L.ops.append(('box',x0,L.y,CX1,L.y+h,UB,None)); L.ops+=L2.ops
            for kk,v in L2.rects.items(): L.rects.setdefault(kk,[]).extend(v)
            L.y+=h+8
        elif k=='who':
            L.ops.append(('box',CX0,L.y+2,CX0+9,L.y+11,OR,None)); L.ops.append(('t',CX0+13,L.y,b[1],MUTE)); L.y+=LH+2
        elif k=='para': L.text_flow(seg(b[1]),CX0,CX1); L.y+=4
        elif k=='term':
            y0=L.y; L.y+=5; L2=L
            for ln in b[1]: L.text_flow(seg(ln),CX0+6,CX1-6,(232,226,244),(255,236,150))
            L.ops.insert(0,('box',CX0,y0,CX1,L.y+3,(43,38,52),None)); L.y+=10
        elif k=='input':
            y0=L.y; L.y+=6; full=b[1]; n=len(full) if typed_n is None else typed_n
            x,y=L.text_flow(seg(full),CX0+6,CX1-6,INK,(108,80,210),n=n,sc=2,lh=28)
            if typed_n is not None: L.ops.append(('caret',x+1,y))
            h=max(L.y-y0+22,100)
            L.ops.insert(0,('box',CX0,y0,CX1,y0+h,(255,255,255),OR))
            L.ops.append(('box',CX1-18,y0+h-17,CX1-5,y0+h-4,OR,None)); L.ops.append(('t',CX1-14,y0+h-18,'↑',(255,255,255)))
            L.ops.append(('t',CX0+6,y0+h-16,b[2] if len(b)>2 else 'Agent 模式',(176,160,150)))
            L.y=y0+h+8
        elif k=='h2': L.ops.append(('big',CX0,L.y,b[1],INK)); L.y+=26
        elif k=='sub': L.text_flow(seg(b[1]),CX0,CX1,MUTE); L.y+=4
        elif k=='list':
            y0=L.y; rh=b[2] if len(b)>2 else 18
            for i,(bt,bc,txt,right) in enumerate(b[1]):
                yy=y0+4+i*rh
                if bt=='✓': L.ops.append(('check',CX0+6,yy+2))
                elif bt=='●': L.ops.append(('box',CX0+6,yy+3,CX0+12,yy+9,OR,None))
                elif bt: L.ops.append(('box',CX0+5,yy,CX0+7+tw(bt)+4,yy+12,bc,None)); L.ops.append(('t',CX0+7,yy-1,bt,(255,255,255)))
                L.y=yy-1; L.text_flow(seg(txt),CX0+(14 if bt in('✓','●') else 13+tw(bt)),CX1-6)
                if right:
                    if isinstance(right,tuple):
                        rt,rc,rf=right; rs=seg(rt); rw=sum(tw(t) for t,_ in rs)+8
                        L.ops.append(('box',CX1-6-rw,yy-1,CX1-6,yy+12,rc,None)); L.y=yy-1; L.text_flow(rs,CX1-2-rw,CX1-4,rf,rf)
                    else: L.ops.append(('t',CX1-6-tw(right),yy-1,right,(176,160,150)))
                if i: L.ops.append(('line',CX0+2,yy-3,CX1-2,(236,226,210)))
            L.ops.insert(0,('box',CX0,y0,CX1,y0+len(b[1])*rh+4,(255,255,255),(220,206,186)))
            L.y=y0+len(b[1])*rh+10
        elif k=='diff':
            y0=L.y; L.y+=3
            for kind,ln in b[1]:
                if kind=='-': L.ops.append(('box',CX0+1,L.y-1,CX1-1,L.y+12,(253,226,224),None)); col=(178,64,48)
                elif kind=='+': L.ops.append(('box',CX0+1,L.y-1,CX1-1,L.y+12,(222,244,228),None)); col=(46,124,74)
                else: col=INK
                L.text_flow(seg(ln),CX0+6,CX1-4,col,col,lh=14)
            L.ops.insert(0,('box',CX0,y0,CX1,L.y+2,(255,255,255),(220,206,186))); L.y+=8
        elif k=='link':
            y0=L.y; L.y+=5; L.ops.append(('box',CX0+6,y0+5,CX0+18,y0+17,(36,41,47),None)); L.ops.append(('t',CX0+9,y0+4,'G',(255,255,255)))
            L.text_flow(seg(b[1]),CX0+24,CX1-6); L.ops.insert(0,('box',CX0,y0,CX1-30,L.y+3,(255,255,255),(220,206,186))); L.y+=10
        elif k=='btn':
            rs=seg(b[1]); w=sum(tw(t) for t,_ in rs)+14; x0=CX0 if len(b)<4 else CX1-w
            L.ops.append(('box',x0,L.y,x0+w,L.y+16,b[2],None)); yy=L.y; L.y+=2; L.text_flow(rs,x0+7,x0+w,(255,255,255),(255,255,255)); L.y=yy+24
        elif k=='gap': L.y+=b[1]
        elif k=='browser':
            y0=L.y; L.ops.append(('box',CX0,y0,CX1,y0+16,(236,228,214),None)); L.y=y0+2
            L.ops.append(('box',CX0+20,y0+2,CX1-6,y0+14,(255,255,255),None)); L.text_flow(seg(b[1]),CX0+24,CX1-8,MUTE,MUTE)
            L.ops.append(('t',CX0+6,y0+1,'◆',(150,200,140)))
            L.ops.append(('box',CX0,y0+16,CX1,y0+120,(253,226,206),None))
            L.ops.append(('bigc',CX0+12,y0+28,"Hi, I'm du.",(70,44,40))); L.ops.append(('t',CX0+12,y0+56,'AI tools for creators.',(110,80,70)))
            L.ops.append(('t',CX0+12,y0+72,'Tutorials, templates, tiny apps.',(150,116,100)))
            L.ops.append(('box',CX0+12,y0+94,CX0+92,y0+110,OR,None)); L.ops.append(('t',CX0+18,y0+96,'Get started →',(255,255,255)))
            L.ops.append(('frame',CX0,y0,CX1,y0+120)); L.y=y0+128
        elif k=='toast':
            y0=L.y; L2=Lay(); L2.y=y0+3; L2.text_flow(seg(b[1]),CX0+8,CX1,(255,255,255),(255,226,140))
            w=max(x for op in L2.ops if op[0]=='t' for x in [op[1]+tw(op[3])])-CX0+8
            L.ops.append(('box',CX0,y0,CX0+w,y0+18,UB,None)); L.ops+=L2.ops
            for kk,v in L2.rects.items(): L.rects.setdefault(kk,[]).extend(v)
            L.y=y0+24
        elif k=='phone':
            x0,y0=CX0+40,L.y; x1,y1=x0+110,L.y+176
            L.ops.append(('box',x0,y0,x1,y1,(31,27,34),None)); L.ops.append(('box',x0+5,y0+6,x1-5,y1-6,(253,226,206),None))
            L.ops.append(('box',x0+12,y0+14,x1-12,y0+26,(236,228,214),None)); L.y=y0+13; L.text_flow(seg(b[1]),x0+16,x1-12,MUTE,MUTE)
            L.ops.append(('bigc',x0+12,y0+44,"Hi, I'm",(70,44,40))); L.ops.append(('bigc',x0+12,y0+68,'du.',(70,44,40)))
            L.ops.append(('t',x0+12,y0+96,'AI tools for',(110,80,70))); L.ops.append(('t',x0+12,y0+110,'creators.',(110,80,70)))
            L.ops.append(('box',x0+12,y0+132,x0+80,y0+146,OR,None)); L.ops.append(('t',x0+16,y0+133,'Get started',(255,255,255)))
            L.y=y1+6
    return L
CARDS={
 'c1':dict(title='Claude Code · my-portfolio',blocks=[('user','帮我把作品集网站的首页做好'),('who','Claude'),('para','首页做好了，打开 index.html 就能预览。'),('para','建议现在用 [Git] 给项目存个档：我帮你初始化仓库，再做第一次 〔commit〕。改坏了随时能退回这一版。')]),
 'c2':dict(title='Claude Code · my-portfolio',blocks=[('user','好，帮我存档'),('who','Claude'),('para','已完成第一次 commit：「首页完成」。'),('para','要不要把代码推送到 [GitHub]？换一台电脑也能接着做，还能一键部署上线。')]),
 'c3':dict(title='Claude Code · my-portfolio',blocks=[('user','把博客板块整个重做一遍'),('who','Claude · 长任务进行中'),
    ('list',[('●','', '重做博客板块      14 / 20',None),('✓','','读取项目结构',None),('✓','','新建分支 blog-redesign',None),('✓','','改写 6 个页面的样式',None),('✓','','[git commit] 博客页改版',None),('✓','','运行测试：全部通过',None),('✓','','推送到 〔GitHub〕',None)],16)]),
 'c2a':dict(title='Claude Code · 新对话',blocks=[('hint','直接对 Agent 说这一句：'),('input','帮我检查电脑有没有装 Git，没有的话帮我装上。')],type=True),
 'c2b':dict(title='Claude Code · 新对话',blocks=[('user','帮我检查电脑有没有装 Git，没有的话帮我装上。'),('who','Claude'),('para','检查过了，你的电脑已经装好了 Git：'),('term',['$ git --version','[git version 2.39.5]']),('para','如果没装，我会直接帮你装上。')]),
 'c3a':dict(title='Claude Code · my-novel',blocks=[('hint','新建项目文件夹之后，输入：'),('input','帮我在这个项目文件夹开启 Git。')],type=True),
 'c3b':dict(title='Claude Code · my-novel',blocks=[('user','帮我在这个项目文件夹开启 Git。'),('who','Claude'),('para','好了，已经在 my-novel 开启了 [Git 仓库]。'),('para','以后你说「存档」，我就帮你存一个版本。')]),
 'c4a':dict(title='my-site · 存档记录',blocks=[('h2','存档记录'),('sub','每一次存档都在这里'),
    ('list',[('V4',OR,'改成深色主题','5 分钟前'),('V3',(170,156,146),'导航栏加了博客入口','1 小时前'),('V2',(170,156,146),'[首页配色换成粉色]','昨天'),('V1',(170,156,146),'第一版首页','3 天前')],20)]),
 'c4b':dict(title='my-site · V2 改了什么',blocks=[('h2','V2 改了什么'),('sub','style.css · 改了 3 行'),
    ('diff',[(' ','.header {'),('-','- background: #4a90d9;'),('+','+ background: [#f4a6c0];'),(' ','}'),(' ','.button {'),('-','- color: #ffffff;'),('+','+ color: #5a2a3a;'),(' ','}')])]),
 'c5a':dict(title='设置 · 连接器',blocks=[('h2','连接器'),('sub','让 Agent 能用你的其他工具'),
    ('list',[('D',(66,133,244),'云端硬盘',('已连接',(222,244,228),(46,124,74))),('N',UB,'笔记',('连接',UB,(255,255,255))),('G',(36,41,47),'[GitHub]',('连接',UB,(255,255,255))),('S',OR,'日历',('连接',UB,(255,255,255)))],20)]),
 'c5a2':dict(title='设置 · 连接器',blocks=[('h2','连接器'),('sub','让 Agent 能用你的其他工具'),
    ('list',[('D',(66,133,244),'云端硬盘',('已连接',(222,244,228),(46,124,74))),('N',UB,'笔记',('连接',UB,(255,255,255))),('G',(36,41,47),'GitHub',('[已连接]',(222,244,228),(46,124,74))),('S',OR,'日历',('连接',UB,(255,255,255)))],20)]),
 'c5b':dict(title='Claude Code · my-site',blocks=[('hint','在对话框里 @GitHub：'),('input','[@GitHub] 帮我把整个项目打包，推送到我自己的 GitHub 仓库。','已连接：GitHub')],type=True),
 'c5c':dict(title='Claude Code · my-site',blocks=[('user','@GitHub 帮我把整个项目打包，推送到我自己的 GitHub 仓库。'),('who','Claude'),('para','完成了！新建了仓库，所有文件和存档记录都推上去了：'),('link','[github.com/du/my-site]')]),
 'c6a':dict(title='浏览器 · github.com/du/my-site',blocks=[('h2','du / my-site'),('sub','☁ [23 次存档 · 都在云端]'),
    ('list',[('▸',(196,146,96),'blog','加了博客'),('▸',(170,156,146),'index.html','深色主题'),('▸',(170,156,146),'style.css','粉色配色'),('▸',(170,156,146),'README.md','第一版')],18),('btn','↓ 〔复制链接〕',(47,158,88))]),
 'c6b':dict(title='朋友的 Claude Code · 新对话',blocks=[('user','帮我把这个项目下载下来：[github.com/du/my-site]'),('who','Claude'),('para','已下载到 〔~/my-site〕，打开就能用。')]),
 'c7a':dict(title='浏览器 · my-site.pages.dev',blocks=[('browser','my-site.pages.dev'),('gap',4),('toast','已推送到 [GitHub]')]),
 'c7b':dict(title='Cloudflare · Workers & Pages',blocks=[('h2','部署 my-site'),('sub','来源：GitHub · du/my-site'),
    ('list',[('✓','','连接 GitHub 仓库',None),('✓','','安装依赖、构建',None),('✓','','上传到全球节点',None),('✓','','[部署成功]','pages.dev')],20)]),
 'c7c':dict(title='手机预览',blocks=[('phone','[my-site.pages.dev]')]),
 'c8a':dict(title='github.com/du/my-site/pull/12',blocks=[('h2','改了首页文案 #12'),('sub','朋友 想把 1 个改动合并进 main'),
    ('diff',[('-','- <h1>欢迎来到我的网站</h1>'),('+',"+ <h1>Hi, I'm du.</h1>")]),('list',[('✓','','没有冲突，可以合并',None)],18),('btn','[同意合并]',(47,158,88),'r')]),
}
def typelen(cid):
    return sum(len(t) for t,_ in seg([b for b in CARDS[cid]['blocks'] if b[0]=='input'][0][1]))
_LAY={}
def layout(cid,n=None):
    key=(cid,n)
    if key not in _LAY:
        if len(_LAY)>200: _LAY.clear()
        _LAY[key]=build(CARDS[cid],n)
    return _LAY[key]
def draw_card(sc,cid,t,hl=(),typing=None,slide=0):
    """hl: [(key, t_start)], typing: (t0,t1) for input cards."""
    u=sc.u; img=sc.ui
    n=None
    if typing:
        N=typelen(cid); n=int(round(N*clamp((t-typing[0])/(typing[1]-typing[0]))))
    L=layout(cid,n)
    dy=slide
    # window
    u.rectangle((WX0+3,WY0+3+dy,WX1+3,WY1+3+dy),fill=(40,30,50,110))
    u.rectangle((WX0-1,WY0-1+dy,WX1+1,WY1+1+dy),fill=INK); u.rectangle((WX0,WY0+dy,WX1,WY1+dy),fill=PAPER)
    u.rectangle((WX0,WY0+dy,WX1,WY0+13+dy),fill=BAR)
    for k,c in enumerate([(240,96,96),(250,200,90),(110,200,120)]): u.rectangle((WX0+5+k*7,WY0+5+dy,WX0+9+k*7,WY0+9+dy),fill=c)
    text(u,(WX0+28,WY0+dy),CARDS[cid]['title'],(214,206,240))
    # highlights under text
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
        if k in ('box','line'): continue
        if k=='t': text(u,(op[1],op[2]+dy),op[3],INK if (len(op)>5 and op[5] in lit) else op[4])
        elif k=='box':
            _,x0,y0,x1,y1,f,o=op
            if o: u.rectangle((x0,y0+dy,x1,y1+dy),fill=o); u.rectangle((x0+1,y0+1+dy,x1-1,y1-1+dy),fill=f)
            else: u.rectangle((x0,y0+dy,x1,y1+dy),fill=f)
        elif k=='line': u.line([(op[1],op[2]+dy),(op[3],op[2]+dy)],fill=op[4])
        elif k=='check': x,y=op[1],op[2]+dy; u.line([(x,y+4),(x+2,y+6),(x+6,y+1)],fill=(47,158,88),width=2)
        elif k=='caret':
            if int(t*2.5)%2==0 or (typing and t<typing[1]): u.rectangle((op[1],op[2]+2+dy,op[1]+2,op[2]+26+dy),fill=OR)
        elif k=='big': bigtext(img,(op[1],op[2]+dy-2),op[3],op[4],scale=2)
        elif k=='bigc': bigtext(img,(op[1],op[2]+dy-2),op[3],op[4],scale=2)
        elif k=='frame': u.rectangle((op[1],op[2]+dy,op[3],op[4]+dy),outline=(200,186,166))
    # redraw highlighted text on top of marker already done by ordering? markers drawn first, text after: ok
MON=(6,8,264,222)   # monitor bezel; screen inset 7px
def desk_world(sc,t):
    d=sc.d; px=sc.px
    # room wall (warm, dithered stripes) and wooden desk
    d.rectangle((0,0,W,H),fill=(238,224,204))
    for x in range(0,W,12):
        for y in range(0,236):
            if (y//2+x//12)%2==0 and y%2==0: px[x,y]=(230,214,192,255)
    DY=246
    d.rectangle((0,DY,W,H),fill=(196,142,96)); d.line([(0,DY),(W,DY)],fill=(150,100,64)); d.line([(0,DY+1),(W,DY+1)],fill=(222,174,126))
    for y in range(DY+8,H,9): d.line([(0,y),(W,y)],fill=(186,132,88))
    for (x,y) in [(30,DY+20),(120,DY+40),(210,DY+60),(70,DY+80)]: d.line([(x,y),(x+26,y)],fill=(174,120,80))
    # monitor
    x0,y0,x1,y1=MON
    d.rectangle((126,y1,144,DY+2),fill=INK); d.rectangle((127,y1,143,DY+1),fill=(120,112,132))
    d.rectangle((106,DY-2,164,DY+4),fill=INK); d.rectangle((107,DY-1,163,DY+3),fill=(150,142,160))
    d.rectangle((x0,y0,x1,y1),fill=INK); d.rectangle((x0+1,y0+1,x1-1,y1-1),fill=(84,76,98)); d.line([(x0+2,y0+2),(x1-2,y0+2)],fill=(120,112,134))
    d.rectangle((x0+6,y0+6,x1-6,y1-12),fill=INK)
    px[(x0+x1)//2,y1-6]=(110,220,140,255); px[(x0+x1)//2+1,y1-6]=(110,220,140,255)
    # screen: dithered wallpaper + menu bar
    sx0,sy0,sx1,sy1=x0+7,y0+7,x1-7,y1-13
    top=(120,110,200); bot=(244,170,190)
    for y in range(sy0,sy1+1):
        tt=(y-sy0)/(sy1-sy0); band=int(tt*6); f=tt*6-band; c0=lerpc(top,bot,band/6); c1=lerpc(top,bot,(band+1)/6)
        d.line([(sx0,y),(sx1,y)],fill=c0)
        if f>0.5:
            for x in range(sx0,sx1+1):
                if ((x+y)%2==0 if f<0.75 else not (x%2 and y%2)): px[x,y]=c1+(255,)
    d.rectangle((sx0,sy0,sx1,sy0+9),fill=(250,244,236)); d.line([(sx0,sy0+10),(sx1,sy0+10)],fill=INK)
    sc.sparkle(sx0+6,sy0+4,(232,98,62))
    for i,w_ in enumerate((10,8,10)): d.rectangle((sx0+16+i*18,sy0+3,sx0+16+i*18+w_,sy0+5),fill=(150,128,116))
    hh=int(t*2)%2; d.rectangle((sx1-30,sy0+3,sx1-26,sy0+5),fill=(150,128,116)); d.rectangle((sx1-20,sy0+3,sx1-6,sy0+5),fill=(150,128,116))
    # keyboard + mug on the desk (left of the PiP circle)
    kx,ky=18,DY+18
    d.rectangle((kx,ky,kx+128,ky+30),fill=INK); d.rectangle((kx+1,ky+1,kx+127,ky+29),fill=(232,226,236))
    for r in range(3):
        for c in range(14):
            xx=kx+5+c*9; yy=ky+5+r*8; d.rectangle((xx,yy,xx+6,yy+5),fill=(200,192,210)); d.line([(xx,yy),(xx+6,yy)],fill=(250,248,252))
    d.rectangle((kx+30,ky+22,kx+96,ky+26),fill=(200,192,210))
    mx,my=152,DY+14
    d.rectangle((mx,my,mx+12,my+16),fill=INK); d.rectangle((mx+1,my+1,mx+11,my+15),fill=(232,98,62)); d.rectangle((mx+12,my+4,mx+16,my+10),outline=INK)
    for k in range(3):
        sy=my-4-k*4-int(t*6+k)%3; d.point((mx+4+k%2*3,sy),fill=(255,255,255))
_DESK=None
def desk():
    global _DESK
    if _DESK is None: _DESK=BAnim(desk_world,lambda sc,t:None,mood='golden',focus=0.4,band=0.45,bloom=0.25,push=0,dur=10,rays=True)
    return _DESK
def card_image(cid,t,hl=(),typing=None,slide=0):
    D=desk()
    D.ui=lambda sc,tt:draw_card(sc,cid,t,hl,typing,slide)
    return D.frame(t)
if __name__=='__main__':
    tests=[('c1',5,[(1,3.4),(2,3.9)],None),('c3',12,[(1,9.3),(2,11.5)],None),('c2a',64,[],(62.3,65.6)),('c2b',72,[(1,70.6)],None),('c4a',113,[(1,112.7)],None),('c4b',116,[(1,114.6)],None),
           ('c5a2',186,[(1,185)],None),('c5b',190,[],(187.3,190.6)),('c5c',196,[(1,194)],None),('c6a',212,[(1,204.9),(2,210.8)],None),('c6b',217,[(1,213.4),(2,216.3)],None),('c7a',229,[(1,228)],None),('c7b',234,[(1,232.6)],None),('c7c',236,[(1,234.6)],None),('c8a',270,[(1,268.5)],None)]
    s=Image.new('RGB',(270*8,360*2))
    for i,(cid,t,hl,ty) in enumerate(tests):
        s.paste(card_image(cid,t,hl,ty).resize((270,360)),((i%8)*270,(i//8)*360))
    s.save(WORK+'/full/pcards.jpg',quality=88)
    card_image('c1',5,[(1,3.4),(2,3.9)]).save(WORK+'/full/pc1.png')
