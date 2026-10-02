"""Conservative roof candidates from visually selected low-rise satellite blocks."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];S=R/'knowledge/sources/bitgaram'
e=json.loads((S/'district-satellite-extent.json').read_text())['extent']
a=np.array(Image.open(R/'work/bitgaram-district-satellite.jpg').convert('RGB'));h,w=a.shape[:2]
# These masks were selected from the image, not from a universal building classifier.
zones=[(.329,.57,.497,.699),(.541,.275,.623,.397),(.117,.255,.218,.349),(.175,.594,.277,.667),(.391,.20,.486,.283),(.071,.575,.156,.683)]
def xy(px,py):
 lon=e['xmin']+(px/w)*(e['xmax']-e['xmin']);lat=e['ymax']-(py/h)*(e['ymax']-e['ymin'])
 return [(lon-126.790447)*111320*math.cos(math.radians(35.016925)),(35.016925-lat)*111320]
mx=a.max(axis=2).astype(float);mn=a.min(axis=2).astype(float);light=a.mean(axis=2)
mask=(light>132)&(light<242)&((mx-mn)<48);selected=np.zeros_like(mask)
for x0,y0,x1,y1 in zones:selected[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=True
mask &= selected;seen=np.zeros_like(mask);candidates=[]
for yy,xx in zip(*np.where(mask)):
 if seen[yy,xx]:continue
 stack=[(int(xx),int(yy))];seen[yy,xx]=True;component=[]
 while stack:
  x,y=stack.pop();component.append((x,y))
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   nx,ny=x+dx,y+dy
   if 0<=nx<w and 0<=ny<h and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;stack.append((nx,ny))
 if not 5<=len(component)<=95:continue
 xs=[p[0] for p in component];ys=[p[1] for p in component];bw=max(xs)-min(xs)+1;bh=max(ys)-min(ys)+1
 if min(bw,bh)<2 or max(bw,bh)/min(bw,bh)>3.4 or len(component)/(bw*bh)<.42:continue
 cx,cz=xy(sum(xs)/len(xs),sum(ys)/len(ys));ww=min(22,max(7,bw*(e['xmax']-e['xmin'])/w*111320*math.cos(math.radians(35.016925))));dd=min(24,max(7,bh*(e['ymax']-e['ymin'])/h*111320))
 candidates.append(dict(center=[round(cx,2),round(cz,2)],size=[round(ww,2),round(dd,2)],pixels=len(component)))
(S/'district-roof-candidates.json').write_text(json.dumps(dict(method='Estimated pale roof components within six visually selected low-rise blocks; roads, mapped buildings, water and duplicates are excluded again in Blender.',zones=zones,candidates=candidates),indent=2))
print('roof candidates',len(candidates))
