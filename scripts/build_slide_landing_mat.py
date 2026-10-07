"""Landing mat at the foot of the Bitgaram stone slide (interpretive prop, not a surveyed object).

blender --background --python scripts/build_slide_landing_mat.py

Creates assets/props/slide-landing-mat.blend once and exports public/models/props/slide-landing-mat.glb.
If the .blend already exists it is opened and only re-exported, so hand edits in Blender are kept.
Frame: centred on the top surface, top at z=0, 2.0 m wide (X) and 3.1 m long (Y), 0.6 m deep.
"""
import bpy, bmesh
from pathlib import Path

R = Path(__file__).resolve().parents[1]
BLEND = R / 'assets/props/slide-landing-mat.blend'
GLB = R / 'public/models/props/slide-landing-mat.glb'
W, L, D = 2.0, 3.1, 0.6


def material(name, rgb, rough=.86):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*rgb, 1); bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = 0
    m.diffuse_color = (*rgb, 1)
    return m


def box(name, size, location, mat, bevel=0.0, segments=3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.location = location; me.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new('round', 'BEVEL'); mod.width = bevel; mod.segments = segments; mod.limit_method = 'NONE'
        bpy.context.view_layer.objects.active = ob; ob.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name); ob.select_set(False)
    for p in me.polygons: p.use_smooth = bevel > 0
    return ob


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    blue = material('Mat_blue_vinyl', (0.06, 0.24, 0.62), .7)
    yellow = material('Mat_yellow_piping', (0.95, 0.66, 0.08), .75)
    strap = material('Mat_dark_strap', (0.05, 0.06, 0.08), .9)
    # Padded body; its lower part sits below the sloping lawn so no gap shows under the edges.
    box('landing_mat_body', (W, L, D), (0, 0, -D / 2), blue, bevel=.07, segments=4)
    # Yellow piping just proud of the edges and three quilted seams across the landing.
    for x in (-W / 2 + .02, W / 2 - .02):
        box('landing_mat_piping', (.05, L - .1, .035), (x, 0, -.012), yellow, bevel=.015, segments=2)
    for y in (-L / 2 + .02, L / 2 - .02):
        box('landing_mat_piping', (W - .1, .05, .035), (0, y, -.012), yellow, bevel=.015, segments=2)
    for y in (-L / 4, 0, L / 4):
        box('landing_mat_seam', (W - .3, .035, .012), (0, y, .002), yellow, bevel=.004, segments=1)
    # Carry handles on the long sides.
    for x in (-W / 2 - .012, W / 2 + .012):
        for y in (-.75, .75):
            box('landing_mat_handle', (.024, .42, .06), (x, y, -.14), strap, bevel=.01, segments=2)
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


if BLEND.exists():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
else:
    build()
GLB.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format='GLB', export_apply=True, export_yup=True)
print('SLIDE_MAT', GLB, GLB.stat().st_size, flush=True)
