"""Build a standing Naju cultural-guide (docent) figure and export the browser GLB.

Run with: blender --background --python scripts/build_npc_guide.py
Original stylised figure (durumagi coat, sash, gat) - no photo reference bundled.
Reuses the shared MuseumGeometry primitives (lathed vessel, tube, box, mesh) so the
export shares the exact Blender-to-glTF axis convention as every other asset here:
the model's local -Z is its front, matching the project's yaw convention (rotation.y
applied directly, forward = (-sin(yaw), -cos(yaw))).
"""
import bpy, sys, math, json, gzip
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from museum_geometry import MuseumGeometry

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs' / 'npc-hall-guide.blend'
if OUTPUT.exists() and '--replace' not in sys.argv:
    raise RuntimeError('Output exists. Use -- --replace to rebuild the generated deliverable.')
OUTPUT.parent.mkdir(exist_ok=True)
(ROOT / 'public' / 'models').mkdir(parents=True, exist_ok=True)

ROBE = '#2f4d3a'; SASH = '#c96734'; SKIN = '#e7bd94'; HAT = '#191919'; STRING = '#8a6a3d'; SHOE = '#241f1c'; MOUTH = '#7a4a3a'; EYE = '#2b2016'

scene = bpy.data.scenes.new('Naju_NPC_Hall_Guide')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
g = MuseumGeometry(scene, center=(0, 0), angle=0)

def sphere(name, x, y, z, r, color, rings=12, segments=16):
    verts = []
    for j in range(rings + 1):
        v = j / rings * math.pi
        ring_r = r * math.sin(v)
        yy = y + r * math.cos(v)
        for i in range(segments):
            u = i / segments * math.tau
            verts.append((x + ring_r * math.cos(u), yy, z + ring_r * math.sin(u)))
    faces = []
    for j in range(rings):
        for i in range(segments):
            a = j * segments + i; b = j * segments + (i + 1) % segments
            c = (j + 1) * segments + (i + 1) % segments; d = (j + 1) * segments + i
            faces.append((a, b, c, d))
    return g.mesh(name, verts, faces, color, smooth=True)

# Durumagi coat: lathed profile, wide hem sweeping in to a cinched waist and
# flaring again at the chest before narrowing to a high collar near the chin.
g.vessel('guide_durumagi_coat', 0, 0, 0, 1, ROBE, profile=[
    (0.05, .28), (0.15, .265), (0.45, .24), (0.75, .225),
    (0.95, .235), (1.15, .255), (1.40, .195),
])
# Sash tied at the waist, wrapped slightly proud of the coat body.
g.vessel('guide_waist_sash', 0, 0, 0, 1, SASH, profile=[(0.83, .235), (0.90, .25), (0.97, .235)])

for side in (-1, 1):
    x = side * .30
    g.vessel(f'guide_sleeve_{"left" if side < 0 else "right"}', x, 0, 0, 1, ROBE, profile=[
        (1.20, .115), (1.00, .105), (0.75, .095), (0.55, .10),
    ])
    sphere(f'guide_hand_{"left" if side < 0 else "right"}', x, .48, .01, .045, SKIN, rings=8, segments=10)

g.tube('guide_neck', (0, 1.40, 0), (0, 1.475, 0), .058, SKIN)
sphere('guide_head', 0, 1.585, 0, .11, SKIN, rings=14, segments=18)
g.box('guide_eye_left', -.033, 1.595, -.103, .020, .011, .004, EYE)
g.box('guide_eye_right', .033, 1.595, -.103, .020, .011, .004, EYE)
g.box('guide_mouth', 0, 1.55, -.108, .042, .007, .004, MOUTH)

# Gat: a wide horsehair brim wrapped around the upper head, with a rounded
# stovepipe crown resting on top - the silhouette of a Joseon-period guide's hat.
g.vessel('guide_gat_brim', 0, 0, 0, 1, HAT, profile=[(1.58, .035), (1.625, .30), (1.66, .035)])
g.vessel('guide_gat_crown', 0, 0, 0, 1, HAT, profile=[(1.65, .13), (1.72, .14), (1.83, .12), (1.87, .09)])
for side in (-1, 1):
    g.tube(f'guide_gat_string_{"left" if side < 0 else "right"}', (side * .095, 1.60, -.04), (side * .06, 1.42, -.02), .008, STRING)

for side in (-1, 1):
    g.box(f'guide_shoe_{"left" if side < 0 else "right"}', side * .10, .035, -.02, .10, .06, .22, SHOE)

from mathutils import Vector
bpy.ops.object.camera_add(location=g.bp(1.0, 1.5, -2.3))
camera = bpy.context.object; camera.name = 'Guide_preview_camera'
camera.rotation_euler = (Vector(g.bp(0, 1.3, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 45
scene.camera = camera
bpy.ops.object.light_add(type='SUN', location=(-2, 3, 3))
sun = bpy.context.object; sun.data.energy = 3
scene.world = bpy.data.worlds.new('Guide_daylight'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.72, .82, .88, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .8
scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 900; scene.render.resolution_y = 1100
scene.render.filepath = str(ROOT / 'outputs' / 'npc-hall-guide-preview.png')
scene.view_settings.view_transform = 'AgX'

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.export_scene.gltf(filepath=str(ROOT / 'public' / 'models' / 'npc-hall-guide.glb'), export_format='GLB', use_active_scene=True, export_cameras=False, export_lights=False, export_extras=True, export_apply=True)
(ROOT / 'public' / 'models' / 'npc-hall-guide.glb.gz').write_bytes(gzip.compress((ROOT / 'public' / 'models' / 'npc-hall-guide.glb').read_bytes(), compresslevel=9, mtime=0))
print(json.dumps({'blend': str(OUTPUT), 'objects': len(scene.objects)}, ensure_ascii=False))
if '--render' in sys.argv:
    bpy.ops.render.render(write_still=True)
