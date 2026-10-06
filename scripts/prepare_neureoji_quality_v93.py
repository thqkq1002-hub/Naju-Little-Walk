"""Original map-derived scenery and foliage maps; photographs are inspection only."""
from pathlib import Path
import json, math, random, sys, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'work/python-geo'))
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union, triangulate
from shapely import affinity
W=R/'work/neureoji-v93';W.mkdir(parents=True,exist_ok=True)
A=R/'assets/neureoji-v93';A.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/neureoji-v93';K.mkdir(parents=True,exist_ok=True)
G=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
T=json.loads((R/'knowledge/sources/neureoji-v92/native-terrain.json').read_text(encoding='utf8'))
origin=G['originWGS84'];mx=G['metresPerLongitudeDegree'];B=T['interpretedTowerPadMetres'];rng=random.Random(9304)
water=unary_union([Polygon(p['points'],p['holes']) for p in G['water']])
wood=unary_union([Polygon(p['points'],p['holes']) for p in G['land'] if p['tags'].get('natural')=='wood' or p['tags'].get('landuse')=='forest'])
farms=[Polygon(p['points'],p['holes']) for p in G['land'] if p['tags'].get('landuse') in ('farmland','orchard')]
farmland=unary_union(farms)
native=Image.open(R/'work/neureoji-v92/Copernicus_DSM_COG_10_N34_00_E126_00_DEM.tif');dem=np.asarray(native)
dx,dy,_=native.tag_v2[33550];_,_,_,lon0,lat0,_=native.tag_v2[33922]

def native_height(x,z):
    u=(origin['lon']+x/mx-lon0)/dx;v=(lat0-origin['lat']+z/111320)/dy
    i,j=math.floor(u),math.floor(v);f,h=u-i,v-j
    if not (0<=i<dem.shape[1]-1 and 0<=j<dem.shape[0]-1):raise ValueError('Scenery outside native DEM')
    return float((dem[j,i]*(1-f)+dem[j,i+1]*f)*(1-h)+(dem[j+1,i]*(1-f)+dem[j+1,i+1]*f)*h)-T['modelDatumMetres']

def height(x,z):
    p=Point(x,z);raw=native_height(x,z)
    if water.contains(p):return -1.2
    wooded=wood.contains(p) or (raw>18 and not farmland.contains(p))
    y=max(.12,raw-(8 if wooded else 0))
    dist=water.distance(p)
    # Exact mapped shoreline meets the common modeled water datum, without dry triangles in the river.
    if dist<22:y=.12+(y-.12)*min(1,dist/22)
    r=math.hypot(x,z);t=max(0,min(1,(r-17)/60));t=t*t*(3-2*t)
    return B*(1-t)+y*t if r<77 else y

def polygons(shape):
    if shape.is_empty:return []
    return [shape] if shape.geom_type=='Polygon' else [p for p in getattr(shape,'geoms',[]) if p.geom_type=='Polygon']

# Every land face is clipped to the mapped water boundary. River geometry itself is retained unchanged.
verts=[];faces=[]
for j in range(200):
    z=-2700+j*25
    for i in range(248):
        x=-3100+i*25;q=box(x,z,x+25,z+25)
        if water.covers(q):continue
        pieces=polygons(q.difference(water)) if water.intersects(q) else [q]
        for p in pieces:
            for tri in triangulate(p):
                if not p.covers(tri):continue
                offset=len(verts)
                verts.extend([[xx,height(xx,zz)-.06,zz] for xx,zz in list(tri.exterior.coords)[:3]])
                faces.append([offset,offset+1,offset+2])
print('Prepared terrain shoreline triangles',len(faces),flush=True)

# Original agricultural parcel subdivisions lie inside mapped agricultural envelopes.
# Their internal boundaries and crop colours are interpreted, not cadastral survey data.
size=3072;land=Image.new('RGB',(size,size),'#7f9562');draw=ImageDraw.Draw(land)
def pixel(x,z):return ((x+3100)/6200*size,(z+2700)/5000*size)
for p in G['land']:
    typ=p['tags'].get('landuse',p['tags'].get('natural'))
    color='#405d38' if typ in ('forest','wood') else '#719452' if typ in ('farmland','orchard') else '#94987e'
    draw.polygon([pixel(*a) for a in p['points']],fill=color)
    for h in p['holes']:draw.polygon([pixel(*a) for a in h],fill='#7f9562')
parcels=[];palette=['#7d9d4a','#84a24e','#90aa58','#779b45','#a2ab67','#689744','#909e60','#9caa68']
for p in farms:
    rect=list(p.minimum_rotated_rectangle.exterior.coords);a,b=max(zip(rect,rect[1:]),key=lambda e:math.dist(*e))
    angle=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]));center=(p.centroid.x,p.centroid.y)
    local=affinity.rotate(p,-angle,origin=center);minx,minz,maxx,maxz=local.bounds
    for x in np.arange(minx,maxx,48):
        for z in np.arange(minz,maxz,76):
            for cell in polygons(local.intersection(box(x,z,x+47,z+75))):
                if cell.area<50:continue
                poly=affinity.rotate(cell,angle,origin=center);pts=list(poly.exterior.coords)[:-1]
                color=rng.choice(palette);draw.polygon([pixel(*q) for q in pts],fill=color)
                draw.line([pixel(*q) for q in list(poly.exterior.coords)],fill='#b5bc8a',width=1)
                parcels.append(dict(points=pts,color=color,area=poly.area,source='OSM agricultural envelope; inferred internal divisions'))
                for row in np.arange(z+5,z+74,9):
                    strip=cell.intersection(LineString([(x,row),(x+47,row)]))
                    for line in [strip] if strip.geom_type=='LineString' else getattr(strip,'geoms',[]):
                        if line.geom_type=='LineString':
                            line=affinity.rotate(line,angle,origin=center)
                            draw.line([pixel(*q) for q in line.coords],fill=color,width=1)
