"""Use the same authored park in the orbit map, without regenerating the city."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
revision='entry-detail' if '--entry-detail' in sys.argv else 'aerial-detail'
if '--walkway-detail' in sys.argv:revision='walkway-detail'
if '--forest-detail' in sys.argv:revision='forest-detail'
if '--surroundings' in sys.argv:revision='surroundings'
target=root/f'outputs/bitgaram/bitgaram-overview-{revision}.blend'
if target.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing overview revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-overview.blend'))
for o in list(bpy.data.objects):
    if o.name.startswith(('tower_disc','Baemesan_estimated','building_656235304','building_908801772','park_path')):
        bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(root/f'outputs/bitgaram/bitgaram-park-{revision}.blend'),link=False) as (source,dest):
    dest.objects=[n for n in source.objects if not n.startswith(('context_ground','context_building','context_road','lake_osm_','Camera','Sun','Light'))]
for o in dest.objects:
    if o and o.type in {'MESH','FONT'}:bpy.context.scene.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-overview.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
