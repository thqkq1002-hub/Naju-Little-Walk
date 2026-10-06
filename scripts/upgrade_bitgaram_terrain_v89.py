"""A new Blender revision: native GLO-30 relief plus synchronized navigation.
The v83 artist source and other destination models remain untouched.
"""
import bpy,json,math,sys,hashlib,gzip,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from bitgaram_terrain_v89 import Terrain
from museum_geometry import MuseumGeometry
O=R/'outputs/terrain-v89';O.mkdir(parents=True,exist_ok=True)
SOURCE=R/'outputs/monorail-v83/bitgaram-park-monorail-v83.blend'
suffix='v89d' if '--shore-refinement' in sys.argv else 'v89c' if '--material-repair' in sys.argv else 'v89b' if '--clearance-repair' in sys.argv else 'v89'
TARGET=O/('bitgaram-park-glo30-terrain-'+suffix+'.blend')
if TARGET.exists():raise RuntimeError('Existing artist revision preserved; choose a new output')
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
source_world=O/'world-before.json'
w=json.loads((source_world if source_world.exists() else R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))
if not source_world.exists():source_world.write_text(json.dumps(w,ensure_ascii=False),encoding='utf8')
T=Terrain(next(s['footprint'] for s in w['solids'] if s['name']=='photo_exhibition_shell'))
du,dl=T.upper-16,T.lower-6.22
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;bpy.context.view_layer.update()
g=MuseumGeometry(scene,(0,0),0);changed=[];handled=set()
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [min(v.x for v in p),max(v.x for v in p),min(v.y for v in p),max(v.y for v in p),min(v.z for v in p),max(v.z for v in p)]
def move(o,delta):
 if abs(delta)>1e-6:o.location.z+=delta;changed.append(o.name)
 handled.add(o.name)
def deform(o,fn):
 assert o.data.users==1, 'Do not deform a shared prototype'
 for v in o.data.vertices:
  p=o.matrix_world@v.co;p.z=fn(p.x,-p.y,p.z);v.co=o.matrix_world.inverted()@p
 o.data.update();changed.append(o.name);handled.add(o.name)
def matches(name,prefix):return name==prefix or name.startswith(prefix+'.')
def solid_center(s):
 if s.get('footprint'):
  p=s['footprint'];return sum(v[0] for v in p)/len(p),sum(v[1] for v in p)/len(p)
 return s['position'][0],s['position'][2]
def write_json(path,value,compact=False):
 text=json.dumps(value,ensure_ascii=False,**({'separators':(',',':')} if compact else {'indent':2}))+'\n'
 temp=path.with_name(path.name+'.writing-v89');temp.write_text(text,encoding='utf8');temp.replace(path)
roots={}
for o in scene.objects:
 if o.type=='MESH' and any(matches(o.name,p) for p in ('tree_trunk','woodland_trunk','shore_finish_trunk','surrounding_tree_trunk')):
  b=bounds(o);x,z=(b[0]+b[1])/2,-(b[2]+b[3])/2;roots[o.name]=dict(x=x,z=z,old=b[4],delta=T.ground(x,z)-b[4]);move(o,roots[o.name]['delta'])
for o in scene.objects:
 n=o.get('tree_source_trunk')
 if n in roots:move(o,roots[n]['delta'])
