# All C-shot cards in the v3 agent-app pixel style. card_frame(t) -> 1080x1440 RGB (no PiP / subtitles).
from acards import *
TL=lambda sub,title:('title','',title,sub)
P_GIT='帮我检查电脑有没有装 Git，没有的话帮我装上。'
P_INIT='帮我在这个项目文件夹开启 Git。'
P_PUSH='[@GitHub] 帮我把整个项目打包，推送到我自己的 GitHub 仓库。'
SAVES=[('V4','改成深色主题','5 分钟前',False),('V3','导航栏加了博客入口','1 小时前',False),('V2','[首页配色换成粉色]','昨天',True),('V1','第一版首页','3 天前',False)]
def conns(gh_done):
    return [(('tile','D',(66,133,244)),'云端硬盘',('btn','已连接',(222,244,228),(46,124,74))),
            (('tile','N',(110,96,150)),'笔记',('btn','连接',UB,(255,255,255))),
            (('tile','G',(36,41,47)),'GitHub' if gh_done else '[GitHub]',('btn','[已连接]',(222,244,228),(46,124,74)) if gh_done else ('btn','连接',UB,(255,255,255))),
            (('tile','C',OR),'日历',('btn','连接',UB,(255,255,255)))]
# id -> (blocks, [(t_from, mood, bubble)])
C={
 'c1':([TL('my-portfolio','用 Agent 做项目'),('you',['帮我把作品集网站的首页做好。']),('agent',['首页做好了，打开就能预览。','建议现在用 [Git] 给项目存个档，做第一次 〔commit〕，改坏了随时能退回。'])],[(3.0,'idle','首页做好啦')]),
 'c2':([TL('my-portfolio','用 Agent 做项目'),('you',['好，帮我存档。']),('agent',['已完成第一次 commit：「首页完成」。','要不要推送到 [GitHub]？换台电脑也能接着做。'])],[(6.23,'happy','存好了！')]),
 'c3':([('you',['把博客板块整个重做一遍。']),('agent',['长任务进行中…',('bar','重做博客板块  {n} / 20',0.25,0.7,8.4,13.3),('checks',['读取项目结构','新建分支 blog-redesign','改写 6 个页面的样式','[git commit] 博客页改版','运行测试：全部通过','推送到 〔GitHub〕'],8.6,0.45)])],[(8.37,'idle','干活中…'),(11.6,'happy','都存好了')]),
 'c2a':([TL('第一步','让 Agent 帮你装 Git'),('prompt',P_GIT,'对 Agent 说')],[(61.73,'idle','等你输入…'),(66.0,'happy','收到！')]),
 'c2b':([TL('第一步','让 Agent 帮你装 Git'),('you',[P_GIT]),('agent',['检查过了，你的电脑已经装好了 Git：',('term',['$ git --version','[git version 2.39.5]']),'没装的话，我会直接帮你装上。'])],[(69.67,'happy','搞定！')]),
 'c3a':([TL('第二步','在项目里开启 Git'),('prompt',P_INIT,'对 Agent 说')],[(84.10,'idle','等你输入…'),(86.6,'happy','收到！')]),
 'c3b':([TL('第二步','在项目里开启 Git'),('you',[P_INIT]),('agent',['好了，已经在 my-novel 开启了 [Git 仓库]。','以后你说「存档」，我就帮你存一个版本。'])],[(87.5,'happy','开好了！')]),
 'c4a':([TL('my-site','每次存档都有记录'),('slots','存档记录',SAVES)],[(110.33,'idle','想回到哪一版？')]),
 'c4b':([TL('my-site','V2 改了什么'),('diff',dict(head='style.css',sub='改了 2 处',lines=[(' ','.header {'),('-','  background: #4a90d9;'),('+','  background: [#f4a6c0];'),(' ','}'),(' ','.button {'),('-','  color: #ffffff;'),('+','  color: #5a2a3a;'),(' ','}')]))],[(114.13,'idle','原来改了这里')]),
 'c5a':([TL('设置','连接器'),('rows',dict(sub='让 Agent 能用你的其他工具',rows=conns(False)))],[(176.8,'idle','连上 GitHub 吧')]),
 'c5a2':([TL('设置','连接器'),('rows',dict(sub='让 Agent 能用你的其他工具',rows=conns(True)))],[(184.67,'happy','连上了！')]),
 'c5b':([TL('my-site','一句话推到 GitHub'),('prompt',P_PUSH,'对 Agent 说 · 已连接 GitHub')],[(186.6,'idle','等你输入…'),(191.0,'happy','收到！')]),
 'c5c':([TL('my-site','一句话推到 GitHub'),('you',['@GitHub 帮我把整个项目打包，推送到我自己的 GitHub 仓库。']),('agent',['完成了！新建了仓库，所有文件和存档记录都推上去了：',('link','[github.com/du/my-site]')])],[(193.17,'happy','推上去了！')]),
 'c6a':([TL('GitHub','du / my-site'),('rows',dict(sub='[23 次存档 · 都在云端]',rows=[('dir','blog','加了博客'),('file','index.html','深色主题'),('file','style.css','粉色配色'),('file','README.md','第一版')],btn=('〔复制链接〕',(47,158,88))))],[(203.27,'idle','全在云端'),(210.6,'happy','发给朋友吧')]),
 'c6b':([TL('朋友的电脑','别人也能一键下载'),('you',['帮我把这个项目下载下来：',('link','[github.com/du/my-site]')],'friend'),('agent',['已下载到 〔~/my-site〕，打开就能用。'])],[(213.0,'happy','下载好了！')]),
 'c7a':([TL('网站','已经上线啦'),('page',dict(url='my-site.pages.dev')),('toast','已推送到 [GitHub]')],[(223.63,'idle','网站上线了'),(228.0,'happy','自动更新！')]),
 'c7b':([TL('Cloudflare','自动部署'),('rows',dict(head='部署 my-site',sub='来源：GitHub · du/my-site',reveal=(230.3,0.55),rows=[('check','连接 GitHub 仓库',None),('check','安装依赖、构建',None),('check','上传到全球节点',None),('check','[部署成功]','pages.dev')]))],[(230.07,'idle','部署中…'),(232.4,'happy','成功！')]),
 'c7c':([TL('手机','随时打开'),('page',dict(url='[my-site.pages.dev]',narrow=True))],[(234.27,'happy','手机也能看')]),
 'c8a':([TL('GitHub','朋友提交了修改'),('diff',dict(head='改了首页文案 #12',sub='朋友想把 1 个改动合并进来',lines=[('-','<h1>欢迎来到我的网站</h1>'),('+',"<h1>Hi, I'm du.</h1>")])),('rows',dict(rows=[('check','没有冲突，可以合并',None)],btn=('[同意合并]',(47,158,88))))],[(268.2,'idle','要合并吗？')]),
}
def T(a,b): return ('type',a,b)
SCHED=[('c1',3.0,6.23,[(1,3.45),(2,3.95)]),('c2',6.23,8.37,[(1,6.6)]),('c3',8.37,13.33,[(1,10.4),(2,11.3)]),
 ('c2a',61.73,69.67,T(62.3,65.6)),('c2b',69.67,74.30,[(1,70.6)]),
 ('c3a',84.10,87.50,T(84.4,86.4)),('c3b',87.50,90.10,[(1,88.3)]),
 ('c4a',110.33,114.13,[(1,112.7)]),('c4b',114.13,116.67,[(1,114.6)]),
 ('c5a',176.80,184.67,[(1,181.3)]),('c5a2',184.67,186.60,[(1,185.0)]),('c5b',186.60,193.17,T(187.3,190.6)),('c5c',193.17,197.33,[(1,194.0)]),
 ('c6a',203.27,213.0,[(1,204.9),(2,210.8)]),('c6b',213.0,217.40,[(1,213.4),(2,216.3)]),
 ('c7a',223.63,230.07,[(1,228.0)]),('c7b',230.07,234.27,[(1,232.6)]),('c7c',234.27,236.57,[(1,234.6)]),
 ('c8a',268.20,270.63,[(1,268.5)])]
