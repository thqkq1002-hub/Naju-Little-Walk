from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'work/neureoji-v99';O.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(9905);n=256
# Original procedural aggregate texture; no reference photograph is reused.
noise=rng.normal(0,3.1,(n,n,1));rgb=np.clip(np.array([173,164,146])+noise,0,255).astype('uint8')
for i in range(320):
 y,x=rng.integers(0,n,2);rgb[y,x]=np.array([145,138,125]) if i%3 else np.array([190,181,161])
Image.fromarray(rgb).save(O/'path-aggregate.png')
