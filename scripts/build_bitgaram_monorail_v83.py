"""Repair the photo-informed monorail and export an independent operable cabin."""
import bpy, json, math, sys, gzip, hashlib, struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
O=R/'outputs/monorail-v83';O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v75/bitgaram-shore-v75.blend'
target=O/'bitgaram-park-monorail-v83.blend';cabtarget=O/'bitgaram-monorail-cab-v83.blend'
if target.exists() or cabtarget.exists():raise RuntimeError('Existing artist files preserved')
sha=hashlib.sha256(source.read_bytes()).hexdigest()
w=json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))
(O/'world-before.json').write_text(json.dumps(w,ensure_ascii=False),encoding='utf8')
ref=json.loads((R/'knowledge/sources/bitgaram/access-v69.json').read_text(encoding='utf8'))
# Keep mapped x/z, align passenger floor with the existing two platform levels.
route=[[x,y-.95,z] for x,y,z in reversed(ref['rail_route'])]
def fingerprint(o):
 h=hashlib.sha256();h.update(str(tuple(tuple(r) for r in o.matrix_world)).encode())
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(str(tuple(p.vertices)).encode())
 return h.hexdigest()
def export(path):
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,use_visible=False,use_renderable=False,export_animations=False)
 raw=path.read_bytes();path.with_suffix('.glb.gz').write_bytes(gzip.compress(raw,9,mtime=0));return len(raw)
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update();scene=bpy.context.scene
changed_prefix=('photo_monorail_cab_','monorail_roof_vent','mapped_monorail_','monorail_running_strip','monorail_support')
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and not o.name.startswith(changed_prefix)}
removed=[]
for o in list(scene.objects):
 if o.name.startswith(('photo_monorail_cab_','monorail_roof_vent','mapped_monorail_','monorail_running_strip')):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 elif o.type=='MESH' and o.name.startswith('monorail_support') and not o.name.startswith('monorail_support_foot'):
  o.data=o.data.copy();lo=min(v.co.z for v in o.data.vertices);hi=max(v.co.z for v in o.data.vertices)
  for v in o.data.vertices:v.co.z=lo+(v.co.z-lo)*max(.1,hi-lo-.95)/max(.1,hi-lo)
g=MuseumGeometry(scene,(0,0),0)
for i,(a,b) in enumerate(zip(route,route[1:])):
 dx,dz=b[0]-a[0],b[2]-a[2];length=math.hypot(dx,dz);sx,sz=dz/length,-dx/length
 verts=[(p[0]+sx*u,p[1]+h,p[2]+sz*u) for p in (a,b) for u,h in [(-.2,-.16),(.2,-.16),(.2,.16),(-.2,.16)]]
 g.mesh('mapped_monorail_508048300_beam',verts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'#6e5546')
 for side in [-1,1]:g.tube('monorail_running_strip',(a[0]+sx*side*.17,a[1]+.165,a[2]+sz*side*.17),(b[0]+sx*side*.17,b[1]+.165,b[2]+sz*side*.17),.018,'#a2a8a5',n=6)
 if i%2==0:g.box('monorail_rack_teeth',a[0],a[1]-.19,a[2],.24,.045,.07,'#6b6155',record=False)
for s in w['solids']:
 if s['name'].startswith('monorail_guideway_boundary'):s['position'][1]-=.95
w['solids']=[s for s in w['solids'] if not s['name'].startswith('photo_monorail_cab_')]
stations=[dict(id='lower',name='전시동 하부 승강장',distance=0,arrival=[16,108],height=6.22),dict(id='upper',name='전망대 상부 승강장',distance=sum(math.dist(a,b) for a,b in zip(route,route[1:])),arrival=[12,16],height=16)]
w['monorail']=dict(modelUrl='/models/bitgaram-monorail.glb.gz?v=monorail-v83',route=route,stations=stations,speed=3,acceleration=.65,floorOffset=.35,initialStation='upper',estimated='Mapped plan preserved; height, dimensions and 3 m/s experience speed estimated')
w.setdefault('arrivals',{}).update({'monorail-lower':dict(x=16,z=108,yaw=.4,height=6.22),'monorail-upper':dict(x=12,z=16,yaw=.5,height=16)})
w['places']=[p for p in w['places'] if p['id']!='upper-station']+[dict(id='upper-station',name='모노레일 상부 승강장',description='전시동까지 모노레일을 타고 내려갈 수 있습니다.',position=[12,16],radius=5,arrival=[12,16],arrivalHeight=16)]
for p in w['places']:
 if p['id']=='lower-station':p['description']='모노레일을 호출해 전망대까지 올라갈 수 있습니다.'
