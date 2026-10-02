"""Original Blender details observed in museum photos; dimensions are estimates.

No source photographs or movie frames are distributed as model textures.
"""
import bpy
import math
import random


def textured_material(g, color, name, grain=.07, banding=0):
    material = g.mat(color)
    image = bpy.data.images.new(name, width=256, height=256)
    rgb = [int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)]
    rng = random.Random(name)
    pixels = []
    for y in range(256):
        for x in range(256):
            coarse = .008*math.sin(x*.055+math.sin(y*.07))*math.cos(y*.04)
            noise = rng.uniform(-grain, grain)+coarse+banding*math.sin(y*.33)
            pixels.extend([max(0, min(1, c+noise)) for c in rgb]+[1])
    image.pixels = pixels
    image.pack()
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    material.node_tree.links.new(node.outputs['Color'], material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    return material


def materials(g):
    textured_material(g, '#c28c56', 'Original_ochre_fine_grain', .045)
    for color in ['#b9b5a8', '#aaa99e', '#989e99', '#c1bdad', '#929a99']:
        textured_material(g, color, 'Original_stone_'+color[1:], .075)
    for color in ['#bcb8a2', '#c8c4af', '#c9c2a9', '#65615a', '#615548', '#716551', '#968063', '#b18b63']:
        textured_material(g, color, 'Original_ceramic_'+color[1:], .035, .014)


def stone_wall(g, name, x, z, w, d, y, levels, rng, colors):
    """Staggered, interlocking dry masonry, with large flat coping slabs."""
    for level in range(levels):
        for side in (-1, 1):
            for axis, length in [('x', w), ('z', d)]:
                cursor = -length/2
                while cursor < length/2-.03:
                    span = min(rng.uniform(.32, .86), length/2-cursor)
                    mid = cursor+span/2
                    xx, zz = (x+mid, z+side*d/2) if axis == 'x' else (x+side*w/2, z+mid)
                    height = .28+rng.uniform(-.035, .035)
                    sw, sd = (span-.014, .43) if axis == 'x' else (.43, span-.014)
                    g.rock(name+'_masonry', xx, y+.145+level*.285, zz, sw, height, sd, rng.choice(colors), rng)
                    cursor += span
    # Flat, broadly irregular capstones replace the uniformly rounded blocks.
    for side in (-1, 1):
        for k in range(max(2, int(w/.77))):
            count = max(2, int(w/.77))
            g.rock(name+'_capstone', x-w/2+(k+.5)*w/count, y+levels*.285+.06,
                   z+side*d/2, w/count-.02, .14, .53, rng.choice(colors), rng)
        count=max(2,int(d/.82))
        for k in range(count):
            g.rock(name+'_side_capstone',x+side*w/2,y+levels*.285+.055,
                   z-d/2+(k+.5)*d/count,.52,.14,d/count-.02,rng.choice(colors),rng)


def clipped(poly, a, b, c):
    result = []
    for p, q in zip(poly, poly[1:]+poly[:1]):
        dp, dq = a*p[0]+b*p[1]-c, a*q[0]+b*q[1]-c
        if dp <= 0: result.append(p)
        if (dp <= 0) != (dq <= 0):
            t = dp/(dp-dq)
            result.append([p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])])
    return result


def flagstone_floor(g, name, x, z, w, d, y, rng, colors):
    """Voronoi-cut fitted floor stones with narrow dark joints."""
    w = max(.4, w-.42); d = max(.4, d-.42)
    seeds = []
    nx, nz = max(2, math.ceil(w/.52)), max(2, math.ceil(d/.56))
    for j in range(nz):
        for i in range(nx):
            seeds.append([x-w/2+(i+rng.uniform(.2, .8))*w/nx,
                          z-d/2+(j+rng.uniform(.2, .8))*d/nz])
    g.box(name+'_joint_bed', x, y+.005, z, w, .025, d, '#555249', record=False)
    for i, p in enumerate(seeds):
        poly = [[x-w/2, z-d/2], [x+w/2, z-d/2], [x+w/2, z+d/2], [x-w/2, z+d/2]]
        for q in seeds:
            if p is q: continue
            a, b = q[0]-p[0], q[1]-p[1]
            poly = clipped(poly, a, b, (q[0]**2+q[1]**2-p[0]**2-p[1]**2)/2)
            if not poly: break
        poly = [[p[0]+(v[0]-p[0])*.965, p[1]+(v[1]-p[1])*.965] for v in poly]
        if len(poly) < 3: continue
        n = len(poly); top = y+.052+rng.uniform(-.01, .01)
        verts = [(xx, h, zz) for h in (y+.015, top) for xx, zz in poly]
        g.mesh(name+'_fitted_flagstone', verts, [tuple(range(n-1, -1, -1)), tuple(range(n, 2*n))]+
               [(k, (k+1)%n, (k+1)%n+n, k+n) for k in range(n)], rng.choice(colors), '03_Report_Burials')


