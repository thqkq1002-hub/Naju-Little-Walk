"""Shared Blender helpers for the Naju character NPCs.

Authoring space matches MuseumGeometry: x right, y up, z depth. A character's
front is local -Z, so the app can apply its yaw directly as rotation.y.
"""
import bpy, math, sys, gzip, json
from pathlib import Path
from mathutils import Vector
from museum_geometry import MuseumGeometry

ROOT = Path(__file__).resolve().parents[1]

def new_scene(name):
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    return scene, MuseumGeometry(scene, center=(0, 0), angle=0)

def ellipsoid(g, name, x, y, z, rx, ry, rz, color, rings=14, segments=20, roll=0, pitch=0):
    cr, sr, cp, sp = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch)
    verts = []
    for j in range(rings + 1):
        v = j / rings * math.pi
        for i in range(segments):
            u = i / segments * math.tau
            px, py, pz = rx * math.sin(v) * math.cos(u), ry * math.cos(v), rz * math.sin(v) * math.sin(u)
            py, pz = py * cp - pz * sp, py * sp + pz * cp
            px, py = px * cr - py * sr, px * sr + py * cr
            verts.append((x + px, y + py, z + pz))
    faces = [(j * segments + i, j * segments + (i + 1) % segments, (j + 1) * segments + (i + 1) % segments, (j + 1) * segments + i) for j in range(rings) for i in range(segments)]
    return g.mesh(name, verts, faces, color, smooth=True)

def lathe(g, name, x, y, z, profile, color, sx=1, sz=1, n=32, flutes=0, flute_depth=.03, flute_top=None):
    """Revolve a (height, radius) profile. `flutes` adds vertical pleats that
    deepen toward the hem, which is what reads as fabric folds on a skirt."""
    top = flute_top if flute_top is not None else profile[-1][0]
    base = profile[0][0]
    verts = []
    for yy, r in profile:
        fade = 1 - max(0, min(1, (yy - base) / ((top - base) or 1)))
        for i in range(n):
            a = i * math.tau / n
            rr = r * (1 + flute_depth * fade * math.cos(flutes * a)) if flutes else r
            verts.append((x + math.cos(a) * rr * sx, y + yy, z + math.sin(a) * rr * sz))
    faces = [tuple(range(n)), tuple(range(len(profile) * n - n, len(profile) * n))]
    faces += [(j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i) for j in range(len(profile) - 1) for i in range(n)]
    return g.mesh(name, verts, faces, color, smooth=True)

def limb(g, name, points, radii, color, n=12, smoothing=2):
    """Smooth swept tube with a varying radius, for arms, legs and ribbons."""
    P, R = [Vector(p) for p in points], list(radii)
    for _ in range(2):
        nP, nR = [P[0]], [R[0]]
        for i in range(len(P) - 1):
            nP += [(P[i] + P[i + 1]) / 2, P[i + 1]]
            nR += [(R[i] + R[i + 1]) / 2, R[i + 1]]
        P, R = nP, nR
    for _ in range(smoothing):
        for i in range(1, len(P) - 1):
            P[i] = (P[i - 1] + P[i] * 2 + P[i + 1]) / 4
            R[i] = (R[i - 1] + R[i] * 2 + R[i + 1]) / 4
    verts = []
    for i, (p, r) in enumerate(zip(P, R)):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        t = t.normalized() if t.length > 1e-6 else Vector((0, 1, 0))
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        v = t.cross(u).normalized()
        verts += [tuple(p + r * (math.cos(k * math.tau / n) * u + math.sin(k * math.tau / n) * v)) for k in range(n)]
    faces = [tuple(range(n)), tuple(range(len(P) * n - n, len(P) * n))]
    faces += [(i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k) for i in range(len(P) - 1) for k in range(n)]
    return g.mesh(name, verts, faces, color, smooth=True)

