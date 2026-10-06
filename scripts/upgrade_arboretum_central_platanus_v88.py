"""User-selected central avenue Platanus revision; preserve saved v87.

Official references call this a metasequoia avenue. This species portrayal is
the user's explicit interpretation, not a verified field tree inventory.
"""
import ast,bpy,hashlib,json,math,random
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v88';O.mkdir(parents=True,exist_ok=True)
SOURCE=R/'outputs/quality-v87/naju-arboretum-canopy-v87-r4.blend'
TARGET=O/'naju-arboretum-central-platanus-v88.blend'
if TARGET.exists():raise RuntimeError('Existing editable revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
tree=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<PlantMesh>','exec'))
cache={}
def fingerprint(o):
 m=o.data
 if m not in cache:
  v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
  ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
  lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
  cache[m]=v.tobytes()+ids.tobytes()+lengths.tobytes()
 return hashlib.sha256(cache[m]+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
central=[o for o in scene.objects if o.type=='MESH' and o.get('reference_habit')=='meta']
names={o.name for o in central}
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in names}
before_world=(R/'public/naju-arboretum-world.json').read_bytes()
(O/'world-before.json').write_bytes(before_world)
original={(o['vegetation_lod'],int(o['tree_crown_variant'])):o.data for o in central}
leaf_source={}
for o in scene.objects:
 if o.type=='MESH' and o.get('reference_habit')=='broad' and o.get('canopy_form')=='plane':
  leaf_source[o['vegetation_lod'],int(o['tree_crown_variant'])]=o.data

def basal(p,m,height=4.05):
 # Clip the old lower trunk/root faces with interpolated UVs. New forks start
 # above the existing 4m trunk collider, whose coordinates remain unchanged.
 for f in m.polygons:
  if f.material_index!=0:continue
  vertices=[(m.vertices[i].co.copy(),m.uv_layers.active.data[li].uv.copy()) for i,li in zip(f.vertices,f.loop_indices)]
  clipped=[]
  for (a,ua),(b,ub) in zip(vertices,vertices[1:]+vertices[:1]):
   ia,ib=a.z<=height,b.z<=height
   if ia:clipped.append((a,ua))
   if ia!=ib:
    t=(height-a.z)/(b.z-a.z);clipped.append((a.lerp(b,t),ua.lerp(ub,t)))
  if len(clipped)>=3:p.face([(v.x,v.z,-v.y) for v,uv in clipped],0,[tuple(uv) for v,uv in clipped])

def prototype(lod,variant):
 p=PlantMesh();basal(p,original[lod,variant]);rr=random.Random(8800+variant)
 # Broadleaf fork structure, replacing the old conifer's tiered branches.
 points=[((0,4.05,0),.20),((.08,6.6,.06),.17),((-.12,8.5,.17),.12),((.40,11.7,-.05),.025)]
 for (a,r),(b,q) in zip(points,points[1:]):p.tube(a,b,r,q,n=10)
 for j in range(7):
  angle=j*math.tau/7+variant*.41;base=Vector((.02,6.1+j*.42,.04))
  mid=Vector((math.cos(angle)*2.5,9.2+rr.uniform(-.4,.8),math.sin(angle)*2.5))
  end=Vector((math.cos(angle)*5.6,12.4+rr.uniform(-1,1),math.sin(angle)*5.6))
  tip=end+Vector((math.cos(angle+.4)*.7,1.1,math.sin(angle+.4)*.7))
  p.tube(base,mid,.145,.08,n=8);p.tube(mid,end,.08,.022,n=7);p.tube(end,tip,.022,.008,n=6)
  for k in range(3):
   a=mid.lerp(end,.25+k*.26);theta=angle+(1 if k%2 else -1)*.67
   b=a+Vector((math.cos(theta)*1.55,.85+rr.random()*.9,math.sin(theta)*1.55))
   p.tube(a,b,.027,.006,n=6)
 m=leaf_source[lod,variant]
 for f in m.polygons:
  if f.material_index!=1:continue
  # Reuse the authored five-lobed leaf atlas. Repeating UVs compensates for
  # the larger mature crown so leaves don't become giant flat silhouettes.
  p.face([(m.vertices[i].co.x*1.70,m.vertices[i].co.z*1.85,-m.vertices[i].co.y*1.70) for i in f.vertices],1,
   [(m.uv_layers.active.data[i].uv.x*1.65,m.uv_layers.active.data[i].uv.y*1.65) for i in f.loop_indices])
 mesh=p.finish('Central_Pl​atanus_'+lod+'_v88_'+str(variant),[bpy.data.materials['Canopy_plane_bark_v87'],bpy.data.materials['Canopy_plane_MASK_v87']])
 mesh.calc_loop_triangles();return mesh

protos={(lod,v):prototype(lod,v) for lod in ['near','far'] for v in range(3)}
placements={}
for o in central:
 lod=o['vegetation_lod'];v=int(o['tree_crown_variant'])
 placements[o.name]=dict(matrix=list(np.asarray(o.matrix_world).ravel()),lod=lod,variant=v,original_mesh=o.data.name)
 o.data=protos[lod,v];o['canopy_form']='plane-central';o['canopy_revision']='v88';o['species_portrayal']='User-directed Platanus; official guide names this metasequoia avenue'
labels=[]
for o in scene.objects:
 if o.type=='FONT' and o.data.body=='메타세쿼이아길':
  labels.append(dict(object=o.name,before=o.data.body,after='중앙 가로수길'))
  o.data=o.data.copy();o.data.body='중앙 가로수길'
world=json.loads(before_world)
for p in world['places']:
 if p['id']=='avenue':p['name']='중앙 가로수길';p['description']='넓게 이어지는 수관 아래를 걸어보세요.'
for s in world['signs']:
 if s['text']=='메타세쿼이아길':s['text']='중앙 가로수길'
world['limitations'].append('Central avenue Platanus portrayal follows the user’s explicit selection. Official references name this a metasequoia avenue; current individual species and dimensions unverified.')
(O/'world-after.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
report=dict(source=str(SOURCE.relative_to(R)),output=str(TARGET.relative_to(R)),central_tree_pairs=len(central)//2,
 changed_objects=placements,protected_geometry_hashes=protected,shared_prototypes=6,labels=labels,
 basal_preservation_height=4.05,crown_scale=[1.70,1.70,1.85],world_before_sha256=hashlib.sha256(before_world).hexdigest(),
 limitations=['User selected the central long avenue for Platanus portrayal after v87 deployment. This supersedes the side-path-only assumption; it is not a new field species survey.','Existing roots, lower trunk geometry, tree transforms, all other trees and groundcover retained. Upper branch structure intentionally changes to broadleaf forks. No terrain changes.'])
(R/'knowledge/sources/arboretum/central-platanus-v88.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v88.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('CENTRAL PLATANUS EXPORTED',len(central)//2,'pairs; labels',labels,flush=True)