def finish_hall(g, scene, burials, bridge, terrain):
    # Close the high main-hall / lower visitor-wing junction visible as blue sky.
    g.box('cutaway_south_closure', 0, 8.45, 23.65, 50.55, 4.4, .34, '#c9c6b9', True, group='05_Cutaway_Roof')
    for z in (-23.38, 23.35):
        g.segment('cutaway_wall_head_trim', [-25, z], [25, z], .22, .20, '#72766e', base=10.13, record=False, group='05_Cutaway_Roof')
    for z in range(-22, 24, 4):
        for x in range(-24, 23, 3):
            g.tube('cutaway_truss_crossbrace', (x, 10.23, z), (x+3, 9.69, z), .028, '#202826', '05_Cutaway_Roof')
            g.box('cutaway_truss_connector', x, 9.70, z, .17, .13, .20, '#49504a', group='05_Cutaway_Roof', record=False)
    for x in (-22, -11, 0, 11, 22):
        g.box('cutaway_cable_tray', x, 10.08, 0, .22, .07, 46, '#252d2c', group='05_Cutaway_Roof', record=False)
    # Dark backing makes the exposed steelwork read as an enclosed exhibition hall.
    g.mat('#353b39').node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.007, .011, .010, 1)

    # Observed freestanding glazed site model in front of the replica (2024 photo).
    x, z = 8.8, 25.8
    g.box('site_model_case_plinth', x, .50, z, 3.5, .76, 1.65, '#d9ddd6', True)
    g.box('site_model_case_black_base', x, .16, z, 3.62, .08, 1.75, '#343b38', record=False)
    g.box('site_model_landscape', x, .92, z, 3.25, .10, 1.42, '#697c49', record=False)
    for i, (dx, dz, w, d) in enumerate([(-1, 0, .60, .56), (-.23, .1, .69, .50), (.57, -.05, .76, .63), (1.12, .30, .36, .40)]):
        g.rock('site_model_mound_'+str(i), x+dx, 1.02, z+dz, w, .19, d, '#819361', random.Random(i))
    for side in (-1, 1):
        g.box('site_model_case_glass', x, 1.18, z+side*.84, 3.57, .65, .012, '#92b2b4', record=False)
        g.box('site_model_case_glass_end', x+side*1.78, 1.18, z, .012, .65, 1.68, '#92b2b4', record=False)
    g.box('site_model_case_glass_top', x, 1.51, z, 3.57, .012, 1.68, '#92b2b4', record=False)
    g.label('복암리 고분군', x, .58, z+.84, 2.8, .19, color='#49564d')
    # Barrier stands along the replica apron; do not obstruct the existing stair.
    for i in range(7):
        xx = -15.0+i*3.15; zz = 23.72
        g.tube('replica_barrier_post', (xx, .13, zz), (xx, 1.02, zz), .022, '#949b96')
        g.tube('replica_barrier_base', (xx, .13, zz), (xx, .16, zz), .19, '#6a716c', n=24)
        if i < 6:
            g.segment('replica_barrier_belt', [xx, zz], [xx+3.15, zz], .026, .055, '#8a263b', base=.93, collision=True)
    # Close-fitting mullions and three-level shelf at the right of the long case.
    for z in [-2.8+i*2.6 for i in range(7)]:
        g.box('pottery_case_mullion', 21.83, 1.8, z, .03, 2.28, .028, '#9eaaa2', record=False)
    for y in (.68, 2.93):
        g.box('pottery_case_trim', 21.83, y, 5, .05, .055, 15.7, '#ada68a', record=False)
    for level in range(3):
        g.box('pottery_case_tier', 22.43+level*.16, .79+level*.22, 11.40, .80-level*.16, .18, 1.70, '#eee4d0', record=False)
        for k in range(3):
            g.vessel('pottery_tier_sample', 22.34+level*.16, .90+level*.22, 10.85+k*.53, .24+level*.04, '#968063')
    # Individual exhibit spotlights, aimed at selected replica chambers.
    for b in burials:
        if b['id'] not in ('S96', 'S12', 'S9', 'J6', 'J15'): continue
        x, z = b['model_center']; h = b['replica_floor']
        wx, wz = g.point(x, z)
        g.lights.append(dict(position=[wx, min(8.6, h+3.4), wz], color='#ffdfab', intensity=75, distance=7))
        data = bpy.data.lights.new('Burial_focus_'+b['id'], 'AREA'); data.energy=125; data.shape='DISK'; data.size=1.8
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj); obj.location=g.bp(x, h+3.4, z)
    return dict(revision='exhibition-detail-1', stonework='staggered courses, large coping slabs and fitted polygonal flagstones',
                envelope='upper south roof junction closed', sourceDates=['official photos: date unknown', 'visitor photographs: 2024', 'Gwangju MBC interior footage: 2016 and 2022'],
                limitations='All replica opening sizes, surface levels, fixture positions and unmeasured details remain estimated.')
