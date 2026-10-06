"""Satellite/photo-informed Blender authoring with synchronized walking surfaces.

The Esri image is a review reference only. No reference pixels enter the GLB.
Vertical profiles/dimensions and tree clearance remain interpreted, not surveyed.
"""
import bpy,json,math,sys,hashlib,gzip,struct,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
from bitgaram_terrain_v89 import Terrain
O=R/'outputs/bitgaram-v101';O.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/bitgaram/access-v101';K.mkdir(parents=True,exist_ok=True)
revision=next((a.split('=')[1] for a in sys.argv if a.startswith('--revision=')),'v101')
SOURCE=R/'outputs/terrain-v89/bitgaram-park-glo30-terrain-v89d.blend';TARGET=O/('bitgaram-access-'+revision+'.blend')
if TARGET.exists():raise RuntimeError('Artist revision already exists; use a new revision filename')
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
backup=O/'world-before.json'
if not backup.exists():shutil.copyfile(R/'public/bitgaram-park-world.json',backup)
w=json.loads(backup.read_text(encoding='utf8'));T=Terrain(next(s['footprint'] for s in w['solids'] if s['name']=='photo_exhibition_shell'))
extent=json.loads((R/'work/bitgaram-v101/satellite-export.json').read_text())['extent']
def map_pixel(p):
 mx=extent['xmin']+p[0]/1200*(extent['xmax']-extent['xmin']);my=extent['ymax']-p[1]/1200*(extent['ymax']-extent['ymin'])
 lon=math.degrees(mx/6378137);lat=math.degrees(2*math.atan(math.exp(my/6378137))-math.pi/2)
 return [(lon-T.origin['lon'])*T.mx,(T.origin['lat']-lat)*111320]
# Visible white covered slide traced at native image size. Gaps under crowns
# are interpolated; building lean and unknown image date limit absolute accuracy.
slide_pixels=[[515,462],[504,484],[494,518],[487,552],[479,590],[466,625],[451,663],[448,689],[452,713],[463,743],[481,778]]
# Separate outdoor timber route: visible flights/turns, partially occluded
# sections interpreted between them. Keep it distinct from the covered slide.
outdoor_pixels=[[601,470],[604,521],[603,574],[606,617],[550,636],[539,661],[514,682],[500,700],[570,706],[570,718],[486,726],[496,777]]
slide_plan=[map_pixel(p) for p in slide_pixels];outdoor_plan=[map_pixel(p) for p in outdoor_pixels]
def densify(points,step=.30):
 out=[];lengths=[0]
 for a,b in zip(points,points[1:]):
  n=max(1,math.ceil(math.dist(a,b)/step))
  out.extend([[a[k]+(b[k]-a[k])*i/n for k in range(2)] for i in range(n)])
 out.append(points[-1])
 for a,b in zip(out,out[1:]):lengths.append(lengths[-1]+math.dist(a,b))
 return out,lengths
sp,sd=densify(slide_plan,.18)
def interpreted_heights(points,distances):
 lo=T.upper-T.raw_ground(*points[0]);hi=T.lower-T.raw_ground(*points[-1]);out=[];last=T.upper
 for (x,z),d in zip(points,distances):
  t=d/distances[-1];y=min(last,max(T.lower,T.raw_ground(x,z)+lo*(1-t)+hi*t));out.append(y);last=y
 out[-1]=T.lower;return out
slide=[(x,y,z) for (x,z),y in zip(sp,interpreted_heights(sp,sd))]
def offset_route(route,offset):
 out=[]
 for i,(x,y,z) in enumerate(route):
  a,b=route[max(0,i-1)],route[min(len(route)-1,i+1)];dx,dz=b[0]-a[0],b[2]-a[2];n=math.hypot(dx,dz)
  out.append((x+offset*dz/n,y,z-offset*dx/n))
 return out
stairs=offset_route(slide,-1.25)
# Outdoor floors have horizontal turn landings and <= 16 cm treads. The total
# rise is distributed over flights, rather than forcing arbitrary DSM wiggles.
outdoor=[];landing_centres=[]
lengths=[math.dist(a,b) for a,b in zip(outdoor_plan,outdoor_plan[1:])];distances=[0]
for L in lengths:distances.append(distances[-1]+L)
node_heights=interpreted_heights(outdoor_plan,distances)
for i,(a,b,L) in enumerate(zip(outdoor_plan,outdoor_plan[1:],lengths)):
 height=node_heights[i];rise=height-node_heights[i+1];flat=min(1.05,L*.24);n=max(1,math.ceil(rise/.12*L/(L-2*flat)),math.ceil(L/.30))
 for j in range(n):
  d=L*j/n;t=max(0,min(1,(d-flat)/(L-2*flat)));outdoor.append((a[0]+(b[0]-a[0])*j/n,height-rise*t,a[1]+(b[1]-a[1])*j/n))
 if i>0:landing_centres.append((a[0],height,a[1]))
