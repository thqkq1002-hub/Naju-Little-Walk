"""Trace the near-tower mapped route and make original plant/surface studies.

The 2026 visitor photographs are reference only, never exported or repainted.
OSM provides horizontal centerlines; widths, planting and local grading are interpreted.
"""
import json, math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/python-geo'))
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union, triangulate

R=Path(__file__).resolve().parents[1]
W=R/'work/neureoji-v94';A=R/'assets/neureoji-v94';K=R/'knowledge/sources/neureoji-v94'
for p in [W,A,K]:p.mkdir(parents=True,exist_ok=True)
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
osm=json.loads((R/'work/neureoji-v92/osm.json').read_text(encoding='utf8'))
T=json.loads((R/'knowledge/sources/neureoji-v92/native-terrain.json').read_text(encoding='utf8'))
B=w['spawn']['height'];origin=w['geographicOrigin'];mx=91281.58980911358
native=Image.open(R/'work/neureoji-v92/Copernicus_DSM_COG_10_N34_00_E126_00_DEM.tif');dem=np.asarray(native)
dx,dy,_=native.tag_v2[33550];_,_,_,lon0,lat0,_=native.tag_v2[33922]

def native_height(x,z):
    u=(origin['lon']+x/mx-lon0)/dx;v=(lat0-origin['lat']+z/111320)/dy
    i,j=math.floor(u),math.floor(v);f,h=u-i,v-j
    return float((dem[j,i]*(1-f)+dem[j,i+1]*f)*(1-h)+(dem[j+1,i]*(1-f)+dem[j+1,i+1]*f)*h)-T['modelDatumMetres']-8

def height(x,z):
    # Keep the existing artist-authored plaza and blend into the same canopy allowance.
    r=math.hypot(x,z);t=max(0,min(1,(r-24)/53));t=t*t*(3-2*t)
    return B*(1-t)+native_height(x,z)*t

def mapped(way):
    e=next(e for e in osm['elements'] if e['type']=='way' and e['id']==way)
    return [[(p['lon']-origin['lon'])*mx,(origin['lat']-p['lat'])*111320] for p in e['geometry']]

south=list(reversed([p for p in mapped(699922279) if 24<p[1]<135]))
north=mapped(947992194)
# Existing south approach is retained. Tower-side links are photo interpreted, not OSM nodes.
routes=[dict(id='flower-road',name='수국 언덕길',width=3,points=[[3.2,21],[1.0,23.5]]+south,sourceWay=699922279),
        dict(id='woodland-hydrangea',name='그늘 수국길',width=1.85,points=[[5.0,-5.1],[5.1,-16],[5.1,-33.9]]+north[1:],sourceWay=947992194)]

def resample(points,spacing=.9):
    # Shape-preserving quadratic corner rounding. No spline overshoot beyond the mapped route.
    rounded=[points[0]]
    for a,b,c in zip(points,points[1:],points[2:]):
        la=math.dist(a,b);lc=math.dist(b,c);trim=min(la*.24,lc*.24,2.2)
        p=[b[i]+(a[i]-b[i])*trim/la for i in range(2)];q=[b[i]+(c[i]-b[i])*trim/lc for i in range(2)]
        rounded.append(p)
        for j in range(1,7):
            t=j/6;rounded.append([(1-t)**2*p[i]+2*t*(1-t)*b[i]+t*t*q[i] for i in range(2)])
    rounded.append(points[-1]);out=[]
    for a,b in zip(rounded,rounded[1:]):
        count=max(1,math.ceil(math.dist(a,b)/spacing))
        for j in range(count):out.append([a[i]+(b[i]-a[i])*j/count for i in range(2)])
    out.append(rounded[-1]);return out

for route in routes:
    route['mappedPoints']=route.pop('points');pts=resample(route['mappedPoints']);samples=[];distance=0
    for i,p in enumerate(pts):
        before=pts[max(0,i-1)];after=pts[min(len(pts)-1,i+1)]
        l=math.dist(before,after);tx,tz=(after[0]-before[0])/l,(after[1]-before[1])/l
        if i:distance+=math.dist(pts[i-1],p)
        samples.append(dict(x=p[0],z=p[1],y=height(*p),nx=-tz,nz=tx,distance=distance))
    route.update(samples=samples,lengthMetres=distance,heightRange=[min(s['y'] for s in samples),max(s['y'] for s in samples)])

