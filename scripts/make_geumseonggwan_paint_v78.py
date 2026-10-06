"""Original painted material maps guided by survey observations, never photo crops."""
from pathlib import Path
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
out=Path(__file__).resolve().parents[1]/'assets/geumseonggwan-v78/materials';out.mkdir(parents=True,exist_ok=True)
S=1024
green='#4f8176';cream='#dfd1af';red='#ad6150';blue='#5e8196';gold='#c9a16a';dark='#344f49'

def rosette(d,cx,cy,r,phase=0):
    for k in range(8):
        a=math.tau*k/8+phase;pts=[]
        for j in range(45):
            t=math.tau*j/44;u=r*(.50+.39*math.cos(t));v=r*.21*math.sin(t)
            pts.append((cx+u*math.cos(a)-v*math.sin(a),cy+u*math.sin(a)+v*math.cos(a)))
        d.polygon(pts,fill=cream);d.line(pts,fill=dark,width=max(1,round(r*.014)))
        pts2=[(cx+(x-cx)*.80,cy+(y-cy)*.80) for x,y in pts]
        d.polygon(pts2,fill=red if k%2==0 else gold)
    d.ellipse((cx-r*.32,cy-r*.32,cx+r*.32,cy+r*.32),fill=cream)
    for k in range(6):
        a=k*math.tau/6;px=cx+r*.19*math.cos(a);py=cy+r*.19*math.sin(a)
        d.ellipse((px-r*.105,py-r*.105,px+r*.105,py+r*.105),fill=blue if k%2==0 else green)
    d.ellipse((cx-r*.09,cy-r*.09,cx+r*.09,cy+r*.09),fill=gold,outline=dark,width=2)

def scroll(d,cx,cy,r,mirror=1):
    # Curving foliage with layered lines, rather than separate flower solids.
    for sign in [-1,1]:
        pts=[]
        for k in range(140):
            t=k/139;ang=t*math.tau*1.15;rr=r*(1-t*.87)
            pts.append((cx+mirror*rr*math.cos(ang),cy+sign*rr*.60*math.sin(ang)))
        d.line(pts,fill=dark,width=max(2,round(r*.15)))
        d.line(pts,fill=cream,width=max(2,round(r*.09)))
        d.line(pts,fill=green,width=max(1,round(r*.045)))

def age(im,name,strength=1):
    rng=np.random.default_rng(sum(map(ord,name))+781003);a=np.asarray(im).astype(float)
    y,x=np.mgrid[:a.shape[0],:a.shape[1]]
    coarse=np.sin(x/51)*np.sin(y/67)+np.cos(x/131+y/87)
    n=rng.normal(0,2.1,a.shape[:2]);wear=rng.random(a.shape[:2])<.017*strength
    fade=np.clip(coarse*.014+n/255, -.08,.08)
    a=a*(1+fade[...,None]);a[wear]=a[wear]*.76+np.array([174,163,134])*.24
    im=Image.fromarray(np.clip(a,0,255).astype('uint8'));im.save(out/f'{name}-color.png')
    rough=np.clip(.85+(coarse*.01)+n*.002,.77,.97)
    Image.fromarray((rough*255).astype('uint8')).save(out/f'{name}-roughness.png')

im=Image.new('RGB',(S,S),green);d=ImageDraw.Draw(im)
for inset,color,width in [(9,dark,24),(33,cream,13),(49,red,23),(76,gold,8),(98,dark,9),(114,blue,13),(141,cream,7)]:
    d.rectangle((inset,inset,S-inset,S-inset),outline=color,width=width)
rosette(d,S/2,S/2,S*.33)
for x in [94,S-94]:
    for y in [94,S-94]:rosette(d,x,y,55,math.pi/8)
age(im,'coffer',1.2)
for name,replacements in [('coffer-blue',[(red,blue),(gold,blue)]),('coffer-gold',[(red,gold),(gold,red)])]:
    pixels=np.array(im);original=pixels.copy()
    for before,after in replacements:
        old=np.array(tuple(int(before[i:i+2],16) for i in (1,3,5)))
        new=tuple(int(after[i:i+2],16) for i in (1,3,5))
        pixels[np.all(original==old,axis=2)]=new
    age(Image.fromarray(pixels),name,1.2)

im=Image.new('RGB',(S,256),green);d=ImageDraw.Draw(im)
for y,c,w in [(7,cream,5),(17,red,7),(28,blue,5),(44,dark,4),(208,dark,4),(228,red,7),(243,cream,5)]:d.line((0,y,S,y),fill=c,width=w)
for cx in [110,914]:
    scroll(d,cx,128,75,1 if cx<512 else -1)
    rosette(d,cx,128,33)
    for k,c in enumerate([cream,red,blue,cream,green,red,gold]):
        xx=210+k*7 if cx<512 else 814-k*7;d.rectangle((xx,34,xx+3,222),fill=c)
d.rounded_rectangle((287,64,737,191),radius=20,fill=dark)
d.rounded_rectangle((293,70,731,185),radius=17,fill=cream)
d.rounded_rectangle((310,83,714,172),radius=9,fill=gold)
age(im,'beam',1.5)

im=Image.new('RGB',(512,512),green);d=ImageDraw.Draw(im)
for r,c in [(238,cream),(213,red),(181,blue),(147,cream),(126,green)]:d.ellipse((256-r,256-r,256+r,256+r),fill=c)
rosette(d,256,256,115)
age(im,'rafter-end',1.5)

im=Image.new('RGB',(256,S),green);d=ImageDraw.Draw(im)
for start in [0,870]:
    for i,c in enumerate([red,cream,blue,cream,gold,green,red]):d.rectangle((0,start+i*15,256,start+i*15+11),fill=c)
for cx in [35,128,221]:
    rosette(d,cx,150,34);rosette(d,cx,830,34)
age(im,'rafter-body',1.7)

im=Image.new('RGB',(S,512),'#708e80');d=ImageDraw.Draw(im)
for inset,c,w in [(11,cream,8),(28,dark,16),(54,'#799889',12),(75,'#adb3a1',5)]:d.rectangle((inset,inset,S-inset,512-inset),outline=c,width=w)
for cx in [120,904]:scroll(d,cx,256,54,1 if cx<512 else -1)
age(im,'door-panel',2)

# This original lettering is a brush-style font interpretation, not a copy of the plaque.
im=Image.new('RGB',(1536,512),'#252e29');d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/batang.ttc',385,index=2)
for k,ch in enumerate('館城錦'):
    box=d.textbbox((0,0),ch,font=font);d.text((65+k*484-box[0],256-(box[1]+box[3])/2),ch,font=font,fill='#e3dfc9',stroke_width=1)
age(im,'plaque',.7)
print('V78 original painted maps generated',flush=True)
