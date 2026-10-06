"""Original procedural material maps; no source photograph is used as a texture."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
OUT=Path(__file__).resolve().parents[1]/'assets/geumseonggwan-v76/materials'
OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(761002);n=1024
y,x=np.mgrid[0:n,0:n].astype(float)/n
def smooth(scale,radius):
    a=rng.integers(0,256,(scale,scale),dtype=np.uint8)
    return np.asarray(Image.fromarray(a).resize((n,n),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(radius)),dtype=float)/255-.5
coarse=smooth(48,5);fine=rng.random((n,n))-.5
maps={
    'wood':.93+.035*np.sin(x*420+np.sin(y*24)*2)+.018*np.sin(x*1100+np.sin(y*11)*5)+coarse*.025+fine*.035,
    'stone':.93+coarse*.095+smooth(190,1)*.05+fine*.05,
    'earth':.94+smooth(13,12)*.055+coarse*.045+fine*.045,
    'tile':.92+smooth(21,10)*.085+coarse*.035+fine*.055,
    'grass':.93+smooth(30,8)*.12+coarse*.09+fine*.045,
}
for name,a in maps.items():
    a=np.clip(a,.75,1)
    rgb=np.repeat((a*255).astype(np.uint8)[...,None],3,axis=2)
    if name=='tile':rgb[:,:,2]=np.clip(rgb[:,:,2].astype(float)-smooth(15,10).clip(0,1)*8,0,255).astype(np.uint8)
    Image.fromarray(rgb).save(OUT/f'{name}-color.png')
    rough=np.clip(.78+(1-a)*.65+fine*.02,.65,.99)
    Image.fromarray((rough*255).astype(np.uint8)).save(OUT/f'{name}-roughness.png')
    dx,dy=np.gradient(a)
    normal=np.stack([-dy*2.5,-dx*2.5,np.ones_like(a)],axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    Image.fromarray(((normal*.5+.5)*255).astype(np.uint8)).save(OUT/f'{name}-normal.png')
print('ORIGINAL_MATERIAL_MAPS_COMPLETE',len(maps)*3)
