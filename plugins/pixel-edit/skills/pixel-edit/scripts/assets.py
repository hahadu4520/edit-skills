from lib import *
INK=(46,30,36)
GIRL_PAL={'o':INK,'H':(54,38,40),'h':(96,66,60),'S':(252,218,192),'s':(232,182,154),'e':(40,26,30),'r':(242,152,142),
 'T':(198,174,168),'t':(168,144,140),'B':(134,90,62),'b':(98,64,46),'c':(242,228,204),'P':(74,64,80),'K':(44,32,38),'w':(255,255,255)}
GIRL=[
"....oooooooo....",
"...oHHHHHHHHo...",
"..oHHHhhHHHHHo..",
"..oHHhHHHHHhHo..",
".oHHHHSSSSHHHHo.",
".oHHHSSSSSSHHHo.",
".oHHSeSSSSeSHHo.",
".oHHSeSSSSeSHHo.",
".oHHrSSSSSSrHHo.",
".oHHHSSssSSHHHo.",
".oHHHHoSSoHHHHo.",
".oHHoBTTTTBoHHo.",
".oHoBBTTTTBBoHo.",
"..oBcBTttTBcBo..",
".oBBBBTTTTBBBBo.",
".oBcBcTTTTcBcBo.",
".oSoBBTTTTBBoSo.",
".oooBBBTTBBBooo.",
"...obbbbbbbbo...",
"...oPPPooPPPo...",
"...oPPPooPPPo...",
"...oPPo..oPPo...",
"...oKKo..oKKo...",
"...ooo....ooo...",
]
# 32x32 portrait bust
PORT_PAL=dict(GIRL_PAL); PORT_PAL.update({'g':(128,92,82),'m':(200,86,92),'n':(222,166,140),'l':(255,236,220)})
PORT=[
"...........oooooooooo...........",
"........oooHHHHHHHHHHooo........",
".......oHHHHHHHHHHHHHHHHo.......",
"......oHHHHhhhHHHHHhhHHHHo......",
".....oHHHHhggHHHHHHHghhHHHo.....",
"....oHHHHhgHHHHSSHHHHHghHHHo....",
"....oHHHhgHHHSSSSSSHHHHhHHHo....",
"...oHHHHhHHSSSSSSSSSSHHHhHHHo...",
"...oHHHhHHSSSSSSSSSSSSHHHhHHo...",
"...oHHHhHSSSSSSSSSSSSSSHHhHHo...",
"...oHHHHSSSSSSSSSSSSSSSSHHHHo...",
"...oHHHHSSbbbSSSSSSbbbSSHHHHo...",
"...oHHHHSSSSSSSSSSSSSSSSHHHHo...",
"...oHHHSSSoeeSSSSSSeeoSSSHHHo...",
"...oHHHSSSSweSSSSSSweSSSSHHHo...",
"...oHHHSSSSeeSSSSSSeeSSSSHHHo...",
"...oHHHSrrSSSSSSSSSSSSrrSHHHo...",
"...oHHHSSSSSSSSnSSSSSSSSSHHHo...",
"...oHHHHSSSSSSSnnSSSSSSSHHHHo...",
"...oHHHHSSSSSSSSSSSSSSSSHHHHo...",
"...oHHHHHSSSSSmmmmSSSSSHHHHHo...",
"...oHHHHHsSSSSSSSSSSSSsHHHHHo...",
"...oHHHHHHssSSSSSSSSssHHHHHHo...",
"..oHHHHHHHHHssSSSSssHHHHHHHHHo..",
"..oHHHHHHHHHotTTTTtoHHHHHHHHHo..",
"..oHHHHHHHHoTTTTTTTToHHHHHHHHo..",
".oHHHHHHHHoBBTTTTTTBBoHHHHHHHHo.",
".oHHHHHHHoBcBBTTTTBBcBoHHHHHHHo.",
"oHHHHHHHoBBBcBTTTTBcBBBoHHHHHHHo",
"oHHHHHHoBcBBBBTTTTBBBBcBoHHHHHHo",
"ooHHHHoBBBcBBcTTTTcBBcBBBoHHHHoo",
"oooooooBBBBBBBTTTTBBBBBBBooooooo",
]
PORT=[r.replace(' ','e')[:32].ljust(32,'.') for r in PORT]
# the channel mascot (haha du bear) replaces the long-haired girl as protagonist; the girl stays as a villager
GIRL_H,GIRL_PAL_H,PORT_H,PORT_PAL_H=GIRL,GIRL_PAL,PORT,PORT_PAL
BEAR_PAL={'o':INK,'F':(184,116,56),'f':(146,88,42),'L':(214,152,86),'E':(120,70,38),'M':(236,198,146),'m':(210,166,112),
 'N':(44,30,32),'w':(255,255,255),'e':(40,26,30),'r':(236,140,112),'R':(232,98,62),'Q':(176,66,40)}
