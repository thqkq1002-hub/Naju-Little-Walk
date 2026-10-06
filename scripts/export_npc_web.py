"""Compress only agent-authored v5 web exports; preserve the editable 4K Blender source."""
from pathlib import Path
import bpy, sys, json, shutil

root = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
character = args[0]
version = args[1] if len(args)>1 else 'v5'
base = root / 'assets/npc/meshy71-baedoli-clean-20261002' if character=='baedoli' and version=='v6' else root / 'assets/npc/meshy71-rigged-20261002' / character
bpy.ops.wm.open_mainfile(filepath=str(base / f'{character}-rigged-{version}.blend'))
for image in bpy.data.images:
    if image.type == 'IMAGE' and max(image.size) > 2048:
        image.scale(2048,2048);image.pack()
rig = bpy.data.objects[character+'_GuideRig']
mesh = bpy.data.objects[character+'_Body']
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True)
bpy.context.view_layer.objects.active = rig
dest = root / f'public/models/npc/{character}-{version}.glb'
bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,
    export_animations=True,export_animation_mode='NLA_TRACKS',export_nla_strips=True,
    export_force_sampling=True,export_skins=True,export_all_influences=False,
    export_image_format='WEBP',export_image_quality=95)
shutil.copyfile(dest,base/f'{character}-rigged-{version}.glb')
report = json.loads((base/'rig-verification.json').read_text(encoding='utf-8'))
report.update(web_bytes=dest.stat().st_size,web_texture_resolution=2048,web_texture_format='WebP, quality 95')
(base/'rig-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'character':character,'web_bytes':dest.stat().st_size}))
