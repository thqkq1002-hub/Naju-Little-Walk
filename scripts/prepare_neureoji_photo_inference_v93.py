"""Fill photographed cultivation missing from OSM; never embed source imagery."""
from pathlib import Path
import json, math, random, sys, subprocess
from PIL import Image, ImageDraw
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'work/python-geo'))
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
G=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
W=R/'work/neureoji-v93';D=json.loads((W/'landscape.json').read_text());rng=random.Random(9394)
def world(p):
    lon=126.515+p[0]/1800*.045;lat=34.933375-p[1]/1350*.03375
    return [(lon-G['originWGS84']['lon'])*G['metresPerLongitudeDegree'],(G['originWGS84']['lat']-lat)*111320]
# Visually interpreted cultivated envelopes on the near-facing spit, not cadastral boundaries.
pixel_envelopes=[[(689,216),(770,203),(816,260),(807,300),(741,294)],
    [(746,302),(803,280),(878,306),(863,348),(798,339)],
    [(760,337),(907,362),(917,420),(857,428),(866,484),(817,503),(794,479),(790,430),(750,410)],
    [(812,495),(856,467),(900,491),(899,537),(852,558),(813,538)]]
polys=[Polygon([world(p) for p in points]).buffer(0) for points in pixel_envelopes];fields=unary_union(polys)
water=unary_union([Polygon(p['points'],p['holes']) for p in G['water']]);fields=fields.difference(water)
image=Image.open(R/'assets/neureoji-v93/landcover-original.png');draw=ImageDraw.Draw(image);size=image.width
def px(p):return ((p[0]+3100)/6200*size,(p[1]+2700)/5000*size)
def pieces(p):return [p] if p.geom_type=='Polygon' else [q for q in getattr(p,'geoms',[]) if q.geom_type=='Polygon']
palette=['#78a34c','#8bb65a','#7fa84d','#9caf65','#76a348','#95b66a'];extra=[]
for poly in pieces(fields):
    center=(poly.centroid.x,poly.centroid.y);local=affinity.rotate(poly,24,origin=center);minx,minz,maxx,maxz=local.bounds
    x=minx
    while x<maxx:
        z=minz
        while z<maxz:
            for part in pieces(local.intersection(box(x,z,x+31,z+42))):
                if part.area<15:continue
                p=affinity.rotate(part,-24,origin=center);points=list(p.exterior.coords);color=rng.choice(palette)
                draw.polygon([px(q) for q in points],fill=color);draw.line([px(q) for q in points],fill='#b6c491',width=1)
                extra.append(dict(points=points,color=color,area=p.area,source='Satellite/photo-interpreted cultivated envelope; inferred subdivisions'))
            z+=43
        x+=32
pixels=np.array(image);mask=np.max(np.abs(pixels.astype(int)-np.array([127,149,98])),axis=2)<8
pixels[mask]=np.clip(pixels[mask].astype(int)+np.array([-44,-40,-37]),0,255).astype('uint8')
Image.fromarray(pixels).save(R/'assets/neureoji-v93/landcover-original.png')
before=len(D['trees']);field_buffer=fields.buffer(8);D['trees']=[p for p in D['trees'] if not field_buffer.contains(Point(p[0],p[2]))]
removed=before-len(D['trees'])
# A continuous riparian canopy follows the actual mapped water and photographed wooded margins.
shore=water.buffer(60).difference(water.buffer(7));existing={(round(p[0]/8),round(p[2]/8)) for p in D['trees']}
native=json.loads((R/'knowledge/sources/neureoji-v92/native-terrain.json').read_text(encoding='utf8'))
def height(x,z):
    u=(G['originWGS84']['lon']+x/G['metresPerLongitudeDegree']-native['sampleOriginLongitude'])/native['longitudeSpacingDegrees']
    v=(native['sampleOriginLatitude']-G['originWGS84']['lat']+z/111320)/native['latitudeSpacingDegrees']
    i,j=math.floor(u),math.floor(v);f,h=u-i,v-j;a=native['heightsMetres']
    raw=(a[j][i]*(1-f)+a[j][i+1]*f)*(1-h)+(a[j+1][i]*(1-f)+a[j+1][i+1]*f)*h
    return max(.12,raw-native['modelDatumMetres']-8)
farms=unary_union([Polygon(p['points'],p['holes']) for p in G['land'] if p['tags'].get('landuse') in ('farmland','orchard')]).union(fields).buffer(5)
for z in range(-1500,301,8):
    for x in range(-1700,351,8):
        p=Point(x,z)
        if math.hypot(x,z)<60 or not shore.contains(p) or farms.contains(p) or (round(x/8),round(z/8)) in existing:continue
        D['trees'].append([x+rng.uniform(-2,2),height(x,z),z+rng.uniform(-2,2),rng.uniform(6,9),rng.randrange(4)])
D['parcels'].extend(extra)
(W/'landscape.json').write_text(json.dumps(D,separators=(',',':')),encoding='utf8')
record=json.loads((R/'knowledge/sources/neureoji-v93/landscape.json').read_text())
record.update(photoInferredFieldEnvelopes=[list(p.exterior.coords) for p in pieces(fields)],photoInferredAreaMetres2=fields.area,
    woodlandCrowns=len(D['trees']),inferredParcelCount=len(D['parcels']),panoramaTargetMetres=[-550,-900],
    photoInferenceBasis='Reference-only Esri 1800x1350 returned extent, source fieldwork photo 08.jpg; internal divisions interpreted.')
(R/'knowledge/sources/neureoji-v93/landscape.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
base=subprocess.check_output(['git','show','d1611ad:public/neureoji-world.json']);(W/'base-world.json').write_bytes(base)
print(json.dumps(dict(removedTreeCrowns=removed,fieldArea=fields.area,newCrowns=len(D['trees']),newParcels=len(extra))),flush=True)
