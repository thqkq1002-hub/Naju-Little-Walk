"""Author original surfaces and forest positions from the recorded public geometry."""
from pathlib import Path
import json,math,random,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'))
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union,triangulate
O=R/'work/neureoji-v92';G=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
T=json.loads((R/'knowledge/sources/neureoji-v92/native-terrain.json').read_text(encoding='utf8'))
A=np.array(T['heightsMetres']);origin=G['originWGS84'];mx=G['metresPerLongitudeDegree'];pad=T['interpretedTowerPadMetres'];rng=random.Random(9204)
water=unary_union([Polygon(p['points'],p['holes']) for p in G['water']]);forest=unary_union([Polygon(p['points'],p['holes']) for p in G['land'] if p['tags'].get('landuse')=='forest' or p['tags'].get('natural')=='wood']);shore=water.buffer(90).difference(water.buffer(7))
def height(x,z):
    u=(origin['lon']+x/mx-T['sampleOriginLongitude'])/T['longitudeSpacingDegrees'];v=(T['sampleOriginLatitude']-origin['lat']+z/111320)/T['latitudeSpacingDegrees']
    i,j=math.floor(u),math.floor(v);f,h=u-i,v-j;i=max(0,min(A.shape[1]-2,i));j=max(0,min(A.shape[0]-2,j))
    y=float((A[j,i]*(1-f)+A[j,i+1]*f)*(1-h)+(A[j+1,i]*(1-f)+A[j+1,i+1]*f)*h)-T['modelDatumMetres']
    # DSM is a canopy surface. Explicit photo-based allowance, never labelled surveyed ground.
    if forest.contains(Point(x,z)) or y>18:y=max(0,y-8)
    r=math.hypot(x,z);blend=max(0,min(1,(r-17)/60));blend=blend*blend*(3-2*blend)
    return pad*(1-blend)+y*blend if r<77 else y
n,m=248,200;verts=[];faces=[]
for j in range(m+1):
    z=-2700+j*5000/m
    for i in range(n+1):
        x=-3100+i*6200/n;verts.append([x,height(x,z)-.12,z])
for j in range(m):
    for i in range(n):
        a=j*(n+1)+i;faces.append([a,a+1,a+n+2,a+n+1])
# Native shoreline is triangulated without replacing concavities with a bounding rectangle.
waterv=[];waterf=[]
for p in G['water']:
    poly=Polygon(p['points'],p['holes'])
    for tr in triangulate(poly):
        if not poly.covers(tr):continue
        a=len(waterv);waterv.extend([[x,.08,z] for x,z in list(tr.exterior.coords)[:3]]);waterf.append([a,a+1,a+2])
assert abs(sum(Polygon([(waterv[i][0],waterv[i][2]) for i in f]).area for f in waterf)-water.area)<.01
trees=[]
for z in range(-2500,2250,28):
    for x in range(-3000,3000,28):
        xx=x+rng.uniform(-12,12);zz=z+rng.uniform(-12,12);p=Point(xx,zz);hh=height(xx,zz);r=math.hypot(xx,zz)
        if r<20 or water.buffer(7).contains(p):continue
        if (forest.contains(p) or hh>16 or shore.contains(p)) and rng.random()<.88:
            trees.append([xx,hh,zz,rng.uniform(5,11),rng.randrange(5)])
# Authored map finish: OSM parcel outlines, procedural crop variation inside those parcels.
size=2048;im=Image.new('RGB',(size,size),'#8a9e64');draw=ImageDraw.Draw(im)
def pixel(x,z):return ((x+3100)/6200*size,(z+2700)/5000*size)
for x,y,z in verts:
    if y>16:
        xx,zz=pixel(x,z);draw.rectangle((xx-5,zz-6,xx+5,zz+6),fill=rng.choice(['#5b7547','#627e4a','#6d834d']))
for p in G['land']:
    kind=p['tags'].get('landuse',p['tags'].get('natural'))
    col=rng.choice(['#a5b77a','#91ac65','#b2bb81','#86a568']) if kind in ('farmland','farm','orchard') else '#577342' if kind in ('forest','wood') else '#9bac7b'
    draw.polygon([pixel(x,z) for x,z in p['points']],fill=col)
    if kind in ('farmland','farm'):
        poly=Polygon(p['points'],p['holes']);minx,minz,maxx,maxz=poly.bounds
        for x in np.arange(minx,maxx,48):
            line=poly.intersection(__import__('shapely').geometry.LineString([(x,minz),(x,maxz)]))
            for l in [line] if line.geom_type=='LineString' else getattr(line,'geoms',[]):
                if l.geom_type=='LineString':draw.line([pixel(*a) for a in l.coords],fill='#bac496',width=2)
        for z in np.arange(minz,maxz,70):
            line=poly.intersection(__import__('shapely').geometry.LineString([(minx,z),(maxx,z)]))
            for l in [line] if line.geom_type=='LineString' else getattr(line,'geoms',[]):
                if l.geom_type=='LineString':draw.line([pixel(*a) for a in l.coords],fill='#c6cead',width=2)
for p in G['water']:draw.polygon([pixel(x,z) for x,z in p['points']],fill='#3e716e')
# Original fine variation avoids flat colour, without embedding satellite or blog photos.
a=np.asarray(im).astype(float);noise=np.random.default_rng(9204).normal(0,2.5,(size,size,1));a=np.clip(a+noise,0,255).astype('uint8');Image.fromarray(a).save(O/'original-landcover.png')
json.dump(dict(vertices=verts,faces=faces,waterVertices=waterv,waterFaces=waterf,forest=trees,padHeight=pad,
    backgroundBounds=G['bounds'],waterArea=water.area,treePositions='OSM woods / high DSM ground, inferred individual positions'),open(O/'mesh.json','w',encoding='utf8'),separators=(',',':'))
print(json.dumps(dict(terrainVertices=len(verts),waterTriangles=len(waterf),forestTrees=len(trees),pad=pad)),flush=True)
