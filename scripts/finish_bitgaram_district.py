"""Complete the district overview from OSM and satellite interpretation; no interior edits."""
import bpy,bmesh,sys,json,math,random,ast,gzip
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];S=R/'knowledge/sources/bitgaram';O=R/'outputs/bitgaram';target=O/'bitgaram-district-complete-v5.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
bpy.ops.wm.open_mainfile(filepath=str(O/'bitgaram-drone-detail.blend'))
mod=ast.parse((R/'scripts/refine_bitgaram_district.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in mod.body if isinstance(n,ast.ClassDef) and n.name=='Batch'],type_ignores=[]),'<batch>','exec'))
old=json.loads((S/'geometry.json').read_text(encoding='utf-8'))['ways'];fresh=json.loads((S/'district-2026-09-20.json').read_text(encoding='utf-8'))['ways'];ways={w['id']:w for w in old};ways.update({w['id']:w for w in fresh});ways=list(ways.values())
oldids={w['id'] for w in old};oldbuildings={w['id'] for w in old if w['tags'].get('building')};g=Batch();rng=random.Random(450920)
counts=dict(mapped_buildings=0,estimated_roofs=0,landuse_areas=0,parking_areas=0,sports_areas=0,road_segments=0,trees=0,field_parcels=0)
log=[]
def inside(p,poly):
 x,z=p;hit=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def center(p):return (sum(v[0] for v in p)/len(p),sum(v[1] for v in p)/len(p))
def bounds(p):return (min(q[0] for q in p),max(q[0] for q in p),min(q[1] for q in p),max(q[1] for q in p))
def inframe(x,z):return -2100<x<2100 and -1700<z<1800
def dist(p,a,b):
 dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/max(.001,dx*dx+dz*dz)))
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dz)
water=[w['points'] for w in ways if w['tags'].get('natural')=='water' and w['points'][0]==w['points'][-1]]
buildings=[w['points'] for w in ways if w['tags'].get('building')]
blocked=[(bounds(p),p) for p in water+buildings]
roads=[]
widths={'primary':26,'secondary':22,'tertiary':16,'residential':8,'unclassified':7,'service':5}
for w in ways:
 if w['tags'].get('highway') in widths:
  roads.extend((a,b,widths[w['tags']['highway']]) for a,b in zip(w['points'],w['points'][1:]))
blockgrid={};roadgrid={};cell=64
def cells(x0,x1,z0,z1):
 for xx in range(math.floor(x0/cell),math.floor(x1/cell)+1):
  for zz in range(math.floor(z0/cell),math.floor(z1/cell)+1):yield (xx,zz)
def register_block(poly):
 box=bounds(poly);x0,x1,z0,z1=box
 for key in cells(x0-12,x1+12,z0-12,z1+12):blockgrid.setdefault(key,[]).append((box,poly))
for box,poly in blocked:register_block(poly)
for a,b,ww in roads:
 pad=ww/2+12
 for key in cells(min(a[0],b[0])-pad,max(a[0],b[0])+pad,min(a[1],b[1])-pad,max(a[1],b[1])+pad):roadgrid.setdefault(key,[]).append((a,b,ww))
def free(x,z,margin=3):
 for (x0,x1,z0,z1),p in blockgrid.get((math.floor(x/cell),math.floor(z/cell)),[]):
  if x0-margin<x<x1+margin and z0-margin<z<z1+margin:
   if inside((x,z),p) or min(dist((x,z),a,b) for a,b in zip(p,p[1:]+p[:1]))<margin:return False
 return True
def roadnear(x,z,margin=0):
 return any(dist((x,z),a,b)<ww/2+margin for a,b,ww in roadgrid.get((math.floor(x/cell),math.floor(z/cell)),[]))
