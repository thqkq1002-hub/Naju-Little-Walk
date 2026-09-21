"""Photo interpretation, not surveyed footprints. Keep observed roofs and guesses separate."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];S=R/'knowledge/sources/bitgaram'
e=json.loads((S/'district-satellite-extent.json').read_text())['extent']
a=np.asarray(Image.open(R/'work/bitgaram-district-satellite-hires.jpg').convert('RGB'));h,w=a.shape[:2]
def xy(px,py):
 lon=e['xmin']+px/w*(e['xmax']-e['xmin']);lat=e['ymax']-py/h*(e['ymax']-e['ymin'])
 return [(lon-126.790447)*111320*math.cos(math.radians(35.016925)),(35.016925-lat)*111320]
rows=[]
def roof(x,y,length,depth,angle,height,zone):
 # Manual positions are on the inspected crop (original pixel offset 150,150).
 cx,cz=xy((x+150)*w/2000,(y+150)*h/1600);co=math.cos(math.radians(angle));si=math.sin(math.radians(angle))
 p=[[round(cx+u*co-v*si,2),round(cz+u*si+v*co,2)] for u,v in [(-length/2,-depth/2),(length/2,-depth/2),(length/2,depth/2),(-length/2,depth/2)]]
 rows.append(dict(polygon=p,height=height,kind='satellite_apartment',zone=zone,source='manually interpreted roof position; footprint, height and facade estimated'))
# Apartment wings clearly visible in the reference, missing from OSM.
for x,y in [(99,53),(131,60),(162,65),(188,74),(84,76),(112,82),(143,88),(174,97),(80,99),(110,105),(141,113),(169,120),(91,128),(122,136),(150,143)]:roof(x,y,54,14,13,48,'northwest_outer')
for x,y,an in [(368,104,16),(365,128,15),(391,133,14),(362,151,14),(390,156,14),(355,172,14),(384,178,14),(355,191,14),(385,197,14),(433,91,-8),(440,113,-7),(445,132,-7),(450,151,-7),(495,82,-5),(519,80,-5),(546,82,2),(493,104,-4),(519,101,-4),(550,106,-2),(493,125,-3),(520,122,-3),(556,128,0),(406,101,30),(407,121,30)]:roof(x,y,48,14,an,51,'northwest_lake')
for x,y,an in [(332,569,-4),(361,586,-6),(323,604,15),(350,613,15),(323,625,18),(346,638,18),(317,649,18),(341,661,18),(369,660,29),(393,674,29),(416,689,29),(401,654,29),(430,670,29),(452,684,29),(435,712,24),(459,727,24),(492,743,18),(478,755,18),(506,769,18),(518,787,18)]:roof(x,y,49,14,an,54,'west_lake')
for x,y,an in [(573,820,0),(595,820,0),(573,842,0),(595,842,0),(553,830,75),(554,854,75),(547,911,23),(523,887,34),(511,867,34),(496,891,34),(519,910,34),(549,952,0),(574,954,0),(599,954,0),(569,977,0),(594,978,0)]:roof(x,y,43,14,an,48,'southwest_lake')
# Roof detection restricted to visually inspected built blocks. No blanket filling of vacant land.
zones=[(.203,.319,.254,.355),(.176,.466,.273,.541),(.127,.518,.193,.589),(.118,.590,.191,.652),(.319,.571,.459,.644),(.364,.650,.457,.697),(.507,.342,.548,.396),(.548,.322,.621,.392),(.515,.209,.582,.254),(.494,.282,.547,.318),(.262,.345,.355,.394),(.331,.343,.491,.399),(.296,.402,.347,.455),(.257,.456,.320,.498)]
mx=a.max(2).astype(float);mn=a.min(2).astype(float);light=a.mean(2)
mask=(light>105)&(light<242)&(mx-mn<53);selected=np.zeros_like(mask)
for x0,y0,x1,y1 in zones:selected[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=True
mask &= selected;seen=np.zeros_like(mask)
for yy,xx in zip(*np.where(mask)):
 if seen[yy,xx]:continue
 stack=[(int(xx),int(yy))];seen[yy,xx]=1;pts=[]
 while stack:
  x,y=stack.pop();pts.append((x,y))
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   nx,ny=x+dx,y+dy
   if 0<=nx<w and 0<=ny<h and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=1;stack.append((nx,ny))
 if not 12<=len(pts)<=850:continue
 xs=[p[0] for p in pts];ys=[p[1] for p in pts];bw=max(xs)-min(xs)+1;bh=max(ys)-min(ys)+1
 if min(bw,bh)<2 or max(bw,bh)/min(bw,bh)>4 or len(pts)/(bw*bh)<.38:continue
 cx,cz=xy(sum(xs)/len(xs),sum(ys)/len(ys))
 rows.append(dict(center=[round(cx,2),round(cz,2)],size=[round(min(38,max(6,bw*1.30)),2),round(min(38,max(6,bh*1.585)),2)],kind='satellite_shop' if len(pts)>200 else 'satellite_house',pixels=len(pts),source='roof-tone component inside inspected built block; approximate footprint and height'))
# Dark/colored house roofs often do not form isolated bright components. Inspect
# small parcel windows as well; the Blender pass still excludes roads and all buildings.
housezones=[(.203,.321,.252,.354),(.126,.516,.190,.584),(.12,.591,.18,.650),(.365,.576,.459,.641),(.364,.650,.454,.694),(.554,.344,.621,.390),(.518,.209,.582,.256)]
neutral=(mx-mn<35)&(light>55)&(light<225)
for zi,(x0,y0,x1,y1) in enumerate(housezones):
 for yy in range(int(y0*h)+8,int(y1*h)-8,17):
  for xx in range(int(x0*w)+8,int(x1*w)-8,19):
   patch=neutral[yy-7:yy+8,xx-7:xx+8];rgb=a[yy-7:yy+8,xx-7:xx+8].astype(float)
   # Preserve visibly vegetated/bare-soil parcels. Roof tones alone are not truth.
   if patch.mean()<.34 or np.std(rgb.mean(2))<19:continue
   py,px=np.where(patch);cx,cz=xy(xx-7+px.mean(),yy-7+py.mean())
   rows.append(dict(center=[round(cx,2),round(cz,2)],size=[12,14],kind='satellite_parcel_house',zone=zi,source='roof-toned parcel patch; schematic placement and height, not measured outline'))
(S/'district-block-infill.json').write_text(json.dumps(dict(reference='Esri World Imagery, acquisition date unknown',manual_count=75,zones=zones,candidates=rows),ensure_ascii=False,indent=2),encoding='utf-8')
print('candidates',len(rows),'manual',sum('polygon' in r for r in rows))
