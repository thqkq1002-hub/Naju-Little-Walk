"""Satellite-guided grove density and photo-informed entrance detailing."""
import bpy,sys,json,math,random,gzip
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum';outblend=O/'naju-arboretum-groves-v7.blend'
if outblend.exists():raise RuntimeError('Existing revision is preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-surface-v6.blend'))
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(926)
E=json.loads((R/'knowledge/sources/arboretum/satellite-export.json').read_text())['extent']
def px(u,v):
 x=E['xmin']+(E['xmax']-E['xmin'])*u/1600;y=E['ymax']-(E['ymax']-E['ymin'])*v/1200
 return ((x/6378137*180/math.pi-126.8256689)*111320*math.cos(math.radians(35.00648)),-(math.atan(math.sinh(y/6378137))*180/math.pi-35.00648)*111320)
def inside(x,z,p):
 hit=False
 for a,b in zip(p,p[1:]+p[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
 return hit
def local(s,t):return (-475+s*.98-t*.2,-50+s*.2+t*.98)
world=json.loads((R/'public/naju-arboretum-world.json').read_text(encoding='utf-8'))
data=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'))
paths=[]
for w in data['ways']:
 if w['tags'].get('highway'):paths.extend(zip(w['points'],w['points'][1:]))
for trace in json.loads((R/'knowledge/sources/arboretum/detail-traces.json').read_text())['traces']:
 if 'walk' in trace['name'] or 'connection' in trace['name']:
  p=[px(*a) for a in trace['pixels']];paths.extend(zip(p,p[1:]))
def clearance(x,z):
 for a,b in paths:
  dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
  if math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)<5:return False
 return True
patches=[[(415,469),(639,527),(594,638),(397,586)],[(671,570),(803,607),(746,754),(624,704)],[(215,622),(375,667),(351,756),(229,737)],[(821,666),(998,710),(968,849),(824,806)],[(865,940),(1058,1002),(989,1092),(820,1078)],[(841,113),(1015,152),(985,249),(812,209)],[(444,184),(626,236),(601,277),(439,249)],[(1320,361),(1511,414),(1480,548),(1360,510)],[(1321,903),(1524,950),(1438,1094),(1289,1034)]]
proto=next(o for o in bpy.data.objects if o.name.startswith('estimated_broadleaf')).copy();proto.data=proto.data.copy()
added=0
for index,pp in enumerate(patches):
 p=[px(*a) for a in pp]
 # Keep land cover inside the original campus outline.
 campus=next(w['points'] for w in data['ways'] if w['id']=='1306096596')
 for o in list(bpy.data.objects):
  if o.name.startswith('estimated_broadleaf') and inside(o.location.x,-o.location.y,p):bpy.data.objects.remove(o,do_unlink=True)
 for attempt in range(175):
  x=rng.uniform(min(a[0] for a in p),max(a[0] for a in p));z=rng.uniform(min(a[1] for a in p),max(a[1] for a in p))
  if not inside(x,z,p) or not inside(x,z,campus) or not clearance(x,z):continue
  if any(s.get('collision') and s.get('footprint') and inside(x,z,s['footprint']) for s in world['solids']):continue
  o=proto.copy();o.data=proto.data;scene.collection.objects.link(o);o.name='satellite_grove_'+str(index);o.location=g.bp(x,0,z)
  k=rng.uniform(.95,1.65);o.scale=(k*rng.uniform(.9,1.2),k*rng.uniform(.9,1.2),k);o.rotation_euler.z=rng.random()*math.tau;added+=1
# The prototype was never linked, but copied tree geometry remains shared.
bpy.data.objects.remove(proto,do_unlink=True)
def box(name,s,t,y,w,h,d,c):
 x,z=local(s,t);return g.box(name,x,y,z,w,h,d,c,rotation=.2013,record=False)
# Gate timber cladding, caps, low flower edging and asphalt marking from the entry photo.
for s,t,w,d,h in [(-1,-9,3,4,3.8),(-1,10,1.1,1,3.4)]:
 box('entry_cap',s,t,h+.08,w+.28,.16,d+.25,'#656259')
 for k in range(int(w/.16)):
  box('entry_vertical_board',s-w/2+k*.16,t-d/2-.04,h/2,.025,h-.1,.04,'#342f29')
for s in range(-4,9):
 for t in [-5.6,7.8]:box('entry_yellow_edge',s,t,.025,.96,.03,.09,'#d4b753')
for t in [-8,9]:
 box('entry_planter',5,t,.16,5,.32,.65,'#9c8164')
 for k in range(20):
  x,z=local(2.6+k*.25,t+rng.uniform(-.2,.2))
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.10,location=g.bp(x,.42,z));o=bpy.context.object;o.name='entry_small_flowers';o.data.materials.append(g.mat(rng.choice(['#e5dcc9','#c08c9e','#75925a'])))
# Rounded shrubs around entrance seen in the field photo, kept out of the path.
for s,t in [(8,-12),(13,-12),(18,-12),(10,13),(15,13)]:
 x,z=local(s,t);bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=g.bp(x,.8,z));o=bpy.context.object;o.name='entry_clipped_shrub';o.scale=(1.2,1.1,.8)
 for p in o.data.polygons:p.use_smooth=True
 o.data.materials.append(g.mat('#426638'))
(R/'knowledge/sources/arboretum/grove-traces.json').write_text(json.dumps(dict(reference='Existing Esri World Imagery export, acquisition date unverified',pixel_polygons=patches,trees_added=added,individual_positions='estimated within visually identified grove polygons'),ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(outblend));out=R/'public/models/naju-arboretum.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
cam=scene.camera;cam.location=g.bp(-590,400,430);cam.rotation_euler=(Vector(g.bp(-230,0,-40))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=38
scene.render.filepath=str(O/'groves-overview.png');bpy.ops.render.render(write_still=True)
print('GROVES COMPLETE',added,out.stat().st_size)