def tree(x,z,h=5,r=2.6):
 if not inframe(x,z) or not free(x,z,2) or roadnear(x,z,2):return
 g.box('district_tree_trunk',x,h*.3,z,.45,h*.6,.45,'#736951',record=False)
 for ox,oz,rr,yy in [(0,0,r,h),(-r*.48,r*.25,r*.72,h*.84),(r*.4,-r*.2,r*.68,h*.92)]:
  n=8;v=[(x+ox,yy+rr*.75,z+oz),(x+ox,yy-rr*.55,z+oz)]+[(x+ox+math.cos(i*math.tau/n)*rr,yy,z+oz+math.sin(i*math.tau/n)*rr) for i in range(n)]
  g.mesh('district_tree_crown',v,[(0,2+i,2+(i+1)%n) for i in range(n)]+[(1,2+(i+1)%n,2+i) for i in range(n)],['#638455','#76935f','#52794c'][counts['trees']%3])
 counts['trees']+=1
def building(p,h,kind,ident,estimated=False):
 col=['#d4d0c0','#c8c9c1','#d8d9cf','#b9c5c5'][int(ident)%4];g.polygon('infill_body',p,0,h,col)
 for a,b in zip(p,p[1:]+p[:1]):
  ll=math.dist(a,b)
  if ll<3:continue
  ux,uz=(b[0]-a[0])/ll,(b[1]-a[1])/ll
  for y in range(3,int(h)-1,3):g.segment('infill_glazing',(a[0]+ux,a[1]+uz),(b[0]-ux,b[1]-uz),.25,1.35,'#78959a',base=y,record=False)
  g.segment('roof_edge',a,b,.32,.55,'#e1e0d4',base=h,record=False)
  if ll>16 and h>16:
   for d in range(6,int(ll)-2,9):g.box('infill_vertical',a[0]+ux*d,h/2,a[1]+uz*d,.42,h,.42,'#deddd1',record=False)
 cx,cz=center(p)
 if inside((cx,cz),p):
  g.box('roof_equipment',cx,h+.6,cz,2,1.2,2,'#8c9c99',record=False)
  if h<15:g.box('roof_patch',cx,h+.03,cz,4,.05,4,['#8a9d8c','#899ca7'][int(ident)%2],record=False)
 log.append(dict(id=ident,height=h,estimated_footprint=estimated,kind=kind))

# Mapped ground categories give meaning to the previously uniform empty plane.
for w in ways:
 p=w['points'];t=w['tags'];cx,cz=center(p)
 if not inframe(cx,cz):continue
 closed=p[0]==p[-1]
 if closed and t.get('natural')=='water' and w['id'] not in oldids:g.polygon('mapped_additional_water',p,-.10,.08,'#547e82')
 if t.get('building') and w['id'] not in oldbuildings and closed:
  level=t.get('building:levels','');height=t.get('height','');kind=t['building']
  h=float(height) if height.replace('.','').isdigit() else float(level)*3.1 if level.replace('.','').isdigit() else 48 if kind=='apartments' else 12 if kind in ['school','commercial','public','university'] else 7.5
  building(p[:-1],min(h,160),kind,w['id']);counts['mapped_buildings']+=1
 if closed and math.hypot(cx,cz)>600:
  col=None
  if t.get('landuse')=='residential':col='#b6bda5'
  elif t.get('landuse')=='commercial':col='#c4c0ae'
  elif t.get('landuse')=='construction':col='#b7a481'
  elif t.get('landuse')=='farmland':col=['#a7ad7c','#bbb487','#94a37a'][int(w['id'])%3]
  elif t.get('natural')=='wood' or t.get('landuse')=='forest':col='#7e9968'
  elif t.get('leisure') in ['park','garden','playground']:col='#9db580'
  elif t.get('amenity') in ['school','university','hospital']:col='#b9c4b2'
  if col:g.polygon('mapped_landuse',p,-.17,.015,col);counts['landuse_areas']+=1
  if t.get('amenity')=='parking':
   g.polygon('parking_surface',p,.08,.012,'#9ba5a0');counts['parking_areas']+=1
   x0,x1,z0,z1=bounds(p)
   for x in range(math.ceil(x0+3),int(x1-3),3):
    for z in range(math.ceil(z0+3),int(z1-4),13):
     if inside((x,z),p) and inside((x,z+4),p):g.segment('parking_stripe',(x,z),(x,z+4),.15,.008,'#e7e5d4',base=.11,record=False)
  if t.get('leisure')=='pitch':
   g.polygon('sport_surface',p,.11,.015,'#689776' if t.get('sport')!='basketball' else '#b68e73');counts['sports_areas']+=1
   for a,b in zip(p,p[1:]):g.segment('sport_line',a,b,.35,.01,'#e3e7cf',base=.14,record=False)
 if t.get('highway') in widths and w['id'] not in oldids:
  ww=widths[t['highway']]
  for a,b in zip(p,p[1:]):
   if not inframe(*center([a,b])):continue
   g.segment('new_road',a,b,ww,.02,'#939f99',base=.05,record=False);counts['road_segments']+=1
   if ww>=8:
    ll=math.dist(a,b)
    if ll<2:continue
    ux,uz=(b[0]-a[0])/ll,(b[1]-a[1])/ll
    for side in [-1,1]:g.segment('new_sidewalk',(a[0]-uz*(ww/2+1)*side,a[1]+ux*(ww/2+1)*side),(b[0]-uz*(ww/2+1)*side,b[1]+ux*(ww/2+1)*side),1.8,.02,'#d3d0bc',base=.08,record=False)
