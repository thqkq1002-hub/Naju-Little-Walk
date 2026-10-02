"""Correct a previously guessed roof rim blocking the newly authored lower station."""
import bpy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v69';O.mkdir(exist_ok=True);TARGET=O/'bitgaram-access-v69.blend'
if TARGET.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/quality-v68/bitgaram-access-v68.blend'))
shell=bpy.data.objects['photo_exhibition_sloped_shell'];changed=0
for v in shell.data.vertices:
 if -v.co.y<111 and v.co.z>6.22:v.co.z=6.22;changed+=1
shell.data.update();shell['estimated_roof_rim_correction']='Lower station north edge ends at the existing authored roof terrace level; precise building section remains estimated'
report=json.loads((R/'knowledge/sources/bitgaram/access-v68.json').read_text(encoding='utf8'))
report['output']=str(TARGET.relative_to(R));report['modified_existing_meshes']=['photo_exhibition_sloped_shell'];report['roof_rim_vertices_adjusted']=changed
report['estimated'].append('north roof rim adjusted to existing 6.22 m authored terrace; no surveyed elevation')
world=json.loads((R/report['world_output']).read_text(encoding='utf8'));WP=O/'bitgaram-park-world-v69.json';WP.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8');report['world_output']=str(WP.relative_to(R))
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(O/'bitgaram-park-v69.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
(R/'knowledge/sources/bitgaram/access-v69.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('LOWER OPENING EXPORTED',changed,flush=True)
