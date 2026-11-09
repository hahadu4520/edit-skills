import json,subprocess,os
K=[(0,373.20),(378.87,379.415),(384.585,388.33),(399.50,536.1)]
def m(t):
    acc=0
    for a,b in K:
        if t<a: return acc
        if t<=b: return acc+t-a
        acc+=b-a
    return acc
TOT=m(536.1)
# 1 cut source
if not os.path.exists('../src_cut.mp4'):
    fc=''
    for i,(a,b) in enumerate(K):
        d=b-a
        fc+=f'[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={d-0.012:.3f}:d=0.012[a{i}];'
    fc+=''.join(f'[v{i}][a{i}]' for i in range(len(K)))+f'concat=n={len(K)}:v=1:a=1[v][a]'
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i','../src.mp4','-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-crf','16','-preset','fast','-r','30','-c:a','aac','-b:a','192k','../src_cut.mp4'],check=True)
# 2 subs
subs=json.load(open('subs.json'));en=open('en.txt').read().split('\n')
for k,v in {160:'第二步呢咱们就可以根据拆出来的',258:'那咱们就可以及时',259:'地去做一个放大'}.items(): subs[k][2]=v
S=[];E=[]
for i,(a,b,t) in enumerate(subs):
    if i in range(199,205) or i in range(208,214): continue
    e=en[i]
    if i==205: a,t,e=378.87,'咱们就大白话讲一下','just tell it in plain words'
    S.append([m(a),m(b),t]);E.append(e)
json.dump(S,open('subs.json','w'),ensure_ascii=False);open('en.txt','w').write('\n'.join(E))
# 3 segs (in NEW time)
K_='kf/'
def seg(a,b,layer,tag=None,**kw): d=dict(t0=a,t1=b,layer=layer,tag=tag);d.update(kw);return d
old=json.load(open('segs_v2.json'))
G=[]
# opening compare
G.append(seg(0,6.5,'cmp:chob,juice',None,cmp=[[ 'chob',8.0],['juice',8.5]]))
G.append(seg(6.5,16.4,'cmp:dog,-',None,cmp=[['dog',3.4],[None,'宠物生成成片待补']]))
G.append(seg(16.4,25.7,'cmp:-,bottle',None,cmp=[[None,'手拍原视频待补'],['bottle',0]]))
for o in old:
    a,b=o['t0'],o['t1']
    if b<=25.7 or a>=367.2 and b<=399.6: continue
    if o['layer'].startswith('clips:R9'): continue
    G.append(seg(m(a),m(b),o['layer'],o.get('tag'),**({'zoom':o['zoom']} if 'zoom' in o else {})))
# replace specific
def put(a,b,layer,tag=None):
    global G
    G=[g for g in G if not (g['t0']>=a-0.01 and g['t1']<=b+0.01)];G.append(seg(a,b,layer,tag))
put(m(320.7),m(337.8),'clips:R9')
put(m(337.8),m(357.2),'clips:R10')
put(m(357.2),m(367.2),'clips:R10P','R10 成片待补：宠物生成视频')
put(m(367.2),m(399.6)+0.0001,'clips:RX')
put(m(418.7),m(438.4),'clips:R12')
put(m(438.4),m(454.1),'clips:R13','R13 待补：写入完成后打开飞书表格')
G.sort(key=lambda g:g['t0'])
# fix continuity
for i in range(len(G)-1): G[i]['t1']=G[i+1]['t0']
G[-1]['t1']=TOT
json.dump(G,open('segs.json','w'),ensure_ascii=False,indent=0)
for g in G: print(round(g['t0'],2),round(g['t1'],2),g['layer'],g.get('tag') or '')
print('TOT',TOT,'chapters', [round(m(x),2) for x in [127.9,195.6,292.4,337.8,399.6,454.1]])