# Ground-surface meshes all use the same field, including the adjoining lawn.
ground_names=('estimated_hill','mapped_park_lawn_shore_v75')
for name in ground_names:
 o=bpy.data.objects.get(name)
 if not o:continue
 if name=='estimated_hill':
  N=201;verts=[(x,-z,T.ground(x,z)+.015) for z in [-150+j*1.5 for j in range(N)] for x in [-150+i*1.5 for i in range(N)]]
  faces=[]
  for j in range(N-1):
   for i in range(N-1):
    a=j*N+i;faces.extend([(a,a+N+1,a+1),(a,a+N,a+N+1)])
  old=o.data;mesh=bpy.data.meshes.new('GLO30_bilinear_terrain_1p5m_display_grid');mesh.from_pydata(verts,[],faces);mesh.update()
  for m in old.materials:mesh.materials.append(m)
  # Retain the established forest / lawn material partition by nearest old face.
  from mathutils.kdtree import KDTree
  kd=KDTree(len(old.polygons))
  for i,p in enumerate(old.polygons):kd.insert((p.center.x,p.center.y,0),i)
  kd.balance()
  for p in mesh.polygons:p.material_index=old.polygons[kd.find((p.center.x,p.center.y,0))[1]].material_index;p.use_smooth=True
  # The source shader reads Color. A new mesh without this attribute renders
  # black; carry the original colour field in plan, independent of elevation.
  old_color=old.color_attributes.get('Color');assert old_color and old_color.domain=='CORNER'
  colors=[[0.,0.,0.,0.,0] for _ in old.vertices]
  for loop in old.loops:
   c=old_color.data[loop.index].color;r=colors[loop.vertex_index]
   for k in range(4):r[k]+=c[k]
   r[4]+=1
  color_kd=KDTree(len(old.vertices))
  for i,v in enumerate(old.vertices):color_kd.insert((v.co.x,v.co.y,0),i)
  color_kd.balance();col=mesh.color_attributes.new(name='Color',type='BYTE_COLOR',domain='POINT')
  for v in mesh.vertices:
   _,i,_=color_kd.find((v.co.x,v.co.y,0));r=colors[i];col.data[v.index].color=tuple(r[k]/r[4] for k in range(4))
  mesh.color_attributes.active_color=col
  uv=mesh.uv_layers.new(name='Metre_ground_UV')
  for loop in mesh.loops:
   v=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x*.15,-v.y*.15)
  o.data=mesh;o['terrain_dataset']='Copernicus GLO-30 DSM (30m nominal)';o['display_interpolation_metres']=1.5;o['surveyed_bare_earth']=False
  changed.append(o.name);handled.add(o.name)
 else:
  prepared=json.loads((O/'dense-shore-ground.json').read_text(encoding='utf8'))
  old=o.data;mesh=bpy.data.meshes.new('Mapped_lawn_DSM_refined_4m')
  mesh.from_pydata([(x,-z,y) for x,y,z in prepared['vertices']],[],prepared['faces']);mesh.update()
  for m in old.materials:mesh.materials.append(m)
  for p,mi in zip(mesh.polygons,prepared['material_indices']):p.material_index=mi;p.use_smooth=True
  uv=mesh.uv_layers.new(name='UVMap')
  for loop in mesh.loops:
   v=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x/3.2,v.y/3.2)
  o.data=mesh;changed.append(o.name);handled.add(o.name)
# Existing mapped paths were draped over the old Gaussian. Replace that relief.
def oldhill(x,z):return min(16*math.exp(-((x/100)**2+(z/105)**2)*1.6),15.75)
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith(('surrounding_mapped_paths','surrounding_recreation','surrounding_parking')):
  deform(o,lambda x,z,y:T.ground(x,z)+y-(oldhill(x,z) if y>.2 else 0))
# Each existing floor box keeps its exact plan; mesh and collision use one level.
floor_specs=[('walk-floor_mapped_forest_549492174',T.forest),('walk-floor_slide_side_stairs',T.stairs)]
floor_levels={}
for name,route in floor_specs:
 solids=[s for s in w['solids'] if s['name']==name];o=bpy.data.objects[name]
 assert len(solids)==len(route)-1 and len(o.data.vertices)==8*len(solids)
 from mathutils.kdtree import KDTree
 kd=KDTree(len(solids));deltas=[]
 for i,(s,a,b) in enumerate(zip(solids,route,route[1:])):
  cx,cz=solid_center(s);kd.insert((cx,cz,0),i)
  assert math.hypot(cx-(a[0]+b[0])/2,cz-(a[2]+b[2])/2)<.01
  level=(a[1]+b[1])/2;oldtop=s['position'][1]+s['size'][1]*(1 if s['kind']=='building' else .5)
  delta=level-oldtop;s['position'][1]+=delta;deltas.append(delta)
 kd.balance();seen=set();verts=list(o.data.vertices)
 for k in range(0,len(verts),8):
  block=verts[k:k+8];cx=sum(v.co.x for v in block)/8;cz=-sum(v.co.y for v in block)/8
  _,i,d=kd.find((cx,cz,0));assert d<.01 and i not in seen,(name,k,i,d);seen.add(i)
  for v in block:v.co.z+=deltas[i]
 floor_levels[name]=[(a[1]+b[1])/2 for a,b in zip(route,route[1:])]
 changed.append(name);handled.add(name);o.data.update()
