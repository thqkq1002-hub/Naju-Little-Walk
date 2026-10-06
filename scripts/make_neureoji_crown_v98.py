from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1];O=R/'work/neureoji-polish-v98';O.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(98105);n=512;y,x=np.mgrid[0:n,0:n]/n
mask=np.zeros((n,n),dtype=float)
for cx,cy,rx,ry in [(.50,.52,.39,.38),(.29,.47,.20,.25),(.68,.40,.21,.28),(.44,.29,.21,.23),(.53,.73,.28,.20)]:
 mask=np.maximum(mask,1-((x-cx)/rx)**2-((y-cy)/ry)**2)
def noise(size):
 a=Image.fromarray((rng.random((size,size))*255).astype('uint8'));return np.array(a.resize((n,n),Image.Resampling.BICUBIC),dtype=float)/255
broad=noise(24);fine=noise(150);edge=noise(65)
alpha=np.clip((mask+(edge-.5)*.17)*18,0,1)
shade=.72+.28*broad+.10*fine-.20*y+.07*(1-x)
base=np.array([80,113,64]);rgb=np.clip(shade[:,:,None]*base+(fine[:,:,None]-.5)*10,0,255)
rgba=np.dstack([rgb,alpha*255]).astype('uint8');Image.fromarray(rgba).save(O/'woodland-crown-v98.png')