assert all(fingerprint(bpy.data.objects[n])==h for n,h in protected.items())
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
parkbytes=export(R/'public/models/bitgaram-park.glb')
(R/'public/bitgaram-park-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf8')
# New cabin, local origin on the beam. Hollow glazing and underbody straddle it.
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0)
def box(n,x,y,z,w,h,d,c):return g.box(n,x,y,z,w,h,d,c,record=False)
white='#e4e7e2';dark='#253b3d';orange='#db8239';steel='#879491'
glass=g.mat('#8eafac');bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.22;bs.inputs['Roughness'].default_value=.16;glass.diffuse_color=(.46,.65,.62,.22);glass.surface_render_method='DITHERED';glass.use_backface_culling=False
box('photo_monorail_cab_body',0,.31,0,2.14,.08,4.1,white)
box('cab_floor',0,.36,0,2.02,.025,3.96,'#7f786b')
for side in [-1,1]:
 box('cab_lower_cheek',side*.8,.06,0,.5,.43,3.9,white)
 box('cab_orange_sill',side*1.02,.64,0,.095,.49,4,orange)
 box('cab_white_lower_sill',side*1.04,.46,0,.08,.09,4,white)
 box('cab_window_header',side*1.02,2.50,0,.13,.13,4.05,white)
 for z in [-1.91,1.91]:box('cab_corner_pillar',side*1.01,1.65,z,.10,1.75,.12,dark)
 # Two side panes; boarding side has two sliding glazed door leaves in its centre.
 for z in [-1.33,1.33]:
  box('cab_side_glass',side*1.04,1.66,z,.012,1.47,1.02,'#8eafac')
  box('cab_side_mullion',side*1.04,1.63,z/1.33*.78,.055,1.69,.055,dark)
 if side<0:box('cab_side_glass',side*1.04,1.67,0,.012,1.47,1.43,'#8eafac')
 else:
  for z,label in [(-.37,'left'),(.37,'right')]:
   parent=bpy.data.objects.new('monorail_door_'+label,None);scene.collection.objects.link(parent);parent['authored_dynamic']=True
   for o in [box('door_glass',1.055,1.65,z,.025,1.5,.69,'#8eafac'),box('door_bottom',1.055,.62,z,.055,.5,.72,orange),box('door_stile',1.07,1.52,z+.34,.04,2,.04,dark),box('door_handle',1.09,1.40,z+.22,.05,.29,.04,steel)]:o.parent=parent
 for z in [-1.2,1.2]:
  box('cab_seat',side*.73,.75,z,.39,.12,.85,'#567879');box('cab_seat_back',side*.94,1.08,z,.10,.57,.85,'#567879')
 for z in [-1.22,1.22]:
  g.tube('cab_grab_pole',(side*.53,.4,z),(side*.53,2.4,z),.022,steel,n=10)
for end in [-1,1]:
 # Slightly raked end windows and a real central opening around the beam.
 z=end*2.025
 box('cab_end_glass',0,1.66,z,1.89,1.48,.016,'#8eafac')
 box('cab_end_window_lower_frame',0,.9,z,2.08,.085,.09,dark)
 for side in [-1,1]:box('cab_end_bogie_cheek',side*.78,.21,z,.52,.6,.10,white)
 box('cab_end_lower_panel',0,.66,z,2.09,.46,.10,white)
 for side in [-1,1]:box('cab_marker_light',side*.73,.61,z+end*.06,.095,.06,.025,'#fff1c3')
box('cab_roof',0,2.59,0,2.22,.18,4.24,white)
box('cab_ceiling',0,2.48,0,2.04,.035,3.92,'#d2d5cc')
box('cab_roof_aircon',0,2.82,.12,1.10,.32,1.25,'#bcc7c3')
for i in range(16):box('cab_hvac_vent',-.45+i*.06,2.81,-.52,.024,.22,.012,'#5c6a67')
for z in [-1.2,1.2]:
 box('cab_bogie_frame',0,.05,z,.7,.11,.7,'#3f4845')
 for side in [-1,1]:
  g.tube('cab_running_wheel',(side*.17,.25,z-.12),(side*.17,.25,z+.12),.08,'#242c29',n=16)
  g.tube('cab_guide_wheel',(side*.29,-.02,z-.10),(side*.29,-.02,z+.10),.095,'#303936',n=16)
for z in [-.8,.8]:box('cab_ceiling_light',0,2.445,z,.35,.018,.15,'#fff5cc')
label=g.label('빛가람 모노레일',0,.67,-2.085,1.6,.16,color='#344643')
for o in scene.objects:
 if o.type=='MESH' and o.name.startswith(('cab_roof','cab_lower_cheek','photo_monorail_cab_body','cab_end_lower_panel')):
  mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=.045;mod.segments=3
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(cabtarget))
cabbytes=export(R/'public/models/bitgaram-monorail.glb')
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
report=dict(source=str(source.relative_to(R)),sourceSha256=sha,sourceUnchanged=True,protectedObjects=len(protected),nonMonorailGeometryUnchanged=True,parkEditable=str(target.relative_to(R)),cabEditable=str(cabtarget.relative_to(R)),removedStaticCabObjects=len(removed),routeLength=stations[1]['distance'],parkBytes=parkbytes,cabBytes=cabbytes,references=['https://monorail.co.kr/승객용-모노레일-설치사진/view/6000','https://nanika123.tistory.com/entry/아이와-함께-가볼만-한곳-빛가람-호수공원-전망대-모노레일-타기'],estimated=['height correction to match authored platforms','cabin dimensions and interior fittings','experience operating speed and acceleration'])
(R/'knowledge/sources/bitgaram/monorail-v83.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('MONORAIL_V83',json.dumps(report,ensure_ascii=False),flush=True)
