"""Remove speculative interior contents, preserve previous artist revision."""
import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'outputs/bitgaram/bitgaram-observatory-empty.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-observatory-interior-finish.blend'))
prefixes=('bench','telescope','view_guide','lift_','finish_bench','finish_scope','finish_lift','finish_core','finish_panorama','label_')
removed=[]
for o in list(bpy.data.objects):
    if o.name.startswith(prefixes):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
p=root/'public/bitgaram-observatory-world.json';w=json.loads(p.read_text(encoding='utf-8'))
w['solids']=[s for s in w['solids'] if not s['name'].startswith(prefixes)]
w['signs']=[]
w['limitations']=['Interior furnishings and speculative central facilities removed at user request. Existing exterior context remains schematic; real photographic panorama is pending a suitable source image.']
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-observatory.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
bpy.context.scene.render.filepath=str(root/'outputs/bitgaram/observatory-empty-review.png');bpy.ops.render.render(write_still=True)
print('Removed',len(removed),flush=True)