# Replace the coarse ground only in a narrow corridor; retain all mapped river boundaries.
lines=[LineString([[p['x'],p['z']] for p in r['samples']]) for r in routes]
corridor=unary_union([l.buffer(13) for l in lines])
G=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
water=unary_union([Polygon(p['points'],p['holes']) for p in G['water']]);corridor=corridor.difference(water)
old=json.loads((R/'work/neureoji-v93/landscape.json').read_text(encoding='utf8'))
landv=[];landf=[];patchv=[];patchf=[]
def pieces(shape):
    if shape.is_empty:return []
    return [shape] if shape.geom_type=='Polygon' else [p for p in getattr(shape,'geoms',[]) if p.geom_type=='Polygon']
def original_height(x,z):
    y=native_height(x,z);r=math.hypot(x,z);t=max(0,min(1,(r-17)/60));t=t*t*(3-2*t)
    return B*(1-t)+y*t if r<77 else y
loX,loZ,hiX,hiZ=corridor.bounds
for face in old['faces']:
    vs=[old['vertices'][i] for i in face];xs=[p[0] for p in vs];zs=[p[2] for p in vs]
    if max(xs)<loX or min(xs)>hiX or max(zs)<loZ or min(zs)>hiZ:
        offset=len(landv);landv.extend(vs);landf.append([offset,offset+1,offset+2]);continue
    tri=Polygon([(p[0],p[2]) for p in vs])
    if not tri.intersects(corridor):
        offset=len(landv);landv.extend(vs);landf.append([offset,offset+1,offset+2]);continue
    # Preserve the old triangle's plane on the cut edge, not an unrelated new sampling.
    coeff=np.linalg.solve(np.array([[p[0],p[2],1] for p in vs]),np.array([p[1] for p in vs]))
    for p in pieces(tri.difference(corridor)):
        for q in triangulate(p):
            if not p.covers(q):continue
            offset=len(landv);landv.extend([[x,float(coeff[0]*x+coeff[1]*z+coeff[2]),z] for x,z in list(q.exterior.coords)[:3]]);landf.append([offset,offset+1,offset+2])
samples=[q for r in routes for q in r['samples']];arr=np.array([[p['x'],p['z']] for p in samples])
def patch_height(x,z):
    squared=np.sum((arr-[x,z])**2,axis=1);k=int(np.argmin(squared));p=samples[k];d=math.sqrt(squared[k])
    # Close to the path, leave its visible slab clear and raise the forest bank gently.
    bank=p['y']-.14+min(max(0,d-1.6)*.12,.9);t=max(0,min(1,(d-4)/9));t=t*t*(3-2*t)
    return bank*(1-t)+(original_height(x,z)-.06)*t
for x in np.arange(math.floor(loX/2)*2,hiX,2):
    for z in np.arange(math.floor(loZ/2)*2,hiZ,2):
        cell=box(x,z,x+2,z+2)
        if not cell.intersects(corridor):continue
        for p in pieces(cell.intersection(corridor)):
            for q in triangulate(p):
                if not p.covers(q):continue
                offset=len(patchv);patchv.extend([[xx,patch_height(xx,zz),zz] for xx,zz in list(q.exterior.coords)[:3]]);patchf.append([offset,offset+1,offset+2])
(W/'ground.json').write_text(json.dumps(dict(vertices=landv,faces=landf,patchVertices=patchv,patchFaces=patchf),separators=(',',':')),encoding='utf8')
print('Fine trail terrain:',len(patchf),'triangles; original water untouched',flush=True)

rng=random.Random(9404)
# One original toothed ovate leaf, packed into a single cutout material with visible veins.
leaf=Image.new('RGBA',(512,512));d=ImageDraw.Draw(leaf)
outline=[]
for k in range(101):
    t=k/100;yy=455-t*410;half=164*math.sin(math.pi*t)**.8*(.93+.07*math.cos(k*math.pi))
    outline.append((256-half,yy))
