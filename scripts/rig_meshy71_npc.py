"""Build region-guide skeletons, subtle grounded clips and separate web GLBs in Blender."""
from pathlib import Path
from mathutils import Vector, Quaternion
import bpy, json, math, sys, shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assets/npc/meshy71-rigged-20261002'
args = sys.argv[sys.argv.index('--') + 1:]
character = args[0]
version = args[1] if len(args)>1 else 'v5'
clean = version == 'v6' and character == 'baedoli'
if clean: BASE = ROOT / 'assets/npc/meshy71-baedoli-clean-20261002'
HEIGHTS = {'baedoli': 1.2, 'beodeuri': 1.65, 'hongdoli': 1.05, 'teacher': 1.72}
H = HEIGHTS[character]
mascot = character in ('baedoli', 'hongdoli')
out = BASE if clean else BASE / character
out.mkdir(parents=True, exist_ok=True)
source = out / 'baedoli-meshy71-original.glb' if clean else (ROOT / 'assets/npc/meshy71-ultra-20261002/baedoli-meshy71-original.glb' if character == 'baedoli' else out / 'meshy71-original.glb')
blend = out / f'{character}-rigged-{version}.blend'
web = ROOT / f'public/models/npc/{character}-{version}.glb'
assert not blend.exists() and not web.exists(), 'Never overwrite existing review edits or published assets'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
low, high = [Vector([fn(p[i] for p in points) for i in range(3)]) for fn in (min, max)]
factor = H / (high.z - low.z)
for ob in meshes:
    # Bake authoring coordinates without changing the original GLB.
    matrix = ob.matrix_world.copy()
    ob.parent = None
    for v in ob.data.vertices:
        p = matrix @ v.co
        v.co = ((p.x - (high.x + low.x) / 2) * factor, (p.y - (high.y + low.y) / 2) * factor, (p.z - low.z) * factor)
    ob.matrix_world.identity()
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes: ob.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1: bpy.ops.object.join()
mesh = bpy.context.object
mesh.name = character + '_Body'
mesh.data.calc_loop_triangles()
original_triangles = len(mesh.data.loop_triangles)
budget = 60000 if clean else 55000 if not mascot else 45000
if original_triangles > budget:
    modifier = mesh.modifiers.new('Web_detail_budget', 'DECIMATE')
    modifier.ratio = budget / original_triangles
    bpy.ops.object.modifier_apply(modifier=modifier.name)
for face in mesh.data.polygons: face.use_smooth = True
if version=='v6': mesh.data.normals_split_custom_set([(0,0,0)]*len(mesh.data.loops))
mesh.data.calc_loop_triangles()
triangles = len(mesh.data.loop_triangles)

# Each mascot has its own proportions rather than a forced human template.
if character == 'baedoli':
    hip, chest, neck, head = .19, .35, .47, .63
    shoulder, elbow, hand = (.19, .40), (.32, .43), (.43, .50)
    head_limit, arm_limit = .48, .30
    if clean:
        shoulder, elbow, hand = (.18,.35),(.28,.27),(.34,.21)
        arm_limit=.215
elif character == 'hongdoli':
    hip, chest, neck, head = .19, .39, .58, .73
    shoulder, elbow, hand = (.33, .42), (.43, .43), (.51, .50)
    head_limit, arm_limit = .70, .37
else:
    hip, chest, neck, head = .46, .66, .77, .84
    shoulder, elbow, hand = (.14, .70), (.22, .56), (.30, .43)
    head_limit, arm_limit = .78, .14
    if character=='beodeuri' and version=='v6':
        shoulder,elbow,hand=(.105,.70),(.16,.56),(.215,.47)
        arm_limit=.115
    if character=='teacher' and version=='v6':
        shoulder,elbow,hand=(.10,.70),(.145,.56),(.18,.45)
        arm_limit=.10

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
rig = bpy.context.object
rig.name = character + '_GuideRig'
rig.data.name = character + '_Skeleton'
rig.data.edit_bones.remove(rig.data.edit_bones[0])
def bone(name, start, end, parent=None):
    b = rig.data.edit_bones.new(name)
    b.head, b.tail = Vector(start) * H, Vector(end) * H
    if parent: b.parent = rig.data.edit_bones[parent]
    return b
bone('Root', (0, 0, 0), (0, 0, .08))
bone('Hips', (0, 0, hip), (0, 0, hip + .08), 'Root')
bone('Spine', (0, 0, hip + .08), (0, 0, chest), 'Hips')
bone('Chest', (0, 0, chest), (0, 0, neck), 'Spine')
bone('Neck', (0, 0, neck), (0, 0, head), 'Chest')
bone('Head', (0, 0, head), (0, 0, .96), 'Neck')
for suffix, sign in [('R', -1), ('L', 1)]:
    sx, sz = shoulder; ex, ez = elbow; hx, hz = hand
    bone('UpperArm.' + suffix, (sign * sx, 0, sz), (sign * ex, -.02, ez), 'Chest')
    bone('Forearm.' + suffix, (sign * ex, -.02, ez), (sign * hx, -.035, hz), 'UpperArm.' + suffix)
    bone('Hand.' + suffix, (sign * hx, -.035, hz), (sign * (hx + .04), -.035, hz + (-.05 if clean else .035)), 'Forearm.' + suffix)
    x = .09 if not mascot else .13
    knee = .25 if not mascot else .11
    bone('Thigh.' + suffix, (sign * x, 0, hip), (sign * x, 0, knee), 'Hips')
    bone('Shin.' + suffix, (sign * x, 0, knee), (sign * x, 0, .055), 'Thigh.' + suffix)
    bone('Foot.' + suffix, (sign * x, 0, .055), (sign * x, -.11, .04), 'Shin.' + suffix)