for p in G['water']:draw.polygon([pixel(*q) for q in p['points']],fill='#657567')
arr=np.array(land).astype(np.int16);noise=np.random.default_rng(93).normal(0,2.0,(size,size,1));arr=np.clip(arr+noise,0,255).astype('uint8')
Image.fromarray(arr).save(A/'landcover-original.png')

# An original painted foliage cluster, with small leaf silhouettes rather than oversized individual cards.
leaf=Image.new('RGBA',(512,512),(0,0,0,0));painter=ImageDraw.Draw(leaf)
for k in range(17):
    a=rng.random()*math.tau;rr=rng.uniform(0,130);cx=256+math.cos(a)*rr;cy=255+math.sin(a)*rr*.80
    for n in range(27):
        az=rng.random()*math.tau;rad=rng.uniform(0,90);x=cx+math.cos(az)*rad;y=cy+math.sin(az)*rad*.75
        l=rng.uniform(10,22);w=l*rng.uniform(.35,.65);shade=rng.uniform(.72,1.15)
        col=(int(68*shade),int(112*shade),int(41*shade),255)
        points=[(x-l,y),(x-w*.4,y-w),(x+l,y+1),(x+w*.4,y+w)]
        painter.polygon(points,fill=col);painter.line([(x-l*.5,y),(x+l*.5,y)],fill=(68,102,38,255),width=1)
leaf.save(A/'leaf-cluster-original.png')

# Broad crown atlas contains thousands of original painted leaf spots and an irregular alpha silhouette.
crown=Image.new('RGBA',(512,512),(0,0,0,0));painter=ImageDraw.Draw(crown)
lobes=[]
for k in range(18):
    a=k*math.tau/18;r=rng.uniform(70,146);cx=256+math.cos(a)*r;cy=244+math.sin(a)*r*.68;rr=rng.uniform(53,91)
    lobes.append((cx,cy,rr));painter.ellipse((cx-rr,cy-rr*.83,cx+rr,cy+rr*.83),fill=(55,87,36,245))
for k in range(9000):
    cx,cy,rr=rng.choice(lobes);a=rng.random()*math.tau;r=rr*math.sqrt(rng.random());x=cx+math.cos(a)*r;y=cy+math.sin(a)*r*.83
    l=rng.uniform(1,4);shade=.60+.37*(1-y/512)+rng.uniform(0,.6)
    painter.ellipse((x-l,y-l*.7,x+l,y+l*.7),fill=(int(58*shade),int(99*shade),int(41*shade),255))
crown.save(A/'crown-original.png')

# Dense crowns are constrained to mapped woodland and river margins, never planted over mapped fields.
shore=water.buffer(48).difference(water.buffer(5));trees=[]
for z in range(-2670,2280,16):
    for x in range(-3070,3080,16):
        xx=x+rng.uniform(-5.5,5.5);zz=z+rng.uniform(-5.5,5.5);p=Point(xx,zz);r=math.hypot(xx,zz)
        if r<60 or water.buffer(4).contains(p) or farmland.buffer(3).contains(p):continue
        hh=height(xx,zz)
        if wood.contains(p) or shore.contains(p) or native_height(xx,zz)>22:
            if rng.random()<.92:trees.append([xx,hh,zz,rng.uniform(5.5,10.5),rng.randrange(4)])
json.dump(dict(vertices=verts,faces=faces,trees=trees,pad=B,parcels=parcels),open(W/'landscape.json','w',encoding='utf8'),separators=(',',':'))

# True distant DSM mountain mesh extends the visual backdrop, with no additional walk floors.
farv=[];farf=[];farcolors=[];step=250;nx=69
for j in range(nx):
    z=-8500+j*step
    for i in range(nx):
        x=-8500+i*step;y=max(-1.2,native_height(x,z)-6)
        if -3350<x<3350 and -2950<z<2550:y=height(x,z)-.12
        farv.append([x,y-.2,z]);distance=math.hypot(x,z);t=max(0,min(1,(distance-2200)/10000))
        farcolors.append([.27+.16*t,.40+.12*t,.29+.22*t,1])
for j in range(nx-1):
    for i in range(nx-1):
        x=-8500+(i+.5)*step;z=-8500+(j+.5)*step
        if -3100<x<3100 and -2700<z<2300:continue
        n=j*nx+i;farf.append([n,n+1,n+nx+1,n+nx])
json.dump(dict(vertices=farv,faces=farf,colors=farcolors),open(W/'distant-terrain.json','w',encoding='utf8'),separators=(',',':'))
record=dict(revision='neureoji-quality-v93',mapOrigin=origin,nativeDEM=T['sourceUrl'],nativeResolutionMetres=30,
    mappedRiverAreaMetres2=water.area,riverBoundaryChanged=False,terrainFaces=len(faces),woodlandCrowns=len(trees),
    inferredParcelCount=len(parcels),farBackdropExtentMetres=[-8500,8500,-8500,8500],
    limitations=['Internal field divisions/crop colours are original interpretations inside OSM farm boundaries, not measured parcel boundaries.',
    'DSM includes canopy; 8m local and 6m distant canopy allowances are interpreted, not bare-ground measurements.',
    'Woodland crown locations and vegetation species are inferred from photographs and mapped land use.',
    'Source photographs and satellite imagery are inspection only, not embedded assets.'])
(K/'landscape.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False),flush=True)
