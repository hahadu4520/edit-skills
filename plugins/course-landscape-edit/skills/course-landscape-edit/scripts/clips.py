import json,subprocess,os
P=os.environ.get('MAT','../素材/');R='../rec/'
SD=P+'seedance 生成.mov';LB=P+'连接多维表格.mov';D=P+'策划新视频.mov';RC=R+'重新策划.mov';FS=R+'连接器飞书.mov'
RX=(373.2-367.2)+(379.415-378.87)+(388.33-384.585)+(399.6-399.5)
CL={
'R9':[(0,17.1,RC,0,12.2,(900,0,1800),(300,0,2300))],
'R10':[(0,8.5,SD,0,4.5,(0,700,1550),(0,700,1550)),(8.5,14.7,SD,4.5,10,(0,500,1650),(0,500,1650)),(14.7,19.4,SD,17,30,(0,0,1600),(0,0,1600))],
'R10P':[(0,10,LB,6,16,(715,130,2133),(715,130,2133))],
'RX':[(0,RX,D,22,33,(500,450,2100),(500,400,2100))],
'R12':[(0,11,FS,0,9.9,(0,0,2848),(300,0,2548)),(11,19.7,LB,0,3,(0,560,1600),(0,560,1600))],
'R13':[(0,15.7,LB,13,60,(0,400,1650),(0,150,1650))],
}
c=json.load(open('clips.json'))
for tag,cl in CL.items():
    L=[]
    for k,(a,b,src,s0,s1,b0,b1) in enumerate(cl):
        d=f'rec/{tag}_{k}'
        if os.path.isdir(d): subprocess.run(['rm','-rf',d])
        os.makedirs(d)
        f=(b-a)/(s1-s0)
        subprocess.run(['ffmpeg','-loglevel','error','-y','-ss',str(s0),'-t',str(s1-s0),'-i',src,'-vf',f'setpts=PTS*{f},fps=30','-q:v','3',f'{d}/%05d.jpg'],check=True)
        L.append([a,b,d,list(b0),list(b1)])
    c[tag]=L
json.dump(c,open('clips.json','w'))
print({k:[len(os.listdir(x[2])) for x in c[k]] for k in CL})