if character == 'hongdoli':
    bone('Tail', (0, .09, .48), (.24, .23, .74), 'Chest')
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front = True
mesh.parent = rig
mod = mesh.modifiers.new('Guide_skin', 'ARMATURE'); mod.object = rig

coords = np.empty(len(mesh.data.vertices) * 3, dtype=np.float32)
mesh.data.vertices.foreach_get('co', coords)
coords = coords.reshape(-1, 3) / H
x, y, z = coords.T
weights = {b.name: np.zeros(len(coords), dtype=np.float32) for b in rig.data.bones}
def blend_z(mask, lower, upper, center, spread):
    t = np.clip((z[mask] - center + spread) / (2 * spread), 0, 1)
    weights[lower][mask] = 1 - t; weights[upper][mask] = t
if mascot:
    mask = z >= .19
    blend_z(mask, 'Chest', 'Head', .47 if character == 'baedoli' else .58, .07)
else:
    weights['Hips'][z < .52] = 1
    blend_z((z >= .52) & (z < .65), 'Spine', 'Chest', .585, .065)
    blend_z(z >= .65, 'Chest', 'Head', .765, .025)
    # Long hair follows the head; feet and skirt remain grounded.
    if character == 'beodeuri':
        mask = (y > .055) & (z > .52)
        for w in weights.values(): w[mask] = 0
        weights['Head'][mask] = 1
        weights['Hips'][z < .49] = 1

# Limb assignment uses restricted body regions, then smooth capsule weights.
def segment_distance(a, b):
    a, b = np.array(a), np.array(b)
    delta = b - a
    t = np.clip(((coords - a) @ delta) / np.dot(delta, delta), 0, 1)
    return np.linalg.norm(coords - (a + t[:, None] * delta), axis=1)
for suffix, sign in [('R', -1), ('L', 1)]:
    mask = (x * sign > arm_limit) & (z > (.15 if clean else .29 if mascot else .35)) & (z < (.43 if clean else .73 if mascot else .76))
    if character == 'baedoli' and not clean:
        mask &= (z < .55) | (x * sign > .36) | ((sign == 1) & (y < -.13) & (x > .28))
    names = ['UpperArm.' + suffix, 'Forearm.' + suffix, 'Hand.' + suffix]
    d = np.stack([segment_distance(tuple(rig.data.bones[n].head_local / H), tuple(rig.data.bones[n].tail_local / H)) for n in names], axis=1)
    arm_weight = np.exp(-d[mask] / .018)
    arm_weight /= np.maximum(arm_weight.sum(axis=1, keepdims=True), 1e-12)
    edge = np.clip((x[mask] * sign - arm_limit) / .045, 0, 1)
    for w in weights.values(): w[mask] *= 1 - edge
    for i, n in enumerate(names): weights[n][mask] += arm_weight[:, i] * edge
    if character=='beodeuri' and version=='v6':
        glove=(x*sign>.18)&(z>.37)&(z<.50)
        for w in weights.values():w[glove]=0
        weights['Hand.'+suffix][glove]=1
    if character=='teacher' and version=='v6':
        glove=(x*sign>.14)&(z>.35)&(z<.50)
        for w in weights.values():w[glove]=0
        weights['Hand.'+suffix][glove]=1
    if clean:
        # Finger silhouettes are rigid; the blend ends at the wrist.
        glove=mask&(x*sign>.30)&(z<.265)
        for w in weights.values():w[glove]=0
        weights['Hand.'+suffix][glove]=1
    if character != 'beodeuri':
        leg = (x * sign >= 0) & (z < (hip if not mascot else .19))
        if clean:leg &= np.abs(x)<.22
        if character=='teacher' and version=='v6':leg &= np.abs(x)<.115
        for w in weights.values(): w[leg] = 0
        foot = leg & (z < .09)
        weights['Foot.' + suffix][foot] = 1
        shin = leg & ~foot
        blend_z(shin, 'Shin.' + suffix, 'Thigh.' + suffix, .25 if not mascot else .12, .035)
if clean:
    # Hat and pear head have no influence from arm bones, regardless of material.
    for w in weights.values():w[z>.43]=0
    weights['Head'][z>.43]=1
if character=='beodeuri' and version=='v6':
    skirt=(z<.38)|((z<.515)&(np.abs(x)<.15))
    for w in weights.values():w[skirt]=0
    weights['Hips'][skirt]=1
if character=='teacher' and version=='v6':
    pants=(z>.26)&(z<.49)&(np.abs(x)<.115)
    for w in weights.values():w[pants]=0
    weights['Hips'][pants]=1
