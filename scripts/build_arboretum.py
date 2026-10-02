"""Naju forest campus: OSM ground plan, photo-informed avenue, estimated planting."""
import bpy,sys,json,math,random,gzip
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/arboretum';OUT.mkdir(exist_ok=True)
target=OUT/'naju-arboretum-base-v2.blend'
if target.exists():raise RuntimeError('Existing Blender revision preserved')
D=json.loads((ROOT/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'));W={w['id']:w for w in D['ways']}
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(916)
def local(s,t):return (-475+s*.98-t*.2,-50+s*.2+t*.98)
def box(n,s,t,y,w,h,d,c,collision=False):
 x,z=local(s,t);return g.box(n,x,y,z,w,h,d,c,collision,rotation=math.atan2(.2,.98))
def line(n,a,b,width=.2,h=.1,c='#bda88a',base=0,collision=False):
 return g.segment(n,local(*a),local(*b),width,h,c,base=base,collision=collision,record=collision)
campus=W['1306096596']['points']
g.polygon('ground_campus_osm',campus,-.3,.3,'#77885a',group='01_OSM_Envelope')
paths=[]
ids=['1258471012','1258471013','1258471015','1258471018','1258471019','1306096595']
for wid in ids:
 pts=W[wid]['points'];width=6 if wid=='1306096595' else 3.8
 for a,b in zip(pts,pts[1:]):
  g.segment('mapped_path_'+wid,a,b,width,.09,'#b5ad99',base=.01,record=False);paths.append((a,b,width))
  # Fine pale shoulders retain the real centerline, without covering garden plots.
for wid in ['1258471017']:
 g.polygon('water_osm_'+wid,W[wid]['points'],.015,.02,'#557c72',True,group='01_OSM_Envelope')
 # Full-depth collision prevents stepping into the pond.
 g.collider('pond_boundary',W[wid]['points'],-2,4)

def proto(kind):
 before=set(bpy.data.objects)
 h=19 if kind=='meta' else 9 if kind=='juniper' else 7
 trunk=g.tube('bark',(0,0,0),(0,h,0),.30 if kind=='meta' else .20,'#745b40',n=12)
 if kind=='meta':
  for j in range(7):
   y=6+j*1.75;r=3.1*(1-j/9)
   for k in range(3):
    a=k*math.tau/3+j*.9
    g.tube('branch',(0,y,0),(r*math.cos(a),y+1,r*math.sin(a)),.055,'#756447',n=5)
 else:r=2
 count=32 if kind=='meta' else 9
 for j in range(count):
  a=j*2.4;y=(6+j*.39) if kind=='meta' else (2+j*.65);spread=2.7*(1-j/(count+5));r=1.25 if kind=='meta' else (1.1 if kind=='juniper' else 1.5)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2 if kind=='meta' else 1,radius=1,location=g.bp(math.cos(a)*spread*.7,y,math.sin(a)*spread*.7))
  o=bpy.context.object;o.scale=(r,r,1.1 if kind=='juniper' else .9);o.data.materials.append(g.mat(rng.choice(['#456644','#567744','#63844b','#729454'])))
  for p in o.data.polygons:p.use_smooth=True
 items=list(set(bpy.data.objects)-before);bpy.ops.object.select_all(action='DESELECT')
 for o in items:o.select_set(True)
 bpy.context.view_layer.objects.active=trunk;bpy.ops.object.join();o=bpy.context.object;o.name='prototype_'+kind
 bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR');return o
prototypes={k:proto(k) for k in ['meta','juniper','broadleaf']};tree_count=0
def tree(s,t,kind='broadleaf',scale=1,collision=False):
 global tree_count
 x,z=local(s,t);o=prototypes[kind].copy();o.data=prototypes[kind].data;scene.collection.objects.link(o)
 o.name='estimated_'+kind;o.location=g.bp(x,0,z);o.scale=(scale,scale,scale);o.rotation_euler.z=rng.random()*math.tau;tree_count+=1
 if collision:g.solids.append(dict(name='tree_trunk',kind='cylinder',position=[x,2,z],size=[.8,4,.8],color='#745b40',collision=True))
for s in range(16,431,7):
 for t in [-5.2,5.2]:tree(s,t,'meta',rng.uniform(.90,1.12),True)
for s in range(48,425,8):
 for t in [-181,-169]:tree(s,t,'juniper',rng.uniform(.95,1.2),True)
# Walkway deck beside the principal avenue, based on on-site photos; board dimensions estimated.
for s in range(20,420,2):
 box('avenue_deck',s,10,.09,1.94,.14,2.2,'#9f8762')
for s in range(30,411,42):
 for t in [-10,14]:
  box('bench_seat',s,t,.52,1.8,.12,.55,'#9e794f',True)
  box('bench_back',s,t+.3,.85,1.8,.5,.08,'#9e794f')
  for ds in [-.65,.65]:box('bench_foot',s+ds,t,.24,.08,.48,.5,'#394b40')
# Air-photo garden blocks: inferred vegetation; mapped paths and pond always stay clear.
def point_in(p,poly):
 x,z=p;inside=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:inside=not inside
 return inside
def nearpath(p):
 for a,b,w in paths:
  dx,dz=b[0]-a[0],b[1]-a[1];u=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dz)/(dx*dx+dz*dz or 1)))
  if math.hypot(p[0]-a[0]-u*dx,p[1]-a[1]-u*dz)<w/2+4:return True
 return False