def hand(g, name, wrist, forward, side, size, color, fingers=4, thumb=True, curl=.0, spread=.44):
    """Palm plus fingers swept along `forward`; `side` spreads them sideways."""
    w, f = Vector(wrist), Vector(forward).normalized()
    s = Vector(side).normalized()
    down = f.cross(s).normalized()
    knuckle = w + f * size * 1.05
    limb(g, f'{name}_palm', [w, w + f * size * .55, knuckle], [size * .60, size * .72, size * .70], color, n=12)
    for k in range(fingers):
        off = (k - (fingers - 1) / 2) * size * spread
        base = knuckle + s * off
        length = size * (.80 - abs(k - (fingers - 1) / 2) * .08)
        mid = base + f * length * .55 + down * curl * length * .45
        tip = mid + f * length * .45 + down * curl * length * .75
        limb(g, f'{name}_finger_{k}', [base, mid, tip], [size * .21, size * .19, size * .15], color, n=8)
        ellipsoid(g, f'{name}_fingertip_{k}', *tip, size * .15, size * .15, size * .15, color, rings=6, segments=8)
    if thumb:
        root = w + f * size * .28 - s * size * .48
        tip = root + (f * .5 - s * .8).normalized() * size * .85
        limb(g, f'{name}_thumb', [w - s * size * .2, root, tip], [size * .26, size * .24, size * .18], color, n=8)
        ellipsoid(g, f'{name}_thumbtip', *tip, size * .18, size * .18, size * .18, color, rings=6, segments=8)

def surface_z(cx, cy, cz, rx, ry, rz, x, y):
    t = 1 - ((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2
    return cz - rz * math.sqrt(max(t, 0))

def profile_radius(profile, y):
    for (y0, r0), (y1, r1) in zip(profile, profile[1:]):
        if y0 <= y <= y1:
            return r0 + (r1 - r0) * (y - y0) / ((y1 - y0) or 1)
    return profile[-1][1]

def eye(g, tag, cx, cy, cz, rx, ry, rz, x, y, size, color='#191412'):
    z = surface_z(cx, cy, cz, rx, ry, rz, x, y) - .004
    ellipsoid(g, f'{tag}_eye_white', x, y, z, size * .95, size * 1.15, size * .35, '#fbfbf4', rings=8, segments=12)
    ellipsoid(g, f'{tag}_pupil', x, y - size * .05, z - size * .12, size * .68, size * .85, size * .3, color, rings=8, segments=12)
    ellipsoid(g, f'{tag}_glint', x + size * .2, y + size * .3, z - size * .25, size * .22, size * .22, size * .12, '#ffffff', rings=6, segments=8)

def arc(g, name, points, r, color):
    for i, (a, b) in enumerate(zip(points, points[1:])):
        g.tube(f'{name}_{i}', a, b, r, color, n=6)

def finish(scene, g, slug, height, render=False):
    outputs = ROOT / 'outputs'
    outputs.mkdir(exist_ok=True)
    (ROOT / 'public' / 'models').mkdir(parents=True, exist_ok=True)
    bpy.ops.object.camera_add(location=g.bp(height * .55, height * .62, -height * 2.3))
    camera = bpy.context.object
    camera.name = f'{slug}_preview_camera'
    camera.rotation_euler = (Vector(g.bp(0, height * .5, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 45
    scene.camera = camera
    bpy.ops.object.light_add(type='SUN', location=(-2, 3, 3))
    sun = bpy.context.object
    sun.rotation_euler = (math.radians(50), 0, math.radians(-160))
    sun.data.energy = 3.2
    scene.world = bpy.data.worlds.new(f'{slug}_daylight')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.72, .82, .88, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .9
    names = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in names else 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 800; scene.render.resolution_y = 1000
    scene.render.filepath = str(outputs / f'{slug}-preview.png')
    scene.view_settings.view_transform = 'AgX'
    blend = outputs / f'{slug}.blend'
    if blend.exists():
        blend.unlink()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), copy=True)
    glb = ROOT / 'public' / 'models' / f'{slug}.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_active_scene=True, export_cameras=False, export_lights=False, export_extras=True, export_apply=True)
    glb.with_suffix('.glb.gz').write_bytes(gzip.compress(glb.read_bytes(), compresslevel=9, mtime=0))
    print(json.dumps({'slug': slug, 'objects': len(scene.objects), 'bytes': glb.stat().st_size}))
    if render:
        bpy.ops.render.render(write_still=True)