# Deform the open granite slide and gallery without moving their mapped plans.
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith(('photo_stone_slide','slide_gallery_')):
  deform(o,lambda x,z,y:y+T.slide_delta(z))
# Preserve the station cabin model; guideway follows sampled relief and remains
# level with each passenger platform at its endpoints.
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith(('mapped_monorail_','monorail_running_strip','monorail_rack_teeth')):
  deform(o,lambda x,z,y:y+T.rail_delta(z))
for name in ('monorail_support','monorail_support_foot'):
 o=bpy.data.objects[name];assert len(o.data.vertices)%8==0
 for k in range(0,len(o.data.vertices),8):
  vs=list(o.data.vertices)[k:k+8];x=sum(v.co.x for v in vs)/8;z=-sum(v.co.y for v in vs)/8
  lo,hi=min(v.co.z for v in vs),max(v.co.z for v in vs)
  rail=T.at_z(T.rail_by_z,z,T.rail_z)[1];ground=min(T.ground(x,z),rail-.8)
  newlo=ground;newhi=ground+.14 if name.endswith('_foot') else rail-.16
  for v in vs:v.co.z=newlo+(v.co.z-lo)/(hi-lo)*(newhi-newlo)
 changed.append(name);handled.add(name);o.data.update()
for o in scene.objects:
 if o.type not in ('MESH','FONT') or o.name in handled:continue
 n=o.name;b=bounds(o);x,z=(b[0]+b[1])/2,-(b[2]+b[3])/2
 if n=='context_ground' or n.startswith('lake_osm_'):continue
 if n.startswith('context_road'):deform(o,lambda xx,zz,y:y+T.ground(xx,zz))
 elif n.startswith('summit_stone_foundation'):
  lo,hi=b[4:6]
  deform(o,lambda xx,zz,y:T.ground(xx,zz)+(T.upper-.15-T.ground(xx,zz))*(y-lo)/(hi-lo))
 elif n.startswith(('photo_exhibition_','context_roof_garden','roof_garden_','walk-floor_lower_station','walk-floor_slide_landing')):move(o,dl)
 elif n.startswith('walk-floor_upper_station'):move(o,du)
 elif n.startswith(('shore_finish_shrub','surrounding_bench')):move(o,T.ground(x,z))
 elif n.startswith('context_building_'):move(o,T.ground(x,z))
 elif math.hypot(x,z)<35:move(o,du)
 elif n.startswith(('bench_','entry_sign','label_')):move(o,T.ground(x,z)-oldhill(x,z))
# Collision heights are changed in the same way as their authored geometry.
for s in w['solids']:
 n=s['name'];x,z=solid_center(s);y=s['position'][1]
 if n in floor_levels:continue
 if n=='summit_stone_base':
  oldbase=y-s['size'][1]/2;newbase=T.ground(x,z);newtop=T.upper-.15
  s['position'][1]=newbase if s['kind']=='building' else (newbase+newtop)/2;s['size'][1]=max(.03,newtop-newbase)
 elif n=='monorail_guideway_boundary':s['position'][1]+=T.rail_delta(z)
 elif n in ('stone_slide_safety_boundary','slide_gallery_outer_guard'):s['position'][1]+=T.slide_delta(z)
 elif n.startswith(('photo_exhibition','context_roof_garden','walk-floor_lower_station','walk-floor_slide_landing')):s['position'][1]+=dl
 elif n.startswith('context_building_'):s['position'][1]+=T.ground(x,z)
 elif not n.startswith(('lake_osm_','context_')):s['position'][1]+=du
