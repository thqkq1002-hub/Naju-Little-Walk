"""Reduce leaf-card overdraw without changing root, wood or authored textures."""
import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v87';target=O/'naju-arboretum-canopy-v87-r4.blend'
if target.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-canopy-v87-r3.blend'));scene=bpy.context.scene
meshes={o.data:(o['reference_habit'],o['vegetation_lod']) for o in scene.objects if o.type=='MESH' and o.get('canopy_form')}
removed={}
for mesh,(habit,lod) in meshes.items():
 bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table();index=0;drop=[]
 for face in bm.faces:
  if face.material_index!=1:continue
  card=index//(2 if lod=='near' else 1);index+=1
  remove=card%2==1 if habit=='meta' or lod=='far' else card%3==2
  if remove:drop.append(face)
 removed[mesh.name]=len(drop);bmesh.ops.delete(bm,geom=drop,context='FACES')
 loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 bm.to_mesh(mesh);bm.free();mesh.update();mesh.calc_loop_triangles()
P=R/'knowledge/sources/arboretum/canopy-v87.json';report=json.loads(P.read_text(encoding='utf-8'))
report['output']=str(target.relative_to(R));report['overdraw_refinement']=dict(removed_faces=removed,scope='Interleaved redundant leaf cards only; source wood and placements retained. Browser diagnostics required.')
report['triangles']={m.name:len(m.loop_triangles) for m in meshes}
P.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v87-r4.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('REDUNDANT LEAF LAYERS REMOVED',sum(removed.values()),flush=True)