print('Mapped additions',counts,flush=True)
# Conservative satellite roof candidates are further screened against exact mapped polygons.
for i,c in enumerate(json.loads((S/'district-roof-candidates.json').read_text())['candidates']):
 x,z=c['center'];ww,dd=c['size']
 if not inframe(x,z) or not free(x,z,7) or roadnear(x,z,6):continue
 nearest=min(roads,key=lambda road:dist((x,z),road[0],road[1]));a,b,_=nearest;angle=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(angle),math.sin(angle)
 poly=[(x+dx*co-dz*si,z+dx*si+dz*co) for dx,dz in [(-ww/2,-dd/2),(ww/2,-dd/2),(ww/2,dd/2),(-ww/2,dd/2)]]
 if any(not free(px,pz,2) or roadnear(px,pz,1) for px,pz in poly):continue
 building(poly,[6.8,9.5,12.0][i%3],'satellite_lowrise',str(900000+i),True);register_block(poly);counts['estimated_roofs']+=1

# Smaller mapped park/residential spaces get plants between roads and built footprints.
for w in ways:
 p=w['points'];t=w['tags'];cx,cz=center(p)
 if p[0]!=p[-1] or not inframe(cx,cz) or math.hypot(cx,cz)<650:continue
 natural=t.get('natural')=='wood' or t.get('landuse')=='forest';park=t.get('leisure') in ['park','garden'];res=t.get('landuse')=='residential'
 if not (natural or park or res):continue
 x0,x1,z0,z1=bounds(p);num=min(1400,int((x1-x0)*(z1-z0)/(120 if natural else 380 if park else 1800)))
 for j in range(num):
  x,z=rng.uniform(x0,x1),rng.uniform(z0,z1)
  if inside((x,z),p):tree(x,z,rng.uniform(4,8),rng.uniform(2.2,4))
for a,b,ww in roads:
 ll=math.dist(a,b)
 if ll<32 or ww<8:continue
 ux,uz=(b[0]-a[0])/ll,(b[1]-a[1])/ll
 for d in range(16,int(ll)-8,42):
  for side in [-1,1]:
   x,z=a[0]+ux*d-uz*(ww/2+4)*side,a[1]+uz*d+ux*(ww/2+4)*side
   if math.hypot(x,z)>640:tree(x,z,5.5,2.7)
# Satellite-observed agricultural/woodland sectors: schematic parcel edges are estimates.
extent=json.loads((S/'district-satellite-extent.json').read_text())['extent']
def photo(x,y):
 lon=extent['xmin']+x*(extent['xmax']-extent['xmin']);lat=extent['ymax']-y*(extent['ymax']-extent['ymin'])
 return ((lon-126.790447)*111320*math.cos(math.radians(35.016925)),(35.016925-lat)*111320)