outdoor.append((outdoor_plan[-1][0],T.lower,outdoor_plan[-1][1]))

bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;bpy.context.view_layer.update()
def fingerprint(o):
 h=hashlib.sha256();h.update(str(tuple(tuple(r) for r in o.matrix_world)).encode())
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(str(tuple(p.vertices)).encode())
 return h.hexdigest()
changed_prefix=('photo_stone_slide','slide_gallery_','walk-floor_slide_side_stairs','walk-floor_slide_landing')
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and not o.name.startswith(changed_prefix) and o.name not in ('estimated_hill','mapped_park_lawn_shore_v75')}
removed=[]
for o in list(scene.objects):
 if o.name.startswith(changed_prefix):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
w['solids']=[s for s in w['solids'] if not s['name'].startswith(('walk-floor_slide','stone_slide_safety_boundary','slide_gallery_outer_guard'))]
g=MuseumGeometry(scene,(0,0),0)
class Batch:
 def __init__(self):self.parts={};self.solids=[]
 def mesh(self,name,verts,faces,color):
  vs,fs=self.parts.setdefault((name,color),([],[]));n=len(vs);vs.extend(verts);fs.extend(tuple(n+j for j in f) for f in faces)
 def box(self,name,p,size,color,angle=0,collision=False,floor=False):
  x,y,z=p;ww,hh,dd=size;c,s=math.cos(angle),math.sin(angle)
  pp=[(x+u*c-v*s,z+u*s+v*c) for u,v in [(-ww/2,-dd/2),(ww/2,-dd/2),(ww/2,dd/2),(-ww/2,dd/2)]]
  self.mesh(name,[(xx,yy,zz) for yy in (y-hh/2,y+hh/2) for xx,zz in pp],[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],color)
  if collision or floor:self.solids.append(dict(name=name,kind='building',position=[0,y-hh/2,0],size=list(size),footprint=pp,color=color,collision=collision))
 def tube(self,name,a,b,r,color,n=8):
  p,q=Vector(a),Vector(b);axis=(q-p).normalized();u=axis.cross(Vector((0,1,0)))
  if u.length<.001:u=axis.cross(Vector((1,0,0)))
  u.normalize();v=axis.cross(u).normalized()
  self.mesh(name,[tuple(c+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for c in (p,q) for i in range(n)], [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],color)
 def guard(self,name,a,b,width=.1,height=1.05):
  dx,dz=b[0]-a[0],b[2]-a[2];L=math.hypot(dx,dz)
  # Collision proxy is independent of the narrow visible horizontal rails.
  c,s=dx/L,dz/L;pp=[(x+u*(-s),z+u*c) for x,z,u in [(a[0],a[2],-width/2),(b[0],b[2],-width/2),(b[0],b[2],width/2),(a[0],a[2],width/2)]]
  self.solids.append(dict(name=name,kind='building',position=[0,min(a[1],b[1]),0],size=[L,height+abs(a[1]-b[1]),width],footprint=pp,color='#795c42',collision=True))
 def finish(self):
  for (name,color),(verts,faces) in self.parts.items():
   ob=g.mesh(name,verts,faces,color);ob['reference_revision']='bitgaram-access-v101';ob['surveyed']=False
  return len(self.parts)
B=Batch();wood='#936947';darkwood='#594734';metal='#aeb6b3';cream='#dbded7'
def floors(name,route,width):
 for a,b in zip(route,route[1:]):
  dx,dz=b[0]-a[0],b[2]-a[2];L=math.hypot(dx,dz);h=(a[1]+b[1])/2
  B.box(name,((a[0]+b[0])/2,h-.065,(a[2]+b[2])/2),(L+.025,.13,width),wood,math.atan2(dz,dx),floor=True)
  # Real metal stair noses visible in the 2025 ground-level photograph.
  if abs(a[1]-b[1])>.01:
   B.box(name.replace('walk-floor','access101')+'_nosing',(a[0],h+.004,a[2]),(.045,.008,width-.04),metal,math.atan2(dz,dx))
floors('walk-floor_slide_side_stairs',stairs,1.36);floors('walk-floor_outdoor_timber_stairs',outdoor,1.65)
for x,y,z in landing_centres:B.box('walk-floor_access101_turn_landings',(x,y-.065,z),(2.05,.13,2.05),wood,floor=True)
# Explicit same-height connectors keep both revised paths linked to public
# summit / exhibition roof circulation. Their exact slab edges are estimated.
connectors={
 'upper_gallery':[(0,T.upper,19),(stairs[0][0],T.upper,stairs[0][2])],
 'upper_outdoor':[(5,T.upper,19),outdoor[0]],
 'lower_gallery':[stairs[-1],(stairs[-1][0],T.lower,111),(5,T.lower,111),(16,T.lower,108)],
 'lower_outdoor':[outdoor[-1],(outdoor[-1][0],T.lower,111),(5,T.lower,111)]}
for name,route in connectors.items():floors('walk-floor_access101_'+name,route,2.0)
for name,route,width in [('gallery',stairs,1.36),('outdoor',outdoor,1.65)]:
 last=-100.;distance=0
 for i,p in enumerate(route):
  if i:distance+=math.dist(p,route[i-1])
  if distance-last<1.55 and i!=len(route)-1:continue
  last=distance;a,b=route[max(0,i-1)],route[min(len(route)-1,i+1)];dx,dz=b[0]-a[0],b[2]-a[2];L=math.hypot(dx,dz);sx,sz=dz/L,-dx/L
  if name=='outdoor' and min(math.hypot(p[0]-a[0],p[2]-a[2]) for a in landing_centres)<1.45:continue
  for side in ([-1,1] if name=='outdoor' else [-1]):
   x,z=p[0]+sx*side*(width/2+.05),p[2]+sz*side*(width/2+.05)
   B.box('access101_'+name+'_guard_posts',(x,p[1]+.55,z),(.13,1.1,.13),wood)
   B.box('access101_'+name+'_post_caps',(x,p[1]+1.11,z),(.17,.045,.17),metal)
  if i%2==0:
   ground=T.raw_ground(p[0],p[2]);lo=min(ground,p[1]-.2)
   B.box('access101_'+name+'_deck_piers',(p[0],(lo+p[1]-.13)/2,p[2]),(.18,max(.12,p[1]-.13-lo),.18),darkwood)
 for side in ([-1,1] if name=='outdoor' else [-1]):
  edge=offset_route(route,side*(width/2+.05))
  for a,b in zip(edge,edge[1:]):
   if name=='outdoor' and min(math.hypot((a[0]+b[0])/2-p[0],(a[2]+b[2])/2-p[2]) for p in landing_centres)<1.65:continue
   for h in (.30,.65,1.02):B.tube('access101_'+name+'_horizontal_rails',(a[0],a[1]+h,a[2]),(b[0],b[1]+h,b[2]),.043,wood,n=4)
   B.guard('access101_'+name+'_guard',a,b)
# Granite U-trough. Keep procedural original stone material rather than a photo.
section=[(-.53,.48),(-.41,.48),(-.35,.20),(-.24,.07),(0,0),(.24,.07),(.35,.20),(.41,.48),(.53,.48),(.53,-.13),(-.53,-.13)]
vv=[];ff=[]
for i,(x,y,z) in enumerate(slide):
 a,b=slide[max(0,i-1)],slide[min(len(slide)-1,i+1)];dx,dz=b[0]-a[0],b[2]-a[2];L=math.hypot(dx,dz)
 vv.extend((x+dz/L*u,y+h,z-dx/L*u) for u,h in section)
for i in range(len(slide)-1):
 for j in range(len(section)):ff.append((i*11+j,i*11+(j+1)%11,(i+1)*11+(j+1)%11,(i+1)*11+j))
B.mesh('photo_stone_slide_U_trough',vv,ff,'#737b79')
for a,b in zip(slide,slide[1:]):B.guard('stone_slide_safety_boundary',a,b,1.07,.70)
# Squared laminated timber arch ribs + pale translucent roof, turquoise lower
# panels and internal handrail match the photographed gallery structure.
centres=offset_route(slide,-.55);arc_width=1.76;interval=2.3;distance=0;last=-100;rib_indices=[]
for i,p in enumerate(centres):
 if i:distance+=math.dist(p,centres[i-1])
 if distance-last<interval and i!=len(centres)-1:continue
 last=distance;rib_indices.append(i)
def arc(i,j):
 x,y,z=centres[i];a,b=centres[max(0,i-1)],centres[min(len(centres)-1,i+1)];dx,dz=b[0]-a[0],b[2]-a[2];L=math.hypot(dx,dz);theta=j*math.pi/20
 u=arc_width*math.cos(theta);return (x+dz/L*u,y+.65+2.3*math.sin(theta),z-dx/L*u)
for i in rib_indices:
 for j in range(20):B.tube('slide_gallery_timber_arch',arc(i,j),arc(i,j+1),.09,darkwood,n=4)
 for j in (0,20):
  p=arc(i,j);B.box('slide_gallery_post',(p[0],p[1]-.33,p[2]),(.15,.66,.15),darkwood)
for i,k in zip(rib_indices,rib_indices[1:]):
 for j in (3,6,10,14,17):B.tube('slide_gallery_longitudinal_slats',arc(i,j),arc(k,j),.055,wood,n=4)
 # Upper translucent cover shows as a narrow pale ribbon from satellite.
 for j in range(3,17):B.mesh('access101_gallery_roof',[arc(i,j),arc(i,j+1),arc(k,j+1),arc(k,j)],[(0,1,2,3)],'#c1d5d3')
 for side in (-1,1):
  aa,bb=offset_route([centres[i],centres[k]],side*arc_width)
  B.mesh('slide_gallery_blue_side',[(aa[0],aa[1]+.18,aa[2]),(aa[0],aa[1]+.94,aa[2]),(bb[0],bb[1]+.94,bb[2]),(bb[0],bb[1]+.18,bb[2])],[(0,1,2,3)],'#81b6bc')
# Separate slide / stair handrail, not a bar across the walking lane.
hand=offset_route(slide,-.63)
for a,b in zip(hand,hand[1:]):B.tube('access101_gallery_inner_handrail',(a[0],a[1]+.86,a[2]),(b[0],b[1]+.86,b[2]),.025,metal)
# Oval white passenger shelters are visible at both terminals in the aerial
# reference. Dimensions and support placement are interpreted around the
# existing platform/cabin envelope; keep the boarding path unobstructed.
for label,x,z,h,rx,rz in [('upper',10.1,14,T.upper,3.0,3.8),('lower',13,106.5,T.lower,3.3,4.8)]:
 n=48;vv=[(x+rx*math.cos(i*math.tau/n),h+yy,z+rz*math.sin(i*math.tau/n)) for yy in (3.1,3.28) for i in range(n)]
 ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 B.mesh('access101_'+label+'_station_oval_canopy',vv,ff,cream)
 for side in (-1,1):
  B.box('access101_'+label+'_station_posts',(x+side*(rx-.3),h+1.55,z+rz*(.95 if label=='lower' else .65)),(.13,3.1,.13),metal,collision=True)
 B.box('access101_'+label+'_platform_edge',(x+1.55,h+.006,z),(.18,.012,4.7),'#d7b858')
# Clear only earlier inferred trees occupying newly evidenced facility routes.
all_routes=[slide,outdoor,*connectors.values()]
def nearest(x,z,route):
 best=(1e9,0)
 for a,b in zip(route,route[1:]):
  dx,dz=b[0]-a[0],b[2]-a[2];t=max(0,min(1,((x-a[0])*dx+(z-a[2])*dz)/(dx*dx+dz*dz or 1)))
  d=math.hypot(x-a[0]-t*dx,z-a[2]-t*dz)
  if d<best[0]:best=(d,a[1]+t*(b[1]-a[1]))
 return best
roots=[]
for o in list(scene.objects):
 if o.get('vegetation_lod')!='near':continue
 points=[o.matrix_world@Vector(p) for p in o.bound_box];x=o.location.x;z=-o.location.y
 d,h=nearest(x,z,slide);radius=max(math.hypot(p.x-x,-p.y-z) for p in points)
 penetrates_gallery=d<radius+2.1 and max(p.z for p in points)>h and min(p.z for p in points)<h+3.2
 if penetrates_gallery or min(nearest(x,z,r)[0] for r in all_routes)<2.6:roots.append((x,z,o.get('tree_source_trunk')))
for x,z,trunk in roots:
 for o in list(scene.objects):
  if o.name==trunk or o.get('tree_source_trunk')==trunk:
   protected.pop(o.name,None);removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
w['solids']=[s for s in w['solids'] if not (s['name'] in ('tree_trunk','woodland_trunk') and any(math.hypot(s['position'][0]-x,s['position'][2]-z)<.15 for x,z,_ in roots))]
# Lower local ground beneath new floors; mesh and floor colliders are exported
# together. No interpretation of a new regional DEM is introduced here.
for name in ('estimated_hill','mapped_park_lawn_shore_v75'):
 ob=bpy.data.objects.get(name)
 if not ob:continue
 for v in ob.data.vertices:
  p=ob.matrix_world@v.co
  if -46<p.x<20 and 12<-p.y<115:
   ds=[nearest(p.x,-p.y,r) for r in all_routes];d,h=min(ds)
   if d<2.8:
    weight=1-T.smooth((d-1.6)/1.2);p.z-=max(0,p.z-(h-.20))*weight;v.co=ob.matrix_world.inverted()@p
 ob.data.update()
count=B.finish()
stone=bpy.data.objects['photo_stone_slide_U_trough'];oldmat=bpy.data.materials.get('Stone_slide_polished_granite')
if oldmat:stone.data.materials.clear();stone.data.materials.append(oldmat)
roof=bpy.data.objects['access101_gallery_roof'];mat=roof.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.72;bs.inputs['Roughness'].default_value=.44;mat.surface_render_method='DITHERED';mat.use_backface_culling=False
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith('slide_gallery_blue_side'):o.data.materials[0].use_backface_culling=False
w['solids'].extend(B.solids);w['bounds'][0]=min(w['bounds'][0],min(p[0] for p in slide)-5)
w['arrivals']['slide']=dict(x=stairs[-1][0],z=stairs[-1][2],height=T.lower,yaw=0)
w['arrivals']['outdoor-stairs']=dict(x=outdoor[-1][0],z=outdoor[-1][2],height=T.lower,yaw=0)
w['revision']='bitgaram-access-v101';w['navigationFromBlend']=str(TARGET.relative_to(R))
w['source']+=' · 시설 평면 참고: Esri World Imagery / Vantor / Earthstar Geographics / GIS User Community (2023 영상)'
w['accessReference']=dict(revision='v101',profiles='knowledge/sources/bitgaram/access-v101/navigation-profiles.json',satellite='Esri World Imagery / Vantor WV02, 2023-04-09; metadata source resolution 0.5m, accuracy 5m; accessed 2026-10-05',surveyed=False)
w['monorail']['modelUrl']='/models/bitgaram-monorail.glb.gz?v=bitgaram-access-v101'
w['limitations'].append('위성영상의 미끄럼틀 평면과 현장 사진의 구조를 참고. 가려진 계단 연결·치수·수직 높이는 추정이며 100% 실측 재현이 아닙니다.')
assert all(n in bpy.data.objects and fingerprint(bpy.data.objects[n])==h for n,h in protected.items())
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
stage=O/'bitgaram-park.glb';bpy.ops.export_scene.gltf(filepath=str(stage),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,use_visible=False,use_renderable=False,export_animations=False)
raw=stage.read_bytes();compressed=gzip.compress(raw,9,mtime=0);assert len(compressed)<16*1024*1024
stage.with_suffix('.glb.gz').write_bytes(compressed)
shutil.copyfile(stage,R/'public/models/bitgaram-park.glb');shutil.copyfile(stage.with_suffix('.glb.gz'),R/'public/models/bitgaram-park.glb.gz')
(R/'public/bitgaram-park-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf8')
profiles=json.loads((R/'knowledge/sources/bitgaram/terrain-v89/navigation-profiles.json').read_text());profiles.update(slide_route=slide,stairs_route=stairs,outdoor_route=outdoor,connectors=connectors)
(K/'navigation-profiles.json').write_text(json.dumps(profiles,ensure_ascii=False),encoding='utf8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report=dict(source=str(SOURCE.relative_to(R)),sourceSha256=source_hash,sourceUnchanged=True,output=str(TARGET.relative_to(R)),protectedMeshes=len(protected),removedInferredTreeRoots=len(roots),addedMeshGroups=count,gzipBytes=len(compressed),modelSha256=hashlib.sha256(raw).hexdigest(),slidePlanLengthMetres=sd[-1],slide3dLengthMetres=sum(math.dist(a,b) for a,b in zip(slide,slide[1:])),slideTracePixels=slide_pixels,outdoorTracePixels=outdoor_pixels,satelliteExtent=extent,coordinateOrigin=T.origin,terrainDatumMetres=T.datum,upperModelHeight=T.upper,lowerModelHeight=T.lower,surveyed=False,maxGalleryStep=max(abs(a[1]-b[1]) for a,b in zip(stairs,stairs[1:])),maxOutdoorStep=max(abs(a[1]-b[1]) for a,b in zip(outdoor,outdoor[1:])))
(K/'build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('ACCESS_V101',json.dumps(report),flush=True)
