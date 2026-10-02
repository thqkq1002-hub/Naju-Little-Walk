"""Give the newly authored timber boards usable grain UVs in a new revision."""
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v61';P=R/'knowledge/sources/arboretum/garden-quality-v61.json'
report=json.loads(P.read_text(encoding='utf-8'));target=O/'naju-arboretum-garden-v61-uv.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']))
for o in bpy.context.scene.objects:
 if not o.name.startswith('play_canopy'):continue
 mesh=o.data;uv=mesh.uv_layers.new(name='Timber_grain_metres')
 for f in mesh.polygons:
  for li in f.loop_indices:
   p=mesh.vertices[mesh.loops[li].vertex_index].co
   # Long grain follows each board, with different sampled starts across the roof.
   s=.98*p.x-.20*p.y;t=-.20*p.x-.98*p.y
   uv.data[li].uv=(s*2.2,t*.35+p.z*.2)
report['draft_output']=report['output'];report['output']=str(target.relative_to(R));report['canopy_uv_authored']=True
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));P.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v61-uv.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
print('CANOPY UV COMPLETE',flush=True)