for k in range(100,-1,-1):
    t=k/100;yy=455-t*410;half=164*math.sin(math.pi*t)**.8*(.93+.07*math.cos(k*math.pi))
    outline.append((256+half,yy))
d.polygon(outline,fill=(71,121,43,255));d.line([(256,465),(256,46)],fill=(153,172,78,255),width=4)
for k in range(8):
    yy=405-k*43;half=164*math.sin(math.pi*(455-yy)/410)**.8
    for side in [-1,1]:d.line([(256,yy),(256+side*half*.88,yy-56)],fill=(111,149,65,255),width=2)
leaf.save(A/'hydrangea-leaf-original.png')

# Equirectangular blossom studies on round heads: the small four-sepal shapes remain visible up close.
palette=[(98,144,225),(132,106,210),(214,115,179),(223,221,213)]
for col,base in enumerate(palette):
    im=Image.new('RGBA',(512,256),(0,0,0,0));d=ImageDraw.Draw(im)
    for row in range(12):
        for k in range(24):
            x=(k+(row%2)*.5)*512/24+rng.uniform(-3,3);y=(row+.5)*256/12+rng.uniform(-2,2)
            shade=rng.uniform(.88,1.12);color=tuple(min(255,int(c*shade)) for c in base)+(255,)
            radius=rng.uniform(6,9)
            for a in range(4):
                angle=a*math.pi/2+.25;px=x+math.cos(angle)*radius*.55;py=y+math.sin(angle)*radius*.55
                d.ellipse((px-radius*.62,py-radius*.62,px+radius*.62,py+radius*.62),fill=color)
            d.ellipse((x-1.4,y-1.4,x+1.4,y+1.4),fill=(199,208,144,255))
    im.save(A/f'hydrangea-head-{col}-original.png')

for name,base,seed in [('path-concrete',(173,170,152),941),('path-soil',(133,100,70),942),('woodland-floor',(83,91,54),943)]:
    n=np.random.default_rng(seed);noise=n.normal(0,3,(512,512,1));arr=np.clip(np.array(base)+noise,0,255).astype('uint8')
    im=Image.fromarray(arr);d=ImageDraw.Draw(im)
    for k in range(1500):
        x=rng.randint(0,511);y=rng.randint(0,511);l=rng.randint(1,4)
        shade=rng.randint(-12,12);c=tuple(max(0,min(255,q+shade)) for q in base)
        d.line([(x,y),(x+l,y+rng.randint(-2,2))],fill=c,width=1)
    im.save(A/f'{name}-original.png')

im=Image.new('RGB',(512,512),'#897456');d=ImageDraw.Draw(im)
for k in range(8):
    yy=k*64;shade=rng.randint(-8,8);col=tuple(v+shade for v in (137,116,86))
    d.rectangle((0,yy,511,yy+61),fill=col);d.line([(0,yy+63),(511,yy+63)],fill='#574d3a',width=2)
    for j in range(35):
        y=yy+rng.randint(2,59);x=rng.randint(0,480);d.line([(x,y),(min(511,x+rng.randint(15,80)),y)],fill='#958160',width=1)
im.save(A/'path-wood-original.png')

data=dict(revision='neureoji-hydrangea-v94',originWGS84=origin,routes=routes,canopyAllowanceMetres=8,
    nativeResolutionMetres=30,sourceURLs=['https://akekanfl.tistory.com/8708274','https://www.openstreetmap.org/way/699922279','https://www.openstreetmap.org/way/947992194',T['sourceUrl']],
    evidence='2026-06-27 firsthand photographs: curved concrete approach, mophead/lacecap hydrangeas, narrower shaded trail, dark rails and wooden deck transition.',
    limitations=['Route centerlines are OSM cycleways shared with pedestrians, not a surveyed hydrangea planting plan.','Widths, near-tower connections, individual plants and local grading are photo interpretations.','Only the near-tower sections are reproduced, not the entire reported ten-minute flower walk.','Summer flowering appearance; not a live bloom condition.'])
for p in [W/'trail.json',K/'trail.json']:p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Prepared mapped near-tower trails:',[(r['id'],round(r['lengthMetres'],1),len(r['samples'])) for r in routes])
