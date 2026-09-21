"""Apply the terrain-aligned path mesh to the overview without re-appending the forest."""
import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-overview-surroundings-final.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-overview-surroundings.blend'))
for o in list(bpy.data.objects):
    if o.name.startswith('surrounding_mapped_paths'):bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(root/'outputs/bitgaram/bitgaram-park-surroundings.blend'),link=False) as (source,dest):
    dest.objects=[n for n in source.objects if n.startswith('surrounding_mapped_paths')]
for o in dest.objects:bpy.context.scene.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-overview.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
