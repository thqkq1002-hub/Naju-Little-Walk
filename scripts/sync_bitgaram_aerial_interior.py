"""Keep the interior's overhead architecture consistent with its park exterior."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
revision='entry-detail' if '--entry-detail' in sys.argv else 'aerial-detail'
target=root/f'outputs/bitgaram/bitgaram-observatory-{revision}.blend'
if target.exists():raise RuntimeError('Existing interior revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-observatory.blend'))
for o in list(bpy.data.objects):
    if o.name.startswith(('observatory_roof','silver_upper_rim','silver_lower_rim')) or (revision=='entry-detail' and o.name.startswith(('panoramic_glazing','window_mullion'))):
        bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(root/f'outputs/bitgaram/bitgaram-park-{revision}.blend'),link=False) as (source,dest):
    dest.objects=[n for n in source.objects if n.startswith(('aerial_roof','aerial_inner_reveal','aerial_sweeping_fascia','aerial_deck_edge','aerial_fascia_seam','photo_wrap_'))]
    if revision=='entry-detail':dest.objects += [n for n in source.objects if n.startswith(('panoramic_glazing','window_mullion'))]
for o in dest.objects:
    if o:
        bpy.context.scene.collection.objects.link(o);o.location.z-=30
        if o.name.startswith(('aerial_roof','aerial_inner_reveal')):o['hide_in_overview']=True
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-observatory.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
