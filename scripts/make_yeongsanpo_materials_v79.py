"""Original tileable PBR maps; no reference photographs are redistributed."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[1];O=R/'assets/yeongsanpo-v79/materials';O.mkdir(parents=True,exist_ok=True)
N=512;rng=np.random.default_rng(79);y,x=np.mgrid[0:N,0:N]/N
def noise(size):
    im=Image.fromarray((rng.random((size,size))*255).astype('uint8')).resize((N,N),Image.Resampling.BICUBIC)
    return np.asarray(im).astype(float)/255-.5
low=noise(12);fine=noise(128);micro=rng.random((N,N))-.5
def save(kind,h,c=None,rough=.85,strength=1):
    if c is None:c=np.stack([.86+h*.11]*3,-1)
    Image.fromarray((np.clip(c,0,1)*255).astype('uint8')).save(O/f'{kind}-color.png')
    Image.fromarray((np.clip(rough+fine*.1-h*.04,0,1)*255).astype('uint8')).save(O/f'{kind}-roughness.png')
    dx=(np.roll(h,-1,1)-np.roll(h,1,1))*strength;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*strength
    a=np.stack([-dx,-dy,np.ones_like(h)],-1);a/=np.linalg.norm(a,axis=-1)[...,None]
    Image.fromarray(((a*.5+.5)*255).astype('uint8')).save(O/f'{kind}-normal.png')
save('plaster',low*.5+fine*.28+micro*.08,strength=3)
save('concrete',low*.3+fine*.42+micro*.15,strength=4)
wood=np.sin(x*np.pi*116+np.sin(y*np.pi*6)*1.5+low*2)*.11+np.sin(x*np.pi*350+low)*.04+low*.42+micro*.05
save('wood',wood,rough=.7,strength=4)
brickrow=np.floor(y*10);brickx=(x*6+brickrow%2*.5)%1;by=(y*10)%1
joint=(brickx<.045)|(by<.09);brick=low*.4+fine*.3+micro*.15-joint*.5
color=np.stack([.88+brick*.20,.82+brick*.17,.76+brick*.16],-1);color[joint]=(.54,.55,.51)
save('brick',brick,color,strength=3)
save('asphalt',fine*.4+micro*.28,rough=.92,strength=2)
tile=(np.minimum(x%(.125),.125-x%(.125))<.002)|(np.minimum(y%(.125),.125-y%(.125))<.002)
save('pavers',low*.3+fine*.2-tile*.6,strength=2)
save('roof',fine*.2+low*.35+np.sin(x*320*np.pi)*.025,rough=.65,strength=2)
canvas=(np.sin(x*256*np.pi)*np.sin(y*256*np.pi))*.18+fine*.12
save('canvas',canvas,rough=.96,strength=1.7)
tatami=np.sin(y*256*np.pi)*.27+np.sin(x*64*np.pi)*.04+fine*.10
save('tatami',tatami,np.stack([.88+tatami*.08,.86+tatami*.10,.65+tatami*.07],-1),rough=.91,strength=2)
wave=np.sin((x*23+y*4)*np.pi*2+low*.3)*.17+np.sin((x*7-y*13)*np.pi*2)*.09
save('water',wave,np.stack([.85+low*.08,.9+low*.05,.78+low*.08],-1),rough=.23,strength=3)
# A leaf silhouette with vein shading, authored here rather than cropped from a photo.
im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
for k in range(110,-1,-1):
    r=k/110;pts=[(128+np.sin(a)*65*r,128+np.cos(a)*113*r) for a in np.linspace(0,np.pi*2,80)]
    d.polygon(pts,fill=(int(57+23*(1-r)),int(99+33*(1-r)),int(35+12*(1-r)),255))
d.line([(128,16),(128,241)],fill=(129,149,72,255),width=3)
for yy in range(48,226,25):
    d.line([(128,yy),(88,yy-23)],fill=(94,124,53,255),width=1);d.line([(128,yy),(168,yy-23)],fill=(94,124,53,255),width=1)
im.save(O/'leaf-color.png')
print('Created original PBR maps:',len(list(O.glob('*.png'))))
