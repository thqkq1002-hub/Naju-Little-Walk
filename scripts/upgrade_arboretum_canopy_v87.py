"""Editable canopy revision from saved v74; no artist file or world replacement.

Photographs guide crown closure and understory. Platanus location is an explicit
interpretation of the user's reference, not a verified current tree inventory.
"""
import ast, bpy, hashlib, json, math, random, sys
import numpy as np
from pathlib import Path
from mathutils import Vector

R = Path(__file__).resolve().parents[1]
O = R / 'outputs/quality-v87'
O.mkdir(parents=True, exist_ok=True)
SOURCE = R / 'outputs/quality-v74/naju-arboretum-tree-crowns-v74.blend'
TARGET = O / 'naju-arboretum-canopy-v87-r2.blend'
if TARGET.exists():
    raise RuntimeError('Saved artist revision exists; choose a new revision')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
tree = ast.parse((R / 'scripts/arboretum_botanical_finish.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PlantMesh'], type_ignores=[]), '<PlantMesh>', 'exec'))

def fingerprint(o):
    m = o.data
    v = np.empty(len(m.vertices)*3, np.float32); m.vertices.foreach_get('co', v)
    ids = np.empty(len(m.loops), np.int32); m.loops.foreach_get('vertex_index', ids)
    lengths = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get('loop_total', lengths)
    return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world, np.float64).tobytes()).hexdigest()

changed = [o for o in scene.objects if o.type == 'MESH' and o.get('reference_habit') in ['meta', 'broad', 'broad2']]
names = {o.name for o in changed}
protected = {o.name: fingerprint(o) for o in scene.objects if o.type == 'MESH' and o.name not in names}
old = {(o['reference_habit'], o['vegetation_lod'], int(o['tree_crown_variant'])): o.data for o in changed}
world = json.loads((R / 'public/naju-arboretum-world.json').read_text(encoding='utf-8'))
geometry = json.loads((R / 'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'))
extent = json.loads((R / 'knowledge/sources/arboretum/satellite-export.json').read_text())['extent']

def px(u, v):
    x = extent['xmin']+(extent['xmax']-extent['xmin'])*u/1600
    y = extent['ymax']-(extent['ymax']-extent['ymin'])*v/1200
    return ((x/6378137*180/math.pi-126.8256689)*111320*math.cos(math.radians(35.00648)), -(math.atan(math.sinh(y/6378137))*180/math.pi-35.00648)*111320)

paths = []
for w in geometry['ways']:
    if w['tags'].get('highway'):
        paths.extend(zip(w['points'], w['points'][1:]))
for trace in json.loads((R / 'knowledge/sources/arboretum/detail-traces.json').read_text())['traces']:
    if 'walk' in trace['name'] or 'connection' in trace['name']:
        points = [px(*a) for a in trace['pixels']]; paths.extend(zip(points, points[1:]))

