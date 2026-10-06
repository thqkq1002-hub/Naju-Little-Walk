"""Offline geography preparation from retrieved public OSM and GLO-30 data."""
from pathlib import Path
import json,math,hashlib,sys
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'))
from shapely.geometry import Polygon,LineString,box,mapping
from shapely.ops import unary_union,polygonize
W=R/'work/neureoji-v92';O=R/'knowledge/sources/neureoji-v92';O.mkdir(parents=True,exist_ok=True)
data=json.loads((W/'osm.json').read_text(encoding='utf8'));origin={'lat':34.9159348,'lon':126.5419381}
mx=111320*math.cos(math.radians(origin['lat']));mz=111320
def pt(p):return [(p['lon']-origin['lon'])*mx,(origin['lat']-p['lat'])*mz]
boundary=box(-3100,-2700,3100,2300)
waters=[];land=[];roads=[];buildings=[]
def polygons(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [x for x in g.geoms if x.geom_type=='Polygon'] if hasattr(g,'geoms') else []
def entry(g,tags,id):
    return [dict(id=id,tags=tags,points=list(p.exterior.coords)[:-1],holes=[list(h.coords)[:-1] for h in p.interiors],area=p.area) for p in polygons(g)]
for e in data['elements']:
    tags=e.get('tags',{});points=[pt(p) for p in e.get('geometry',[]) if 'lon' in p]
    if e['type']=='relation' and tags.get('natural')=='water':
        lines=[LineString([pt(p) for p in m['geometry']]) for m in e.get('members',[]) if m.get('geometry') and m.get('role')=='outer']
        if lines:waters+=entry(unary_union(list(polygonize(unary_union(lines)))).intersection(boundary),tags,e['id'])
    if len(points)<3:continue
    if tags.get('highway'):
        g=LineString(points).intersection(boundary)
        if g.geom_type=='LineString':roads.append(dict(id=e['id'],tags=tags,points=list(g.coords)))
    if points[0]!=points[-1]:continue
    g=Polygon(points).buffer(0).intersection(boundary)
    if tags.get('natural')=='water':waters+=entry(g,tags,e['id'])
    elif tags.get('building'):buildings+=entry(g,tags,e['id'])
    elif tags.get('landuse') or tags.get('natural')=='wood':land+=entry(g,tags,e['id'])
# Merge duplicate water representations without changing mapped shorelines.
water=unary_union([Polygon(p['points'],p['holes']) for p in waters]);water_entries=entry(water,{},'OSM-union')
tif=W/'Copernicus_DSM_COG_10_N34_00_E126_00_DEM.tif';im=Image.open(tif);a=np.asarray(im)
dx,dy,_=im.tag_v2[33550];_,_,_,lon,lat,_=im.tag_v2[33922]
assert im.tag_v2[34735][7]==2, 'PixelIsPoint DEM required'
def uv(x,z):return (origin['lon']+x/mx-lon)/dx,(lat-origin['lat']+z/mz)/dy
u0,v0=uv(-3100,-2700);u1,v1=uv(3100,2300)
left,top=math.floor(u0)-1,math.floor(v0)-1;right,bottom=math.ceil(u1)+1,math.ceil(v1)+1
crop=a[top:bottom+1,left:right+1]
def sample(x,z):
    u,v=uv(x,z);i,j=math.floor(u),math.floor(v);f,h=u-i,v-j
    return float((a[j,i]*(1-f)+a[j,i+1]*f)*(1-h)+(a[j+1,i]*(1-f)+a[j+1,i+1]*f)*h)
# Use water-surface DSM samples as a local reference, never a water-level survey.
samples=[]
for p in water_entries:
    poly=Polygon(p['points'],p['holes'])
    for x in range(-2200,2000,100):
        for z in range(-2200,1800,100):
            from shapely.geometry import Point
            if poly.contains(Point(x,z)):samples.append(sample(x,z))
datum=float(np.median(samples));tower_sample=sample(0,0)
terrain=dict(dataset='Copernicus DEM GLO-30, AWS 2021 public release',nativeResolutionMetres=30,originWGS84=origin,
    longitudeSpacingDegrees=dx,latitudeSpacingDegrees=dy,sampleOriginLongitude=lon+left*dx,sampleOriginLatitude=lat-top*dy,
    heightsMetres=crop.tolist(),width=crop.shape[1],height=crop.shape[0],pixelIsPoint=True,modelDatumMetres=datum,
    towerSurfaceMetres=tower_sample,interpretedTowerPadMetres=tower_sample-8,
    platformInterpretation='DSM includes canopy. Subtract an explicit 8m canopy allowance at the mapped tower point; no bare-ground survey available.',
    sourceUrl='https://copernicus-dem-30m.s3.amazonaws.com/'+tif.stem+'/'+tif.name,sourceSha256=hashlib.sha256(tif.read_bytes()).hexdigest(),
    limitations=['30m nominal DSM, vegetation and buildings included. Approximately 2010-2015 observations; 2021 edited release.',
    'Tower base, stair dimensions and nearby grading are photo-interpreted. Original field parcel boundaries may be incomplete.'])
geo=dict(originWGS84=origin,metresPerLongitudeDegree=mx,bounds=[-3100,3100,-2700,2300],water=water_entries,land=land,roads=roads,buildings=buildings,
    source='OpenStreetMap contributors, ODbL 1.0',sourceFileSha256=hashlib.sha256((W/'osm.json').read_bytes()).hexdigest(),
    towerSource='https://www.openstreetmap.org/node/6572786690',license='https://www.openstreetmap.org/copyright')
(O/'geography.json').write_text(json.dumps(geo,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
(O/'native-terrain.json').write_text(json.dumps(terrain,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print(json.dumps(dict(waterArea=water.area,land=len(land),buildings=len(buildings),roads=len(roads),nativeGrid=list(crop.shape),datum=datum,towerSurface=tower_sample,padInterpretation=tower_sample-8)),flush=True)