for a in [w['spawn'],*w['arrivals'].values()]:
 if abs(a.get('height',0)-16)<.001:a['height']=T.upper
 elif abs(a.get('height',0)-6.22)<.001:a['height']=T.lower
 else:a['height']=T.forest_height(a['x'],a['z'])
for p in w['places']:p['arrivalHeight']=T.lower if p['id']=='lower-station' else T.upper
for p in w['portals']:p['height']=T.upper
for s in w['signs']:
 x,_,z=s['position'];s['position'][1]+=dl if z>90 and z<150 else du if math.hypot(x,z)<35 else T.ground(x,z)-oldhill(x,z)
length=sum(math.dist(a,b) for a,b in zip(T.rail,T.rail[1:]))
w['monorail']['route']=T.rail
for s in w['monorail']['stations']:
 s['height']=T.lower if s['id']=='lower' else T.upper;s['distance']=0 if s['id']=='lower' else length
w['monorail']['estimated']='OSM plan exact; interpreted passenger levels from GLO-30 DSM, sampled slope with endpoint levelling. Platform heights/beam clearances and operating speed are not an as-built survey.'
w['terrain']=dict(revision='terrain-v89',dataset=T.grid['dataset'],nativeResolutionMetres=30,
 verticalReference=T.grid['verticalReference'],modelDatumMetres=T.datum,
 upperSurfaceElevationMetres=T.upper+T.datum,lowerSurfaceElevationMetres=T.lower+T.datum,
 platformDifferenceMetres=T.upper-T.lower,surveyedBareEarth=False,
 sourceUrl=T.grid['sourceUrl'],attribution=T.grid['attribution'],limitations=T.grid['limitations'])
w['limitations']=['30m DSM 보간 지형 · 지면 실측값 아님 · 승강장 수평면·궤도·계단 상세는 추정']
bpy.context.view_layer.update()
# Save the separate editable source before the review lighting/cameras are added.
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(R/'public/models/bitgaram-park.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,use_visible=False,use_renderable=False,export_animations=False)
path=R/'public/models/bitgaram-park.glb';raw=path.read_bytes();path.with_suffix('.glb.gz').write_bytes(gzip.compress(raw,9,mtime=0))
write_json(R/'public/bitgaram-park-world.json',w,compact=True)
npc_path=R/'public/npc-placements.json';npc=json.loads(npc_path.read_text(encoding='utf8'))
npc['placements']['bitgaram-park']['position'][1]=T.upper
npc['placements']['bitgaram-park']['spawn']=w['spawn'].copy()
write_json(npc_path,npc)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report=dict(source=str(SOURCE.relative_to(R)),sourceSha256=source_hash,sourceUnchanged=True,output=str(TARGET.relative_to(R)),
 changedObjects=len(changed),treeRootsMoved=sum(abs(q['delta'])>1e-6 for q in roots.values()),upperModelHeight=T.upper,lowerModelHeight=T.lower,
 elevationDifferenceMetres=T.upper-T.lower,railLengthMetres=length,monorailPlanPreserved=True,
 maxFloorStep={n:max(abs(a-b) for a,b in zip(levels,levels[1:])) for n,levels in floor_levels.items()},
 modelBytes=len(raw),gzipBytes=path.with_suffix('.glb.gz').stat().st_size,modelSha256=hashlib.sha256(raw).hexdigest(),
 sourceResolutionMetres=30,displayGridMetres=1.5,surveyedBareEarth=False,
 limitations=T.grid['limitations'],sourceAttribution=T.grid['attribution'])
(R/'knowledge/sources/bitgaram/terrain-v89/build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
profiles=dict(forest_route=T.forest,stairs_route=T.stairs,slide_route=T.slide,rail_route=T.rail)
(R/'knowledge/sources/bitgaram/terrain-v89/navigation-profiles.json').write_text(json.dumps(profiles,ensure_ascii=False),encoding='utf8')
(O/'root-adjustments.json').write_text(json.dumps(roots),encoding='utf8')
print('TERRAIN_V89',json.dumps(report,ensure_ascii=False),flush=True)