BEAR=['.oooo......oooo.', 'oFEEFo....oFEEfo', 'oFEEFoooooooEEfo', '.ooLLFFFFFFFFoo.', '.oLLFFFFFFFFFFo.', 'oFLFFFFFFFFFFFfo', 'oFFFeFFFFFFeFFfo', 'oFFFeFFFFFFeFFfo', 'oFrFFFMMMMFFFrfo', 'oFFFFMMNNMMFFffo', '.oFFFMMMoMMMFfo.', '..ooFFmmmmFFoo..', '..oRRRRRRRRRRo..', '.oFFoQRRRRRoFFo.', '.oFFoFLLLLFoFfo.', '.oFFoLLLLLLofFo.', '..ooFLLLLLLFoo..', '...oFFLLLLFFo...', '...oFFFFFFffo...', '...oFFFooFFfo...', '...oFFFooFffo...', '...oFFo..oFfo...', '...oMMo..oMMo...', '...ooo....ooo...']
BEAR_PORT=['................................', '................................', '....oooo................oooo....', '...oFFFFo..............oFFFFo...', '..oFFEEFFo.oooooooooo.oFFEEfFo..', '..oFEEEEFooLLFFFFFFFFooFEEEEfo..', '..oFEEEEoLLLLFFFFFFFFFFoEEEEfo..', '..oFFEEoLLLFFFFFFFFFFFFFoEEffo..', '...oFFoLLFFFFFFFFFFFFFFFFoffo...', '....ooLLFFFFFFFFFFFFFFFFFFoo....', '.....oLFFFFFFFFFFFFFFFFFFFo.....', '....oFLFFFFFFFFFFFFFFFFFFFfo....', '....oFFFFFFFFFFFFFFFFFFFFFfo....', '....oFFFFFFeFFFFFFFFFFeFFFfo....', '....oFFFFFeweFFFFFFFFeweFFfo....', '....oFFFFFeeeFFFFFFFFeeeFFfo....', '....oFFFFFFeFFFFFFFFFFeFFFfo....', '....oFFrrFFFFMMMMMMFFFFFrrfo....', '....oFFFFFFFMMMMMMMMMFFFFFfo....', '....oFFFFFFMMMNNNNNMMMFFFffo....', '.....oFFFFFMMNwNNNNNMMFFffo.....', '.....oFFFFFMMMNNNNNMMMFFffo.....', '......oFFFFMMMMMNMMMMMFffo......', '......oFFFFMMMoMNMoMMMfffo......', '.......oFFFFmMMoooMMmfffo.......', '........ooFFFmmmmmmmffoo........', '......ooFFFFFFFFFFFFFFffoo......', '....ooFFFFFFFLLLLLFFFFFfffoo....', '...oFFFFFFFLLLLLLLLLFFFFfffo....', '..oFFFFFFFFLLLLLLLLLLFFFFfffo...', '.oFFFFFFFFFFLLLLLLLLFFFFFFfffo..', '.ooooooooooooooooooooooooooooo..']
GIRL,GIRL_PAL=BEAR,BEAR_PAL
PORT,PORT_PAL=BEAR_PORT,BEAR_PAL
X_BADGE=[
".ooooooooo.",
"oRRRRRRRRRo",
"oRwwRRRwwRo",
"oRwwwRwwwRo",
"oRRwwwwwRRo",
"oRRRwwwRRRo",
"oRRwwwwwRRo",
"oRwwwRwwwRo",
"oRwwRRRwwRo",
"oDDDDDDDDDo",
".ooooooooo.",
]
OK_BADGE=[
".ooooooooo.",
"oGGGGGGGGGo",
"oGGGGGGGwwo",
"oGGGGGGwwwo",
"oGwwGGwwwGo",
"oGwwwwwwGGo",
"oGGwwwwGGGo",
"oGGGwwGGGGo",
"oGGGGGGGGGo",
"oDDDDDDDDDo",
".ooooooooo.",
]
BADGE_PAL_X={'o':INK,'R':(226,82,82),'w':(255,255,255),'D':(170,52,60)}
BADGE_PAL_OK={'o':INK,'G':(86,182,108),'w':(255,255,255),'D':(52,128,76)}
FLOPPY=[
"oooooooo.",
"oCwwwwCoo",
"oCwwwwCCo",
"oCCCCCCCo",
"oCCllllCo",
"oCClLLlCo",
"oCClLLlCo",
"ooooooooo",
]
def floppy_pal(c): return {'o':INK,'C':c,'w':(255,255,255),'l':(236,236,236),'L':(150,150,160)}
def window(im,b,fill=(255,246,226),wood=(190,128,82)):
    d=ImageDraw.Draw(im); x0,y0,x1,y1=b
    hi=lerpc(wood,(255,230,180),.45); lo=lerpc(wood,(60,30,20),.35)
    d.rectangle(b,fill=INK)
    d.rectangle((x0+1,y0+1,x1-1,y1-1),fill=wood)
    d.line([(x0+1,y0+1),(x1-1,y0+1)],fill=hi); d.line([(x0+1,y0+1),(x0+1,y1-1)],fill=hi)
    d.line([(x0+1,y1-1),(x1-1,y1-1)],fill=lo); d.line([(x1-1,y0+1),(x1-1,y1-1)],fill=lo)
    d.rectangle((x0+3,y0+3,x1-3,y1-3),fill=INK)
    d.rectangle((x0+4,y0+4,x1-4,y1-4),fill=fill)
    d.line([(x0+4,y0+4),(x1-4,y0+4)],fill=lerpc(fill,(200,170,130),.35))
    px=im.load()
    for (cx,cy) in [(x0,y0),(x1,y0),(x0,y1),(x1,y1)]: px[cx,cy]=(0,0,0,0)
    # rivets
    for (cx,cy) in [(x0+2,y0+2),(x1-2,y0+2),(x0+2,y1-2),(x1-2,y1-2)]: px[cx,cy]=hi+(255,)
