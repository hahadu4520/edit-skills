import json,os
# 进度条章节名：和合成器读同一份 ../chap.json（章节起点 + 终点），名字在 ../chap_names.json
# 用法：cd kf && python gen_bar.py && node ../rl.js $PWD   → kf/lab_0.png … lab_N.png
_B=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','chap.json')))
_N=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','chap_names.json')))
CH=[(n,_B[i],_B[i+1]) for i,n in enumerate(_N)]
HEAD='<!doctype html><meta charset=utf-8><link rel=stylesheet href="../node_modules/misans/lib/Normal/MiSans-Medium.min.css"><link rel=stylesheet href="../node_modules/misans/lib/Normal/MiSans-Bold.min.css"><link rel=stylesheet href="../node_modules/misans/lib/Normal/MiSans-Heavy.min.css"><style>*{margin:0;padding:0;box-sizing:border-box}body{width:1920px;height:1080px;position:relative;overflow:hidden;font-family:MiSans}</style><body>'
def topbar(t,dark=False,labels_only=False):
    X0,X1,GAP=64,1856,8;tot=CH[-1][2];avail=X1-X0-GAP*(len(CH)-1);x=X0;h=''
    for name,a,b in CH:
        w=avail*(b-a)/tot;cur=a<=t<b;done=t>=b
        base='rgba(255,255,255,.16)' if dark else 'rgba(20,24,32,.09)'
        fill=1 if done else ((t-a)/(b-a) if cur else 0)
        if not labels_only: h+=f'<div style="position:absolute;left:{x:.1f}px;top:40px;width:{w:.1f}px;height:8px;border-radius:4px;background:{base};overflow:hidden"><div style="width:{fill*100:.1f}%;height:100%;background:#2F6BFF;border-radius:4px"></div></div>'
        col=('#fff' if dark else '#15171C') if cur else ('rgba(255,255,255,.45)' if dark else '#9AA0AA')
        h+=f'<div style="position:absolute;left:{x:.1f}px;top:58px;width:{w:.1f}px;font:{700 if cur else 500} 19px MiSans;color:{col};white-space:nowrap;overflow:hidden">{name}</div>'
        x+=w+GAP
    logo='logo_w.png' if dark else 'logo.png'
    return h
def save(n,body,bg='transparent'):
    open(n+'.html','w').write(HEAD.replace('<body>',f'<body style="background:{bg}">')+body)
# screenshot scenes: background layer = canvas + panel + box shadow
def scene(n,img,iw,ih,view,focus=None,label=None,cursor=None,ripple=False,dim=True):
    vx,vy,vw=view;s=1240/vw
    P=f'<div style="position:absolute;left:64px;top:126px;width:1240px;height:698px;border-radius:28px;overflow:hidden;box-shadow:0 20px 50px rgba(30,30,40,.10);background:#111">'
    P+=f'<img src="img/{img}" style="position:absolute;left:{-vx*s:.1f}px;top:{-vy*s:.1f}px;width:{iw*s:.1f}px;height:{ih*s:.1f}px">'
    if focus:
        fx,fy,fw,fh=focus;X,Y,Wd,Hd=(fx-vx)*s,(fy-vy)*s,fw*s,fh*s
        sh='0 0 0 3000px rgba(12,14,22,.48),' if dim else ''
        P+=f'<div style="position:absolute;left:{X-6:.1f}px;top:{Y-6:.1f}px;width:{Wd+12:.1f}px;height:{Hd+12:.1f}px;border:4px solid #2F6BFF;border-radius:16px;box-shadow:{sh}0 0 0 8px rgba(47,107,255,.18)"></div>'
        if label:
            lx,ly=label[1],label[2]
            P+=f'<div style="position:absolute;left:{lx}px;top:{ly}px;background:#2F6BFF;color:#fff;font:700 28px MiSans;padding:10px 22px;border-radius:999px;box-shadow:0 10px 24px rgba(47,107,255,.35);white-space:nowrap">{label[0]}</div>'
    if cursor:
        cx,cy=(cursor[0]-vx)*s,(cursor[1]-vy)*s
        if ripple: P+=f'<div style="position:absolute;left:{cx-34:.1f}px;top:{cy-34:.1f}px;width:68px;height:68px;border-radius:50%;background:rgba(47,107,255,.28);border:3px solid rgba(255,255,255,.9)"></div>'
        P+=f'<svg style="position:absolute;left:{cx-4:.1f}px;top:{cy-2:.1f}px" width="40" height="48" viewBox="0 0 20 24"><path d="M2 1 L2 19 L6.5 15 L9.5 22 L12.5 20.7 L9.6 14 L16 14 Z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>'
    P+='</div><div style="position:absolute;left:1336px;top:284px;width:520px;height:540px;border-radius:28px;box-shadow:0 20px 50px rgba(30,30,40,.12)"></div>'
    save(n,P,'#F4F2EE')
# 示例（第 1 集的界面截图镜头，图放 kf/img/）：
# scene('sc_R4','ui.jpg',1552,902,(560,250,660),focus=(886,378,160,52),label=('选「工作」',520,470),cursor=(985,410),ripple=True)

for i,(n,a,b) in enumerate(CH): save(f'lab_{i}',topbar((a+b)/2,False,True))