def nearest_path(x, z):
    best = (float('inf'), (x, z))
    for a, b in paths:
        dx, dz = b[0]-a[0], b[1]-a[1]
        t = max(0, min(1, ((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
        point = (a[0]+t*dx, a[1]+t*dz)
        distance = math.hypot(x-point[0], z-point[1])
        if distance < best[0]: best = distance, point
    return best

def inside(x, z, p):
    hit = False
    for a, b in zip(p, p[1:]+p[:1]):
        if (a[1]>z) != (b[1]>z) and x < (b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]: hit = not hit
    return hit

def local(s, t): return (-475+.98*s-.2*t, -50+.2*s+.98*t)
def st(x, z): return ((.98*(x+475)+.2*(z+50))/1.0004, (-.2*(x+475)+.98*(z+50))/1.0004)

# Analytic leaf silhouettes: true simple palmate leaves for Platanus; distinct
# opposite needle sprays for metasequoia. Original drawings, not photo textures.
N = 768
Y, X = np.mgrid[0:N, 0:N]/(N-1)

def polygon_mask(points):
    mask = np.zeros((N, N), bool)
    for a, b in zip(points, points[1:]+points[:1]):
        if abs(b[1]-a[1]) < 1e-10: continue
        mask ^= ((a[1]>Y) != (b[1]>Y)) & (X < (b[0]-a[0])*(Y-a[1])/(b[1]-a[1])+a[0])
    return mask

def line_mask(a, b, width):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = np.clip(((X-a[0])*dx+(Y-a[1])*dy)/(dx*dx+dy*dy or 1), 0, 1)
    return (X-a[0]-t*dx)**2+(Y-a[1]-t*dy)**2 < width**2

def leaf_atlas(kind):
    rr = random.Random({'meta':8701,'plane':8702,'mixed':8703}[kind])
    rgb = np.zeros((N, N, 3), np.float32); alpha = np.zeros((N, N), np.float32)
    palmate = [(0,-.45),(-.17,-.32),(-.43,-.38),(-.31,-.15),(-.57,.04),(-.31,.13),(-.33,.37),(-.12,.23),(0,.58),(.12,.23),(.33,.37),(.31,.13),(.57,.04),(.31,-.15),(.43,-.38),(.17,-.32)]
    def put(mask, color):
        nonlocal rgb, alpha
        grain = .94+.045*np.sin(X*291+Y*187)+.04*np.cos(X*117-Y*91)
        for k,c in enumerate(color): rgb[:,:,k][mask] = (grain*c)[mask]
        alpha[mask] = 1
    # Frond/leaf clusters have irregular outline but an opaque leafy interior;
    # holes remain between their lobed edges rather than entire thin crowns.
    count = 60 if kind == 'meta' else 43
    for j in range(count):
        a = rr.random()*math.tau; radius = math.sqrt(rr.random())*.33
        cx, cy = .5+radius*math.cos(a), .5+radius*math.sin(a)
        angle = rr.random()*math.tau; u = np.array([math.cos(angle), math.sin(angle)]); v = np.array([-u[1],u[0]])
        color = tuple(c*rr.uniform(.80,1.13) for c in ((.30,.43,.16) if kind=='plane' else (.22,.35,.105) if kind=='meta' else (.25,.38,.115)))
        if kind == 'meta':
            length = rr.uniform(.16,.29)
            a0 = np.array([cx,cy])-u*length*.5; a1 = a0+u*length
            mask = line_mask(a0,a1,.0012)
            for k in range(12):
                t = .07+k*.075; base = a0+u*length*t; reach = length*.30*math.sin((k+1)/14*math.pi)**.45
                for sign in [-1,1]:
                    tip = base+v*sign*reach+u*length*.10
                    pts = [base.tolist(), (tip-u*.006).tolist(), (tip+u*.006).tolist()]
                    mask |= polygon_mask(pts)
        else:
            scale = rr.uniform(.105,.175)
            if kind=='plane':
                pts = [(np.array([cx,cy])+u*q[1]*scale+v*q[0]*scale).tolist() for q in palmate]
            else:
                pts = [(np.array([cx,cy])+u*math.sin(k*math.tau/16)*scale*.6+v*math.cos(k*math.tau/16)*scale*.30*(.93+.07*(-1)**k)).tolist() for k in range(16)]
            mask = polygon_mask(pts)
            mid = np.array([cx,cy]); base = mid-u*scale*.42
            veins = line_mask(base, mid+u*scale*.46, .0011)
            for k in [-1,1]:
                veins |= line_mask(base+u*scale*.17, mid+v*k*scale*.4, .0008)
            put(mask, color)
            put(mask & veins, tuple(c*1.22 for c in color))
            continue
        put(mask, color)
    rgba = np.ones((N,N,4),np.float32); rgba[:,:,:3]=rgb; rgba[:,:,3]=alpha
    image = bpy.data.images.new('Authored_'+kind+'_canopy_atlas_v87',width=N,height=N,alpha=True)
    image.pixels.foreach_set(rgba.ravel()); image.pack()
    mat = bpy.data.materials.new('Canopy_'+kind+'_MASK_v87'); mat.use_nodes=True; mat.use_backface_culling=False; mat.surface_render_method='DITHERED'
    bs = mat.node_tree.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value=.83
    bs.inputs['Specular IOR Level'].default_value=.18
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']); mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
    return mat

leaves = {kind:leaf_atlas(kind) for kind in ['meta','plane','mixed']}

def bark(kind):
    mat = old['meta' if kind=='meta' else 'broad','near',0].materials[0].copy(); mat.name='Canopy_'+kind+'_bark_v87'
    if kind != 'plane': return mat
    n=512; y,x=np.mgrid[0:n,0:n]/n
    cells=np.sin(x*31+np.sin(y*17)*2)+np.cos(y*39+np.sin(x*21)*2)
    colors=np.array([(.39,.40,.30),(.52,.52,.39),(.69,.66,.52),(.79,.77,.64)],np.float32)
    level=np.clip(((cells+2)/4*4).astype(int),0,3)
    rgba=np.ones((n,n,4),np.float32);rgba[:,:,:3]=colors[level]*(.96+.04*np.sin(x*287))[...,None]
    image=bpy.data.images.new('Authored_plane_mottled_bark_v87',width=n,height=n);image.pixels.foreach_set(rgba.ravel());image.pack()
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
    bs=mat.node_tree.nodes['Principled BSDF'];mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.92
    for node in mat.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.14
    return mat

barks={kind:bark(kind) for kind in leaves}

def copy_wood(p,m):
    for f in m.polygons:
        if f.material_index==0:
            p.face([(m.vertices[i].co.x,m.vertices[i].co.z,-m.vertices[i].co.y) for i in f.vertices],0,[tuple(m.uv_layers.active.data[i].uv) for i in f.loop_indices])

def card(p,c,d,width,height,roll,segments=2):
    c=Vector(c);axis=Vector(d).normalized();u=axis.cross(Vector((0,1,0)))
    if u.length<.01:u=axis.cross(Vector((1,0,0)))
    u.normalize();v=axis.cross(u).normalized();side=u*math.cos(roll)+v*math.sin(roll);normal=axis.cross(side)
    for k in range(segments):
        a=k/segments;b=(k+1)/segments
        def row(t):
            center=c+axis*height*(t-.5)+normal*math.sin(t*math.pi)*height*.13
            return center-side*width*.5,center+side*width*.5
        low,high=row(a),row(b);p.face([low[0],low[1],high[1],high[0]],1,[(0,a),(1,a),(1,b),(0,b)])

def build(habit,kind,lod,variant):
    p=PlantMesh();copy_wood(p,old[habit,lod,variant]);rr=random.Random(8781+variant*31+{'meta':0,'plane':200,'mixed':500}[kind]);near=lod=='near'
    if kind=='meta':
        for tier in range(13):
            y=6.1+tier*.94;spread=4.9*(1-tier/14.2)**.64
            for j in range(5):
                a=j*math.tau/5+tier*1.15+variant*.25
                start=Vector((0,y,0));end=Vector((spread*math.cos(a),y+.35,spread*math.sin(a)))
                p.tube(start.lerp(end,.60),end,.026,.004,0,n=4 if near else 3)
                for k in range(4 if near else 2):
                    c=start.lerp(end,.45+k*(.17 if near else .47))
                    c+=Vector((rr.uniform(-.35,.35),rr.uniform(-.25,.3),rr.uniform(-.35,.35)))
                    for q in range(3 if near else 2):
                        theta=a+q*1.45+rr.uniform(-.35,.35)
                        card(p,c,(math.cos(theta),rr.uniform(-.4,.75),math.sin(theta)),rr.uniform(1.65,2.05)*(1 if near else 1.15),rr.uniform(1.3,1.7)*(1 if near else 1.15),rr.random()*math.tau,2 if near else 1)
    else:
        rx,ry,rz=(4.15,2.75,3.8) if kind=='plane' else (3.5,2.65,3.25)
        cy=6.65 if kind=='plane' else 6.3
        # Fibonacci shell and inner layers give depth without opaque polygon blobs.
        for j in range(150 if near else 84):
            t=(j+.5)/(150 if near else 84);yy=1-2*t;a=j*2.399+variant*.47;radius=math.sqrt(1-yy*yy)
            shell=.72 if j%4==0 else 1
            c=Vector((math.cos(a)*radius*rx*shell,cy+yy*ry*shell,math.sin(a)*radius*rz*shell))
            center=Vector((0,4.3,0));p.tube(center.lerp(c,.66),c,.013,.002,0,n=3)
            for k in range(3 if near else 2):
                angle=a+k*1.3+rr.uniform(-.5,.5)
                card(p,c,(math.cos(angle),rr.uniform(-.7,.8),math.sin(angle)),rr.uniform(1.8,2.5)*(1 if near else 1.2),rr.uniform(1.5,2.1)*(1 if near else 1.2),rr.random()*math.tau,2 if near else 1)
    mesh=p.finish('Canopy_'+habit+'_'+kind+'_'+lod+'_v87_'+str(variant),[barks[kind],leaves[kind]])
    mesh.calc_loop_triangles();print('CROWN',mesh.name,len(mesh.loop_triangles),flush=True);return mesh

protos={}
placements={};counts={}
for o in changed:
    habit=o['reference_habit'];lod=o['vegetation_lod'];x,z=o.location.x,-o.location.y
    distance,_=nearest_path(x,z);s,t=st(x,z)
    # Select existing broadleaf trees beside mapped routes, not central meta rows.
    kind='meta' if habit=='meta' else 'plane' if distance<=19 and 24<s<395 and abs(t)>12 else 'mixed'
    variant=int(hashlib.sha256(','.join(str(round(a,3)) for a in o.location).encode()).hexdigest()[:8],16)%3
    key=(habit,kind,lod,variant)
    if key not in protos:protos[key]=build(*key)
    placements[o.name]=dict(habit=habit,lod=lod,kind=kind,variant=variant,matrix=[a for row in o.matrix_world for a in row],original_mesh=o.data.name,path_distance=round(distance,2),position=[x,z])
    o.data=protos[key];o['tree_crown_revision']='Photo-informed canopy v87; roots retained; Platanus positions interpreted, not inventoried';o['tree_crown_variant']=variant;o['canopy_form']=kind
    counts[kind+'_'+lod]=counts.get(kind+'_'+lod,0)+1

# Mondo/Liriope-form, low strappy leaves. Four shared mound meshes, paired LODs.
# No extra tree roots, walls or terrain; all collision geometry stays unchanged.
ground_material=bpy.data.materials.new('Mondo_layered_green_v87');ground_material.use_nodes=True
bs=ground_material.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.13,.255,.052,1);bs.inputs['Roughness'].default_value=.91;ground_material.use_backface_culling=False
ground_protos={}
for lod in ['near','far']:
    for variant in range(3):
        p=PlantMesh();rr=random.Random(8790+variant)
        for j in range(42 if lod=='near' else 18):
            a=rr.random()*math.tau;rad=rr.uniform(0,.36);height=rr.uniform(.22,.42);reach=rr.uniform(.25,.46)
            origin=Vector((math.cos(a)*rad,.018,math.sin(a)*rad));side=Vector((-math.sin(a),0,math.cos(a)))
            for k in range(3 if lod=='near' else 2):
                start=k/(3 if lod=='near' else 2);end=(k+1)/(3 if lod=='near' else 2)
                def tip(t):return origin+Vector((math.cos(a)*reach*t,height*math.sin(t*math.pi*.65),math.sin(a)*reach*t))
                width=.026 if lod=='near' else .05
                p.face([tip(start)-side*width*(1-start),tip(start)+side*width*(1-start),tip(end)+side*width*(1-end),tip(end)-side*width*(1-end)],0)
        ground_protos[lod,variant]=p.finish('Mondo_tuft_'+lod+'_v87_'+str(variant),[ground_material])

campus=next(w['points'] for w in geometry['ways'] if w['id']=='1306096596')
obstacles=[a['footprint'] for a in world['solids'] if a.get('footprint') and (a.get('collision') or a['name'].startswith(('flower_bed','ground_','water_')) and a['name']!='ground_campus_osm')]
ground=[];rr=random.Random(87087);occupied=set()
def add_ground(x,z,region):
    if not inside(x,z,campus):return
    distance,_=nearest_path(x,z)
    if distance<2.4 or any(inside(x,z,p) for p in obstacles):return
    cell=(round(x/.6),round(z/.6))
    if cell in occupied:return
    occupied.add(cell);variant=rr.randrange(3);scale=rr.uniform(.85,1.25);rot=rr.random()*math.tau
    ground.append(dict(position=[x,z],path_distance=distance,region=region,variant=variant,scale=scale,rotation=rot))
    for lod in ['near','far']:
        o=bpy.data.objects.new(('distant_' if lod=='far' else '')+'verge_mondo_v87_'+str(len(ground)),ground_protos[lod,variant]);scene.collection.objects.link(o)
        o.location=(x,-z,.022);o.scale=(scale,scale,scale);o.rotation_euler.z=rot
        o['authored_vegetation']=True;o['vegetation_lod']=lod;o['vegetation_distance']=32;o['reference_habit']='groundcover';o['canopy_revision']='v87';o.hide_render=lod=='far'
for s in np.arange(14,424,.90):
    for t in [-6.7,-5.7,5.7,6.7]:
        add_ground(*local(s+rr.uniform(-.18,.18),t+rr.uniform(-.16,.16)),'avenue')
for o in changed:
    if o['vegetation_lod']!='near' or o['reference_habit']=='meta':continue
    x,z=o.location.x,-o.location.y;distance,_=nearest_path(x,z)
    if distance>14:continue
    for k in range(5):
        angle=k*math.tau/5+rr.random()*.6;radius=rr.uniform(.9,1.7)
        add_ground(x+math.cos(angle)*radius,z+math.sin(angle)*radius,'side-grove')

report=dict(source=str(SOURCE.relative_to(R)),output=str(TARGET.relative_to(R)),changed_objects=placements,protected_geometry_hashes=protected,world_sha256=hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest(),counts=counts,shared_prototypes=len(protos),triangles={m.name:len(m.loop_triangles) for m in protos.values()},groundcover=ground,groundcover_clearance=2.4,groundcover_prototypes=6,reference='https://hangamja.tistory.com/1607',reference_published='2021-06-13',limitations=['Official central avenue retained as metasequoia. Path-side Platanus forms are user-directed interpretation; exact current tree inventory and planting dimensions unverified.','Groundcover positions are interpreted within existing path clearances. No terrain implementation or new tree roots.'])
(R/'knowledge/sources/arboretum/canopy-v87.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(O/'naju-arboretum-v87-r2.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('CANOPY EXPORTED',counts,'groundcover',len(ground),flush=True)