FIRST={3.0,61.73,84.10,110.33,176.80,203.27,223.63,268.20}
NOSLIDE={'c5a2'}
# conversation cards shown as real-looking chat screenshots (rendered from HTML in ../screenshots)
import json
import os; SHOTDIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','screenshots')+'/'
SHOTS={'c2b','c3b','c5c','c6b'}
_SHOT={}; _META=json.load(open(SHOTDIR+'meta.json'))
def _ld(n):
    if n not in _SHOT: _SHOT[n]=Image.open(SHOTDIR+n+'.png').convert('RGB')
    return _SHOT[n]
def shot_img(cid,t,hl):
    """sweep each highlighted mark in from the left (stage k = marks 1..k lit, rendered by the browser)."""
    im=_ld(cid)
    for key,ht in hl:
        p=smooth((t-ht)/0.28)
        if p<=0: continue
        lit=_ld(f'{cid}_h{key}'); im=im.copy()
        for m in _META[cid]:
            if m['k']!=key: continue
            for x0,y0,x1,y1 in m['r']:
                bx=(int(x0)-4,int(y0)-2,int(x0-4+(x1-x0+8)*p),int(y1)+2)
                if bx[2]>bx[0]: im.paste(lit.crop(bx),bx[:2])
    return im
def card_frame(t):
    for cid,a,b,hl in SCHED:
        if a<=t<b: break
    blocks,bub=C[cid]
    mood,text_=bub[0][1],bub[0][2]
    for tb,m,tx in bub:
        if t>=tb: mood,text_=m,tx
    typing=(hl[1],hl[2]) if isinstance(hl,tuple) else None
    hls=[] if typing else hl
    enter=1.0 if (a in FIRST or cid in NOSLIDE) else clamp((t-a)/0.22)
    if cid in SHOTS: return shot_scene(shot_img(cid,t,hls),t,mood,text_,enter=enter),a
    return scene_image(blocks,t,hls,typing,mood,text_,enter),a