if character == 'hongdoli':
    mask = (y > .13) & (z > .42)
    for w in weights.values(): w[mask] = 0
    weights['Tail'][mask] = 1
total = sum(weights.values())
weights['Hips'][total < 1e-5] = 1
total = sum(weights.values())
for name, w in weights.items():
    group = mesh.vertex_groups.new(name=name)
    w /= total
    for index in np.flatnonzero(w > .001): group.add([int(index)], float(w[index]), 'REPLACE')
assert np.all(np.isfinite(total)) and np.all(total > 0)

scene = bpy.context.scene; scene.render.fps = 24
CLIPS = {'Idle': 5, 'Greeting': 3.2, 'Explain': 5.6, 'Nod': 2.6, 'Listen': 4}
def rotate(name, angles):
    pb = rig.pose.bones[name]
    orientation = rig.data.bones[name].matrix_local.to_quaternion()
    q = Quaternion()
    for axis, angle in zip([(1, 0, 0), (0, 1, 0), (0, 0, 1)], angles): q = Quaternion(axis, angle) @ q
    pb.rotation_quaternion = orientation.inverted() @ q @ orientation
for clip, duration in CLIPS.items():
    rig.animation_data_create()
    action = bpy.data.actions.new(clip); rig.animation_data.action = action
    frames = round(duration * 24)
    for frame in sorted(set([*range(1, frames + 1, 2), frames + 1])):
        t = (frame - 1) / frames
        pulse = math.sin(2 * math.pi * t)
        envelope = math.sin(math.pi * t) ** 2
        for pb in rig.pose.bones:
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
        rotate('Spine', (.004 * pulse, 0, .006 * pulse))
        rotate('Chest', (.007 * pulse, 0, -.004 * pulse))
        rotate('Head', (.008 * pulse, .012 * pulse, 0))
        for suffix in ('R', 'L'):
            rest = 0 if mascot else (-.17 if suffix == 'R' else .17)
            rotate('UpperArm.' + suffix, (.01 * pulse, rest, .006 * pulse))
        if clip == 'Greeting':
            amplitude = .12 if mascot else .20 if character=='teacher' and version=='v6' else .48
            rotate('UpperArm.R', (-.10 * envelope, amplitude * envelope, .04 * envelope))
            rotate('Forearm.R', (-.10 * envelope, .16 * envelope, .10 * math.sin(8 * math.pi * t) * envelope))
            rotate('Hand.R', (0, 0, .12 * math.sin(8 * math.pi * t) * envelope))
            rotate('Head', (.025 * envelope, 0, -.018 * envelope))
        elif clip == 'Explain':
            gesture = .5 - .5 * math.cos(4 * math.pi * t)
            rotate('UpperArm.R', (-.10 * gesture, (0 if mascot else -.17) + .10 * gesture, -.025 * pulse))
            rotate('Forearm.R', (-.10 * gesture, .08 * gesture, .045 * pulse))
            rotate('Head', (.025 * gesture, .025 * pulse, .008 * pulse))
            rotate('Chest', (.010 * pulse, 0, .012 * pulse))
        elif clip == 'Nod':
            rotate('Head', (.09 * (math.sin(4 * math.pi * t) ** 2) * envelope, 0, 0))
        elif clip == 'Listen':
            rotate('Head', (.015 * pulse, .014 * pulse, .025 * math.sin(2 * math.pi * t)))
        if character == 'hongdoli': rotate('Tail', (0, .024 * pulse, .035 * pulse))
        for pb in rig.pose.bones: pb.keyframe_insert(data_path='rotation_quaternion', frame=frame, group=pb.name)
    track = rig.animation_data.nla_tracks.new(); track.name = clip
    strip = track.strips.new(clip, 1, action); strip.action_frame_start = 1; strip.action_frame_end = frames + 1
    track.mute = True
rig.animation_data.action = None
for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0)
scene.frame_set(1)
textures = []
for image in bpy.data.images:
    if image.type != 'IMAGE': continue
    if not image.packed_file: image.pack()
    textures.append({'name': image.name, 'source_size': list(image.size)})
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
# Keep 4K editable textures in the blend; only the web export uses 2K images.
for image in bpy.data.images:
    if image.type == 'IMAGE' and max(image.size) > 2048:
        image.scale(2048, 2048); image.pack()
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); mesh.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(web), export_format='GLB', use_selection=True,
    export_animations=True, export_animation_mode='NLA_TRACKS', export_nla_strips=True,
    export_force_sampling=True, export_skins=True, export_all_influences=False)
shutil.copyfile(web, out / f'{character}-rigged-{version}.glb')
report = {'character': character, 'height_m': H, 'original_triangles': original_triangles,
          'web_triangles': triangles, 'bones': len(rig.data.bones), 'clips': CLIPS,
          'web_bytes': web.stat().st_size, 'textures': textures,
          'rigging': 'Blender region-guide custom skeleton and smooth skin weights',
          'facial_lipsync': False, 'feet_animated': False, 'original_preserved': True}
(out / 'rig-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('NPC_RIG_COMPLETE ' + json.dumps(report), flush=True)