for i in range(1200):
 s=rng.uniform(35,445);t=rng.uniform(-240,115);p=local(s,t)
 if not point_in(p,campus) or nearpath(p) or abs(t)<17 or -188<t<-163:continue
 if (s<100 and t<0) or (s>255 and t>30) or (110<s<195 and t>25) or s>425:continue
 tree(s,t,'broadleaf' if t>-130 else 'juniper',rng.uniform(.65,1.35))
# Spiral medicinal/ornamental garden visible in aerial photograph.
for rad in [9,15,21,27]:
 for j in range(60):
  a=j*math.tau/60;b=(j+1)*math.tau/60
  if abs(math.sin(a))<.07:continue
  line('estimated_garden_hedge',(155+rad*math.cos(a),70+rad*math.sin(a)),(155+rad*math.cos(b),70+rad*math.sin(b)),1.25,.6,'#476842')
for a in [0,math.pi/2]:
 line('garden_cross',(155-29*math.cos(a),70-29*math.sin(a)),(155+29*math.cos(a),70+29*math.sin(a)),2,.06,'#d0bea0',.1)
for s in [270,305,340]:
 for t in [48,75]:
  # Opaque pale polycarbonate keeps the many greenhouse panes inexpensive.
  box('estimated_greenhouse',s,t,2.4,27,4.8,15,'#c2d2cf',True)
  for ds in range(-12,13,3):box('greenhouse_rib',s+ds,t,4.9,.09,.12,15.3,'#718c87')
  box('greenhouse_ridge',s,t,5.1,27.5,.18,.15,'#738e88')
def building(s,t,w,d,h,name):
 box('estimated_building_'+name,s,t,h/2,w,h,d,'#d4d4c5',True)
 box('roof_'+name,s,t,h+.2,w+1,.4,d+1,'#526c67')
 for ds in range(-int(w/2)+2,int(w/2)-1,4):
  for y in [2.2,5.5]:
   if y<h:box('window_'+name,s+ds,t-d/2-.04,y,2.8,1.9,.08,'#41636b')
building(445,-7,26,48,8,'research')
building(65,-55,34,15,4.5,'visitor')
box('parking',48,-85,.025,58,.04,38,'#979f93')
for s in range(24,76,3):line('parking_line',(s,-101),(s,-96),.08,.02,'#e1dfca',.06)
for t in [-110,120]:
 for s in range(75,365,20):line('plot_edge',(s,t),(s+15,t),.15,.12,'#aab486')
for label,s,t in [('메타세쿼이아길',18,12),('향나무길',48,-163),('나주수목원',2,12)]:
 x,z=local(s,t);box('signboard',s,t,1.55,3,1,.13,'#244e3e');box('signpost',s,t,.6,.14,1.2,.14,'#695742',True)
 g.label(label,x,1.56,z+.09,2.8,.3,color='#eee6cb')
for o in prototypes.values():bpy.data.objects.remove(o,do_unlink=True)
spawnx,spawnz=local(12,0)
places=[]
for ident,title,s,t,desc in [('avenue','메타세쿼이아길',25,0,'큰 나무 아래 곧게 이어지는 길을 걸어보세요.'),('juniper','향나무길',120,-175,'길을 따라 연구원 안쪽으로 산책해 보세요.'),('garden','원형 정원',155,70,'항공사진을 참고한 정원입니다. 세부 식재는 추정했습니다.')]:
 x,z=local(s,t);places.append(dict(id=ident,name=title,description=desc,position=[x,z],radius=40,arrival=[x,z]))
world=dict(title='나주 산책',subtitle='나주수목원 · 기초 재현',source=D['source'],bounds=[-530,160,-330,200],spawn=dict(x=spawnx,z=spawnz,yaw=-math.atan2(.98,-.2)),solids=g.solids,signs=g.signs,places=places,sceneLinks=[dict(label='빛가람으로',target='bitgaram')],lighting=dict(exposure=1.05,ambient=1.6,sun=2.3),limitations=['OSM boundary and path centerlines; photo-informed planting and buildings with estimated dimensions. Base reconstruction, not survey grade.'])
(ROOT/'public/naju-arboretum-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.2;sun.rotation_euler=(.5,-.5,-.65)
scene.world=bpy.data.worlds.new('Forest daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.7,.85,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
bpy.ops.object.camera_add(location=g.bp(-590,400,430));cam=bpy.context.object;cam.rotation_euler=(Vector(g.bp(-230,0,-40))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.clip_end=3000;cam.data.lens=38;scene.camera=cam
scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=32;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=1;scene.render.resolution_x=1300;scene.render.resolution_y=900;scene.render.resolution_percentage=100
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
glb=ROOT/'public/models/naju-arboretum.glb';bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(glb)+'.gz','wb',compresslevel=9) as f:f.write(glb.read_bytes())
scene.render.filepath=str(OUT/'overview.png');bpy.ops.render.render(write_still=True)
cam.location=g.bp(spawnx,1.72,spawnz);tx,tz=local(150,0);cam.rotation_euler=(Vector(g.bp(tx,7,tz))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24
scene.render.filepath=str(OUT/'avenue.png');bpy.ops.render.render(write_still=True)
print('ARBORETUM COMPLETE',tree_count,'trees',len(g.solids),'solids',glb.stat().st_size,'bytes')
