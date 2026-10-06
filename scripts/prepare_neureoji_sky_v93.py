"""Original soft daylight sky map, without copying photographic panoramas."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
R=Path(__file__).resolve().parents[1];A=R/'assets/neureoji-v93';A.mkdir(parents=True,exist_ok=True)
width,height=1536,768
v=np.linspace(0,1,height)[:,None,None];u=np.linspace(0,1,width)[None,:,None]
top=np.array([116,161,188]);horizon=np.array([201,214,214]);t=np.clip(v/.50,0,1)
rgb=top*(1-t)+horizon*t;rgb=np.broadcast_to(rgb,(height,width,3)).copy()
rng=np.random.default_rng(93093);cloud=np.zeros((height,width))
for scale,weight in [(18,.55),(45,.28),(100,.17)]:
    values=(rng.random((max(3,scale//2),scale))*255).astype('uint8')
    cloud+=np.asarray(Image.fromarray(values).resize((width,height),Image.Resampling.BICUBIC)).astype(float)/255*weight
mask=np.clip((cloud-.55)*3.4,0,.50)*np.clip(1-np.abs(v[:,:,0]-.27)*3.5,0,1)
rgb=rgb*(1-mask[:,:,None])+np.array([223,228,226])*mask[:,:,None]
Image.fromarray(np.clip(rgb,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(.5)).save(A/'sky-original.png')
print('Original daylight sky map prepared')
