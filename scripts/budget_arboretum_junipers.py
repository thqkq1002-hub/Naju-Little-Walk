"""Reduce sub-pixel scale-leaf geometry, keeping the guarded v65 layout/world."""
import bpy,bmesh,math,random,json,ast,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v66';O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v65/naju-arboretum-juniper-road-v65.blend'
target=O/'naju-arboretum-juniper-budget-v66.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
tree=ast.parse((R/'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PlantMesh'],type_ignores=[]),'<PlantMesh>','exec'))
tree=ast.parse((R/'scripts/upgrade_arboretum_junipers.py').read_text(encoding='utf-8'))
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['habit','build','fingerprint']]
class Budget(ast.NodeTransformer):
 def visit_Constant(self,node):
  if type(node.value) is int and node.value in [390,55,40,26,24]:
   return ast.copy_location(ast.Constant({390:120,55:14,40:26,26:16,24:14}[node.value]),node)
  return node
tree=Budget().visit(ast.Module(body=selected,type_ignores=[]));ast.fix_missing_locations(tree);exec(compile(tree,'<budgeted-prototypes>','exec'))
bark=bpy.data.materials['Authored_bark_grain'];dense=bpy.data.materials['Clipped_juniper_dense_veins']
greens=[bpy.data.materials['Clipped_juniper_spray_'+str(i)] for i in range(3)];materials=[bark,dense,*greens]
old_meshes={(habit(o),o.get('vegetation_lod')):o.data for o in scene.objects if o.type=='MESH' and habit(o) in ['column','oval']}
protos={(kind,lod,v):build(kind,lod,v) for kind in ['column','oval'] for lod in ['near','far'] for v in range(3)}
for mesh in protos.values():
 for poly in mesh.polygons:
  if poly.material_index==1:
   for index in poly.loop_indices:
    mesh.uv_layers.active.data[index].uv.x*=12;mesh.uv_layers.active.data[index].uv.y*=5
changed={}
for o in scene.objects:
 if o.type!='MESH' or habit(o) not in ['column','oval']:continue
 kind=habit(o);lod=o['vegetation_lod'];variant=o['juniper_variant'];old=o.data
 before=np.asarray([v.co[:] for v in old.vertices]);o.data=protos[kind,lod,variant]
 o['juniper_budget_revision']='Sub-pixel leaf sprays reduced v66; continuous volume and v65 placement preserved'
 changed[o.name]={'old_mesh':old.name,'habit':kind,'lod':lod,'variant':variant,'matrix':[v for row in o.matrix_world for v in row],'bounds_before':[before.min(axis=0).tolist(),before.max(axis=0).tolist()]}
report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'changed_objects':changed,'protected_geometry_hashes':{o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed},'world_sha256':hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest(),'shared_prototypes':len(protos),'leaf_sprays':{'near':120,'far':14},'reference':'https://hangamja.tistory.com/1607','limitation':'2021 photo-informed shape; species, size and planting offset remain inferred.'}
(R/'knowledge/sources/arboretum/juniper-budget-v66.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v66.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('JUNIPER BUDGET',len(changed),flush=True)