sectors=[[(.06,.19),(.13,.19),(.14,.27),(.065,.29)],[(.02,.28),(.10,.30),(.105,.37),(.025,.36)],[(.19,.18),(.23,.18),(.23,.27),(.18,.26)],[(.30,.71),(.39,.71),(.43,.77),(.35,.80),(.29,.77)],[(.40,.72),(.52,.70),(.55,.75),(.48,.79),(.43,.78)],[(.53,.70),(.61,.72),(.64,.78),(.57,.79),(.55,.75)],[(.67,.14),(.75,.12),(.77,.25),(.71,.29),(.67,.24)],[(.78,.15),(.90,.18),(.88,.29),(.78,.28)],[(.75,.29),(.89,.31),(.86,.39),(.77,.38)],[(.73,.39),(.81,.41),(.79,.47),(.73,.46)],[(.16,.72),(.25,.70),(.27,.78),(.19,.79)],[(.35,.81),(.47,.81),(.48,.87),(.36,.87)]]
for index,points in enumerate(sectors):
 p=[photo(*q) for q in points];cx,cz=center(p)
 if not inframe(cx,cz):continue
 g.polygon('satellite_agricultural_sector',p,-.25,.01,'#a7ad83');x0,x1,z0,z1=bounds(p)
 for x in range(math.ceil(x0),int(x1),76):
  for z in range(math.ceil(z0),int(z1),44):
   poly=[(x+2,z+2),(x+72,z+2),(x+72,z+40),(x+2,z+40)]
   if not all(inside(q,p) and inframe(*q) for q in poly):continue
   color=['#9ba879','#b7b087','#8a9f73','#b2b592','#a6aa7e'][(x//76+z//44+index)%5]
   g.polygon('estimated_field_parcel',poly,-.23,.01,color);counts['field_parcels']+=1
   for zz in range(z+8,z+40,8):g.segment('field_row',(x+3,zz),(x+71,zz),.45,.002,'#b6bb94',base=-.215,record=False)
woods=[[(.26,.018),(.40,.028),(.40,.095),(.33,.135),(.25,.12)],[(.13,.03),(.20,.01),(.22,.075),(.18,.105),(.13,.09)],[(.07,.42),(.12,.40),(.13,.46),(.085,.51)]]
for points in woods:
 p=[photo(*q) for q in points];cx,cz=center(p)
 if not inframe(cx,cz):continue
 g.polygon('satellite_woodland_sector',p,-.23,.02,'#7d9765');x0,x1,z0,z1=bounds(p)
 for _ in range(min(1100,int((x1-x0)*(z1-z0)/100))):
  x,z=rng.uniform(x0,x1),rng.uniform(z0,z1)
  if inside((x,z),p):tree(x,z,rng.uniform(5,10),rng.uniform(3,5))
g.finish();scene=bpy.context.scene
# Keep each source layer editable. Only material batches generated here are already consolidated.
bpy.ops.wm.save_as_mainfile(filepath=str(target))
# Consolidate repeated static colors only after the editable file has been saved.
from blender_static_batch import batch
batch(scene)
out=R/'public/models/bitgaram-overview.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
(S/'district-completion-metrics.json').write_text(json.dumps(dict(counts=counts,buildings=log,glb_bytes=out.stat().st_size,gzip_bytes=Path(str(out)+'.gz').stat().st_size),ensure_ascii=False,indent=2),encoding='utf-8')
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=40
for name,position,aim,scale in [('district-complete',(1400,2450,2600),(180,0,0),4100),('district-south',(500,900,1650),(200,0,650),2050)]:
 scene.camera.location=g.bp(*position);scene.camera.rotation_euler=(Vector(g.bp(*aim))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
 scene.render.filepath=str(O/(name+'-v5.png'));bpy.ops.render.render(write_still=True)
print('DISTRICT COMPLETE',counts,flush=True)
