"""Stage the Meshy-authored guide characters for the walking app.

Run: blender --background --python scripts/stage_npc_assets.py -- [--inspect]

Imports each `*-colored-v4.glb` draft, measures it, drops it onto the ground,
scales it to a walkable height and turns it to face local -Z (the app applies a
character's yaw straight to rotation.y). Exports to public/models with gzip.
"""
import bpy, sys, math, gzip, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets' / 'npc' / 'meshy-first-pass-20261002'
MODELS = ROOT / 'public' / 'models'
INSPECT = '--inspect' in sys.argv

# slug, source folder, target height in metres, extra yaw so the face points at -Z
CHARACTERS = [
    ('npc-baedole', 'baedoli', 'baedoli-colored-v4.glb', 1.25, 180),
    ('npc-beodeul', 'beodeuri', 'beodeuri-colored-v4.glb', 1.70, 180),
    ('npc-hongdori', 'hongdoli', 'hongdoli-colored-v4.glb', 1.15, 180),
    ('npc-dasi-teacher', 'teacher', 'teacher-colored-v4.glb', 1.72, 180),
]

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def bounds(objects):
    lo = Vector((1e9, 1e9, 1e9)); hi = Vector((-1e9, -1e9, -1e9))
    for o in objects:
        if o.type != 'MESH':
            continue
        for corner in o.bound_box:
            p = o.matrix_world @ Vector(corner)
            lo = Vector((min(lo[i], p[i]) for i in range(3)))
            hi = Vector((max(hi[i], p[i]) for i in range(3)))
    return lo, hi

report = []
for slug, folder, filename, target_height, extra_yaw in CHARACTERS:
    clear()
    bpy.ops.import_scene.gltf(filepath=str(SOURCE / folder / filename))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    lo, hi = bounds(meshes)
    size = hi - lo
    # Blender is Z-up after the glTF import, so Z is the character's height.
    scale = target_height / size.z if size.z else 1
    root = bpy.data.objects.new(f'{slug}_root', None)
    bpy.context.scene.collection.objects.link(root)
    for o in meshes:
        if o.parent is None:
            o.parent = root
            o.matrix_parent_inverse = root.matrix_world.inverted()
    root.scale = (scale, scale, scale)
    root.rotation_euler = (0, 0, math.radians(extra_yaw))
    bpy.context.view_layer.update()
    lo2, hi2 = bounds(meshes)
    centre = (lo2 + hi2) / 2
    # Feet on the ground, centred on the walking position.
    root.location = (-centre.x, -centre.y, -lo2.z)
    bpy.context.view_layer.update()
    lo3, hi3 = bounds(meshes)
    report.append({'slug': slug, 'source_size': [round(v, 3) for v in size],
                   'scale': round(scale, 4), 'final_size': [round(v, 3) for v in (hi3 - lo3)],
                   'final_min_z': round(lo3.z, 4)})
    if INSPECT:
        # Look from Blender +Y, which the glTF export turns into the app's -Z front.
        height = hi3.z
        bpy.ops.object.camera_add(location=(0, height * 1.9, height * .55))
        camera = bpy.context.object
        camera.rotation_euler = (Vector((0, 0, height * .55)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.lens = 50
        bpy.context.scene.camera = camera
        bpy.ops.object.light_add(type='SUN', location=(2, 4, 4))
        bpy.context.object.data.energy = 4
        world = bpy.data.worlds.new(f'{slug}_bg'); world.use_nodes = True
        world.node_tree.nodes['Background'].inputs[1].default_value = 1.2
        bpy.context.scene.world = world
        names = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
        bpy.context.scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in names else 'BLENDER_EEVEE_NEXT'
        bpy.context.scene.render.resolution_x = 420; bpy.context.scene.render.resolution_y = 560
        bpy.context.scene.render.filepath = str(ROOT / 'outputs' / f'{slug}-facing.png')
        bpy.ops.render.render(write_still=True)
        continue
    # A 2048 atlas is more than a character seen from a few metres needs.
    for image in bpy.data.images:
        if image.size[0] > 1024:
            image.scale(1024, 1024)
    glb = MODELS / f'{slug}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_active_scene=True,
                              export_cameras=False, export_lights=False, export_apply=True)
    glb.with_suffix('.glb.gz').write_bytes(gzip.compress(glb.read_bytes(), compresslevel=9, mtime=0))
    report[-1]['bytes'] = glb.stat().st_size
    report[-1]['gz_bytes'] = glb.with_suffix('.glb.gz').stat().st_size

print(json.dumps(report, ensure_ascii=False, indent=1))
