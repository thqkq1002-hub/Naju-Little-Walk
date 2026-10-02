"""Preserve current park coordinates; author shared, paired crowns in a new Blender file."""
import bpy,bmesh,ast,math,random,json,gzip,hashlib,shutil,sys
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1]
O=R/'outputs/quality-v58';O.mkdir(exist_ok=True)
TARGET=O/'bitgaram-park-crowns-v58.blend'
if TARGET.exists():raise RuntimeError('Existing artist revision preserved; use a new output revision.')
SOURCE=R/'outputs/palette-v51/bitgaram-park-color-v51.blend'
ASSET=R/'public/models/bitgaram-park.glb'
snapshot=O/'bitgaram-park-before-v58.glb'
if not snapshot.exists():shutil.copy2(ASSET,snapshot)
world_path=R/'public/bitgaram-park-world.json'
world_hash=hashlib.sha256(world_path.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
source=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<shared plant mesh>','exec'))
with bpy.data.libraries.load(str(R/'outputs/palette-v51/naju-arboretum-color-v51.blend'),link=False) as (available,loaded):
 loaded.materials=[name for name in ['Authored_bark_grain','Botanical_living_leaf','Reference_dense_foliage'] if name in available.materials]
bark=bpy.data.materials.get('Authored_bark_grain')
leaf=bpy.data.materials.get('Botanical_living_leaf')
dense=bpy.data.materials.get('Reference_dense_foliage')
if not all([bark,leaf,dense]):raise RuntimeError('The authored bark and leaf material sources are required.')
leaf.use_backface_culling=False;dense.use_backface_culling=False
materials=[bark,leaf,dense]

def matches(o,p):return o.name==p or o.name.startswith(p+'.')
def bounds(o):
 coords=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [min(v[i] for v in coords) for i in range(3)],[max(v[i] for v in coords) for i in range(3)]
def center(o):
 a,b=bounds(o);return ((a[0]+b[0])/2,(a[1]+b[1])/2,a[2],b[2])
sys.path.insert(0,str(R/'scripts'))
from park_foliage import spray_material,crown_prototype
spray=spray_material()
protos={(variant,lod):crown_prototype(PlantMesh,bark,spray,variant,lod=='near') for variant in range(4) for lod in ['near','far']}
# Uniform frame for every paired prototype: actual bounds stay within the old tree crown.
for variant in range(4):
 near=protos[variant,'near'];far=protos[variant,'far']
 coordinates=[v.co for mesh in [near,far] for v in mesh.vertices]
 width=max(abs(v.x) for v in coordinates)*2;depth=max(abs(v.y) for v in coordinates)*2;top=max(v.z for v in coordinates)
 for mesh in [near,far]:
  for v in mesh.vertices:v.co.x/=width;v.co.y/=depth;v.co.z/=top
  mesh.update()

new=bpy.data.collections.new('06_Authored_Paired_Crowns');scene.collection.children.link(new)
placements=[];removed=[];bpy.context.view_layer.update()
for trunk_prefix,canopy_prefix in [('woodland_trunk','aerial_woodland_canopy'),('shore_finish_trunk','shore_finish_tree'),('surrounding_tree_trunk','surrounding_path_tree'),('tree_trunk','tree_canopy')]:
 trunks=[o for o in scene.objects if o.type=='MESH' and matches(o,trunk_prefix)]
 canopies=[o for o in scene.objects if o.type=='MESH' and matches(o,canopy_prefix)]
 roots=[center(o) for o in trunks];assigned=[[] for _ in trunks]
 for canopy in canopies:
  cx,cy,_,_=center(canopy)
  index=min(range(len(roots)),key=lambda i:(roots[i][0]-cx)**2+(roots[i][1]-cy)**2)
  assigned[index].append(canopy)
 for index,trunk in enumerate(trunks):
  if not assigned[index]:continue
  x,y,ground,trunk_top=roots[index];boxes=[bounds(o) for o in assigned[index]]
  left=min(b[0][0] for b in boxes);right=max(b[1][0] for b in boxes)
  low=min(b[0][1] for b in boxes);high=max(b[1][1] for b in boxes);top=max(b[1][2] for b in boxes)
  width=2*max(x-left,right-x);depth=2*max(y-low,high-y);height=top-ground
  if height<=0 or width<=0 or depth<=0:raise RuntimeError('Invalid authored tree envelope')
  # Preserve the original trunk and base. Do not add physical obstacles or shift paths.
  if len(trunk.data.materials)==1:trunk.data.materials[0]=bark
  variant=len(placements)%4;angle=((index*2.399)%math.tau)
  for lod in ['near','far']:
   obj=bpy.data.objects.new(canopy_prefix+'_detail_'+lod,protos[variant,lod]);new.objects.link(obj)
   obj.location=(x,y,ground);obj.scale=(width,depth,height)
   # Rotation is deliberately kept zero so fitted XY envelopes cannot cross an existing clearance.
   obj['authored_vegetation']=True;obj['vegetation_lod']=lod;obj['vegetation_distance']=64
   obj['quality_revision']='park-crowns-v58';obj['tree_source_trunk']=trunk.name;obj['estimated_tree_form']='irregular broadleaf';obj.hide_render=lod=='far'
  placements.append(dict(trunk=trunk.name,position=[x,ground,-y],scale=[width,height,depth],variant=variant,source_canopies=[o.name for o in assigned[index]]))
 removed.extend(canopies)
for obj in removed:bpy.data.objects.remove(obj,do_unlink=True)
# The new near crown contains connected, tapering branches in the existing envelope.
for obj in list(scene.objects):
 if matches(obj,'woodland_branch'):bpy.data.objects.remove(obj,do_unlink=True)

bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
out=O/'bitgaram-park-v58.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
assert hashlib.sha256(world_path.read_bytes()).hexdigest()==world_hash,'World collision and paths must remain unchanged'
metrics=dict(source_blend=str(SOURCE.relative_to(R)),source_glb_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),world_sha256=world_hash,trees=len(placements),removed_canopies=len(removed),shared_crown_meshes=len(protos),near_faces=sum(len(protos[i,'near'].polygons) for i in range(4)),far_faces=sum(len(protos[i,'far'].polygons) for i in range(4)),glb_bytes=out.stat().st_size,gzip_bytes=Path(str(out)+'.gz').stat().st_size,placements=placements,note='Existing ground coordinates and crowns measured from the current authored scene. Species and crown details remain estimated; no newly surveyed trees.')
(R/'knowledge/sources/bitgaram/park-quality-v58.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print('PARK QUALITY EXPORTED',len(placements),out.stat().st_size,flush=True)

if '--render' in sys.argv:
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=32
 scene.world=bpy.data.worlds.new('Park review daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.68,.81,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.4;sun.rotation_euler=(.5,-.6,-.7);sun.data.angle=.14
 bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=32;camera.data.clip_end=3000
 scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
 scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
 for name,position,aim in [('park-entry',(0,-21,17.7),(0,-6,22)),('park-woodland',(0,-68,10),(18,-60,13)),('park-aerial',(-230,-260,200),(0,-25,10))]:
  camera.location=position;camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(O/(name+'-v58.png'));bpy.ops.render.render(write_still=True)
