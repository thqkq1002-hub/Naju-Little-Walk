"""Keep the verified original wood; lift only low leaf-card edges in new r3."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v87'
source=O/'naju-arboretum-canopy-v87-r2.blend';target=O/'naju-arboretum-canopy-v87-r3.blend'
if target.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
meshes={o.data for o in scene.objects if o.type=='MESH' and o.get('canopy_form')}
changed=0
for mesh in meshes:
 leafverts={i for face in mesh.polygons if face.material_index==1 for i in face.vertices}
 for i in leafverts:
  if mesh.vertices[i].co.z<3.05:mesh.vertices[i].co.z=3.05;changed+=1
 mesh.update();mesh.calc_loop_triangles()
P=R/'knowledge/sources/arboretum/canopy-v87.json';report=json.loads(P.read_text(encoding='utf-8'))
report['output']=str(target.relative_to(R));report['clearance_refinement']=dict(source=str(source.relative_to(R)),leaf_edges_lifted=changed,minimum_local_foliage_height=3.05,original_wood_untouched=True)
P.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v87-r3.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('CLEARANCE REFINED',changed,flush=True)
