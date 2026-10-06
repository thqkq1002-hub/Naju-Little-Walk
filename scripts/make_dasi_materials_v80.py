"""Original, physically scaled Dasi surface maps. Reference photographs are not embedded."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'assets/dasi-v80/materials';O.mkdir(parents=True,exist_ok=True)
N=512;rng=np.random.default_rng(80);y,x=np.mgrid[0:N,0:N]/N
def noise(size):
    im=Image.fromarray((rng.random((size,size))*255).astype('uint8')).resize((N,N),Image.Resampling.BICUBIC)
    return np.asarray(im).astype(float)/255-.5
low=noise(16);fine=noise(120);micro=rng.random((N,N))-.5
def save(kind,h,c=None,rough=.85,strength=1):
    if c is None:c=np.stack([.87+h*.13]*3,-1)
    Image.fromarray((np.clip(c,0,1)*255).astype('uint8')).save(O/f'{kind}-color.png')
    Image.fromarray((np.clip(rough+fine*.1-h*.025,0,1)*255).astype('uint8')).save(O/f'{kind}-roughness.png')
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*strength;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*strength
    n=np.stack([-dx,-dy,np.ones_like(h)],-1);n/=np.linalg.norm(n,axis=-1)[...,None]
    Image.fromarray(((n*.5+.5)*255).astype('uint8')).save(O/f'{kind}-normal.png')
row=np.floor(y*8).astype(int);col=np.floor(x*6+row%2*.5).astype(int)%6
var=rng.uniform(-.065,.065,(8,6))[row,col];joint=((x*6+row%2*.5)%1<.037)|((y*8)%1<.075)
h=low*.22+fine*.15+micro*.10-joint*.6
c=np.stack([.83+var+fine*.07,.78+var+fine*.07,.72+var+fine*.08],-1);c[joint]=(.91,.93,.91)
save('brick',h,c,strength=2.7)
save('plaster',low*.3+fine*.20+micro*.06,strength=2.5)
save('granite',low*.18+fine*.38+micro*.35,rough=.86,strength=2)
save('concrete',low*.36+fine*.25+micro*.11,strength=2.2)
save('asphalt',fine*.35+micro*.28,rough=.93,strength=2)
joint=((x*4+np.floor(y*4)%2*.5)%1<.035)|((y*4)%1<.035)
save('pavers',low*.25+fine*.13-joint*.55,strength=2)
save('roof',low*.20+fine*.14+micro*.04,rough=.64,strength=1.2)
grain=np.sin(x*440*np.pi+np.sin(y*6*np.pi)*1.2)*.065+low*.36+fine*.12
save('wood',grain,rough=.72,strength=2)
bark=np.sin(x*42*np.pi+low*2)*.18+np.sin(x*140*np.pi+fine)*.08+low*.24
save('bark',bark,rough=.98,strength=2.2)
grass=low*.26+fine*.22+micro*.10
save('grass',grass,np.stack([.88+grass*.14,.92+grass*.09,.78+grass*.16],-1),rough=.97,strength=2)
save('court',fine*.22+micro*.12,rough=.88,strength=1.4)
# A multi-leaf card retains a leafy outline at walking distances with modest geometry.
for name,ivy in [('leaf',False),('ivy',True)]:
    im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
    centers=[(70,66,-.6),(181,76,.65),(103,180,-.15),(191,184,.35)] if not ivy else [(128,128,0)]
    for cx,cy,a in centers:
        l=54 if not ivy else 102;w=28 if not ivy else 96
        ca,sa=np.cos(a),np.sin(a)
        def pt(u,v):return (cx+u*ca-v*sa,cy+u*sa+v*ca)
        outline=[pt(np.sin(t)*w*(1+.22*np.cos(3*t) if ivy else 1),np.cos(t)*l) for t in np.linspace(0,np.pi*2,70)]
        d.polygon(outline,fill=(56,101,39,255))
        for j in range(4):
            rr=1-j*.14
            d.polygon([pt((p[0]-cx)*rr,(p[1]-cy)*rr) for p in outline],fill=(58+j*5,104+j*7,39+j*3,255))
        d.line([pt(0,-l*.83),pt(0,l*.87)],fill=(124,149,69,255),width=2)
        for v in range(-30,40,15):
            d.line([pt(0,v+8),pt(-w*.72,v-8)],fill=(94,126,50,255),width=1)
            d.line([pt(0,v+8),pt(w*.72,v-8)],fill=(94,126,50,255),width=1)
    im.save(O/f'{name}-color.png')
print('Original Dasi maps',len(list(O.glob('*.png'))))
