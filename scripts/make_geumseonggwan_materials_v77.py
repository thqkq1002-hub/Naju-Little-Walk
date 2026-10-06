"""Original seamless material maps, not copied source photographs."""
from pathlib import Path
import numpy as np
from PIL import Image
out=Path(__file__).resolve().parents[1]/'assets/geumseonggwan-v77/materials';out.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(771003);n=1024
y,x=np.mgrid[0:n,0:n]/n
def noise(terms,frequency):
    a=np.zeros((n,n))
    for _ in range(terms):
        k,l=rng.integers(-frequency,frequency+1,2)
        if k or l:a+=np.sin(2*np.pi*(k*x+l*y)+rng.uniform(0,2*np.pi))
    return a/max(1,terms)**.5
coarse=noise(35,9);grain=noise(50,85)
wood=.91+.065*np.sin(2*np.pi*(55*x+.25*np.sin(2*np.pi*y*2)))+.027*np.sin(2*np.pi*173*x)+.035*coarse+.028*grain
for cx,cy in [(.22,.28),(.73,.67)]:
    d=np.sqrt(((x-cx)*7)**2+((y-cy)*2)**2)
    wood-=.13*np.exp(-d*d*13);wood+=.025*np.sin(d*100)*np.exp(-d*d*3)
earth=.91+.055*coarse+.03*grain+.016*noise(75,350)
paper=.95+.025*noise(45,25)+.01*noise(60,280)
for name,a in [('wood',wood),('earth',earth),('paper',paper)]:
    a=np.clip(a,.63,1);rgb=np.repeat((a*255).astype(np.uint8)[...,None],3,axis=2)
    Image.fromarray(rgb).save(out/f'{name}-color.png')
    rough=np.clip(.83+(1-a)*.4,.8,1)
    Image.fromarray((rough*255).astype(np.uint8)).save(out/f'{name}-roughness.png')
    gx=(np.roll(a,-1,1)-np.roll(a,1,1))*.5;gy=(np.roll(a,-1,0)-np.roll(a,1,0))*.5
    normals=np.stack([-gx*2,-gy*2,np.ones_like(a)],-1);normals/=np.linalg.norm(normals,axis=-1,keepdims=True)
    Image.fromarray(((normals*.5+.5)*255).astype(np.uint8)).save(out/f'{name}-normal.png')
print('v77 original material maps complete')
