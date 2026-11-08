# Segment 22: pixel summary card (full frame), du stays in the bottom-right circle.
import os; WORK=os.environ.get('PIXEL_WORK',os.path.abspath('work'))  # 中间文件目录
from banim import *
def sum_world(sc,t):
    d=sc.d; sc.grass(71)
    for i,(tx,ty) in enumerate([(14,74),(32,62),(256,70),(238,60),(12,236),(30,246)]): sc.tree(tx,ty,10 if i%2 else 12,i+70)
    sc.path([(-4,224),(170,224)],6,'dirt',seed=11,smooth=False)
    sc.house(30,180,OR,smoke=True)
    for i in range(3): sprite(sc.im,82+i*8,206+(i%2)*2,["..o..",".oLo.","oLCDo",".oDo..".strip('.') and ".oDo.","..o.."],{'o':INK,'L':(255,255,255),'C':(110,190,240),'D':(70,130,200)})
def sum_ui(sc,t):
    u=sc.u
    def head(s):
        window(s.ui,(20,12,250,44)); bigtext(s.ui,(135-(tw('一张图记住')+4),16),'一张图记住',INK,scale=2)
    pop_into(sc.ui,t,0.05,head,(20,12,251,45))
    def left(s):
        uu=s.u; window(s.ui,(12,56,132,170))
        uu.rectangle((22,64,52,80),fill=INK); uu.rectangle((23,65,51,79),fill=OR); text(uu,(27,65),'Git',(255,255,255))
        text(uu,(58,65),'在你电脑里',(150,116,96))
        for i,(n,a,b) in enumerate([('1','存档','回到任意版本'),('2','分支','同时试几套方案')]):
            y=88+i*38; uu.rectangle((22,y,34,y+12),fill=OR); text(uu,(25,y-1),n,(255,255,255)); bigtext(s.ui,(40,y-3),a,INK,scale=1); text(uu,(40,y+13),b,(150,116,96))
    def right(s):
        uu=s.u; window(s.ui,(138,56,258,170))
        uu.rectangle((148,64,192,80),fill=INK); uu.rectangle((149,65,191,79),fill=PURPLE); text(uu,(153,65),'GitHub',(255,255,255))
        text(uu,(198,65),'在云端',(150,116,96))
        for i,(n,a) in enumerate([('1','云端备份'),('2','部署上线'),('3','多人协作')]):
            y=88+i*24; uu.rectangle((148,y,160,y+12),fill=PURPLE); text(uu,(151,y-1),n,(255,255,255)); text(uu,(166,y-1),a,INK)
    pop_into(sc.ui,t,0.35,left,(12,56,133,171)); pop_into(sc.ui,t,0.75,right,(138,56,259,171))
SUMMARY=dict(world=sum_world,ui=sum_ui,mood='golden',push=0.02)
if __name__=='__main__':
    a=BAnim(SUMMARY['world'],SUMMARY['ui'],mood='golden',push=0.02,dur=3)
    a.frame(2.0).save(WORK+'/full/test_sum.png')
