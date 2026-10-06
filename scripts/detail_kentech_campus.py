"""Photo-led facade/forecourt pass on the preserved v52 editable Blender scene.

New revision only. Mesh details are batched for web delivery; no source photos are
embedded. Window spacing, planting and paving modules remain interpretations.
"""
import bpy, bmesh, math, random, json, gzip, sys, re
from pathlib import Path
from mathutils import Vector

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'scripts'))
from museum_geometry import MuseumGeometry
from kentech_export import batch_and_export

O = R/'outputs/kentech'
target = O/'kentech-campus-v53.blend'
if target.exists():
    raise RuntimeError('Existing editable revision preserved; choose a new revision filename.')
bpy.ops.wm.open_mainfile(filepath=str(O/'kentech-campus-v52-final.blend'))
scene = bpy.context.scene
g = MuseumGeometry(scene, (0, 0), 0)
for m in bpy.data.materials:
    if re.fullmatch(r'Museum_[0-9a-fA-F]{6}', m.name):
        g.materials['#'+m.name[7:]] = m
rng = random.Random(530920)
worldpath = R/'public/bitgaram-kentech-world.json'
world = json.loads(worldpath.read_text(encoding='utf8'))
data = json.loads((R/'knowledge/sources/kentech-v52/geometry.json').read_text(encoding='utf8'))
ways = {w['id']: w for w in data}

def poly(id):
    pts = [((p[0]-126.803269)*91175, (35.010582-p[1])*111195) for p in ways[id]['points']]
    return pts[:-1] if pts[0] == pts[-1] else pts

def box(n,x,y,z,w,h,d,c,collision=False):
    return g.box(n,x,y,z,w,h,d,c,collision,record=collision)

def seg(n,a,b,w,h,c,y=0):
    return g.segment(n,a,b,w,h,c,y,record=False)

def extent(o):
    vs=[o.matrix_world @ v.co for v in o.data.vertices]
    return (min(v.x for v in vs),max(v.x for v in vs),-max(v.y for v in vs),-min(v.y for v in vs),min(v.z for v in vs),max(v.z for v in vs))

def ground(o):
    o['no_shadow']=True
    return o

def edge_path(n,pts,w,c='#c8c4b8',y=.137):
    for a,b in zip(pts,pts[1:]):
        ground(seg(n+'_stone_border',a,b,w+.22,.035,'#b9bdb1',y-.015))
        ground(seg(n,a,b,w,.022,c,y))

# Resolve duplicate road/footway interpretation before introducing smaller detail.
remove=[]
for o in list(scene.objects):
    if o.type!='MESH':continue
    if o.name.startswith(('campus_quad_path','campus_ground_main_plaza')):
        remove.append(o);continue
    if o.name.startswith(('campus_road_asphalt','campus_road_verge')):
        p=[o.matrix_world@v.co for v in o.data.vertices[:4]]
        width=min((p[i]-p[(i+1)%4]).length for i in range(4))
        is_foot=abs(width-(3 if o.name.startswith('campus_road_asphalt') else 6))<.02
        if is_foot:
            e=extent(o)
            if e[0]>-28 and e[1]<115 and e[2]>14 and e[3]<91:
                remove.append(o)
            else:
                o.data.materials[0]=g.mat('#c8c4b8' if width<4 else '#b9bdb1')
    if o.name.startswith(('entrance_canopy','entrance_recess_atrium','atrium_vertical_frame','atrium_horizontal_frame')):
        remove.append(o)
    if o.name.startswith('top_storey_white_fin'):
        e=extent(o)
        if e[0]>-30 and e[1]<114 and e[2]>-95 and e[3]<18:remove.append(o)
bpy.data.batch_remove(ids=remove)
print('DETAIL removed duplicate paving and simplified entrance parts',len(remove),flush=True)

# Quiet stone forecourt and a single connected network of diagonal paths.
ground(box('detail_forecourt_base',43,.070,23,146,.14,20,'#c8c4b8'))
tile_colors=['#d3d2c7','#dddcd1','#b9c9c4','#c8c4b8']
for ix in range(145):
    for iz in range(19):
        x=-29.5+ix;z=13.5+iz
        ground(box('detail_granite_paver',x,.145,z,.981,.016,.981,rng.choices(tile_colors,[50,15,7,28])[0]))
for zz in [13.2,32.8]:
    ground(seg('detail_forecourt_drain',(-29,zz),(115,zz),.15,.016,'#657275',.154))
    for x in range(-28,114):ground(box('detail_drain_slot',x,.164,zz,.026,.005,.13,'#345765'))
for pts,w,c in [([(-18,31),(-8,61),(8,87),(108,87)],3.5,'#d3d2c7'),
                ([(8,87),(39,32)],3.4,'#d3d2c7'),
                ([(108,32),(108,105),(270,105)],4,'#d3d2c7'),
                ([(5,107),(122,107),(272,107)],6,'#c8c4b8'),
                ([(122,104),(122,282)],6,'#c8c4b8'),
                ([(107,42),(132,14),(134,-24)],3,'#c8c4b8')]:
    edge_path('detail_campus_walk',pts,w,c)
    # Transverse joints only, spaced far enough to avoid distant aliasing.
    for a,b in zip(pts,pts[1:]):
        length=math.dist(a,b);dx=(b[0]-a[0])/length;dz=(b[1]-a[1])/length
        for i in range(1,int(length/2)):
            x=a[0]+dx*i*2;z=a[1]+dz*i*2
            ground(seg('detail_walk_expansion_joint',(x-dz*w/2,z+dx*w/2),(x+dz*w/2,z-dx*w/2),.014,.006,'#a8b5b5',.161))

print('DETAIL forecourt paving ready',len(scene.objects),flush=True)
cream='#dddcd1';frame='#455e63';glass=['#5f8890','#4c7279','#739497','#456970']
for color in glass:
    bs=g.mat(color).node_tree.nodes['Principled BSDF']
    bs.inputs['Metallic'].default_value=.32;bs.inputs['Roughness'].default_value=.22

# Pane-by-pane color, recessed spandrels, opening lights and deep white brise-soleil.
for id in ['1065747586','1201084332']:
    pts=poly(id)
    signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
    for a,b in zip(pts,pts[1:]+pts[:1]):
        ll=math.dist(a,b);dx=(b[0]-a[0])/ll;dz=(b[1]-a[1])/ll
        nx,nz=(dz,-dx) if signed>0 else (-dz,dx)
        n=max(1,round(ll/1.7))
        def point(t,offset=.105):return (a[0]+(b[0]-a[0])*t+nx*offset,a[1]+(b[1]-a[1])*t+nz*offset)
        for floor in range(1,4):
            y=floor*5.2
            seg('detail_recessed_spandrel',point(0,.085),point(1,.085),.12,.76,'#345765',y+.12)
            for j in range(n):
                aa=point((j+.055)/n);bb=point((j+.945)/n)
                seg('detail_glass_pane',aa,bb,.105,3.61,rng.choice(glass),y+.92)
                if (j+floor)%4==0:
                    # Window reveal surrounds a smaller dark opening sash.
                    seg('detail_opening_sash',aa,bb,.17,1.08,frame,y+.97)
                    seg('detail_sash_glass',point((j+.13)/n,.205),point((j+.87)/n,.205),.035,.88,'#345765',y+1.07)
                if floor==3:
                    p=point(j/n,.34)
                    seg('detail_deep_white_fin',(p[0]-nx*.12,p[1]-nz*.12),(p[0]+nx*.58,p[1]+nz*.58),.18,4.10,cream,y+.18)
            seg('detail_horizontal_sunshade',point(0,.31),point(1,.31),.86,.20,cream,y-.04)
        # Small grounding plinth improves the view at pedestrian height.
        if max(a[1],b[1])<9 or min(a[1],b[1])>17:
            seg('detail_facade_plinth',point(0,.10),point(1,.10),.24,.22,'#a8b5b5',.04)
        # Roof guardrail is visible above the solid parapet.
        for j in range(max(1,math.ceil(ll/2))+1):
            p=point(j/max(1,math.ceil(ll/2)),.05)
            g.tube('detail_roof_rail_post',(p[0],21.15,p[1]),(p[0],22.05,p[1]),.028,frame,n=5)
        for y in [21.65,22.05]:seg('detail_roof_guardrail',point(0,.05),point(1,.05),.04,.04,frame,y)

# Photo shows the western atrium stopping below the top storey, with two box canopies.
for x,z in [(-5,10.9),(84,15.5)]:
    if x<0:
        box('detail_atrium_glazing',x,10.1,z+.30,10.5,10,.24,'#345765')
        for dx in [-4.4,-2.9,-1.45,0,1.45,2.9,4.4]:
            for y in [6.4,8.5,10.6,12.7]:box('detail_atrium_pane',x+dx,y,z+.45,1.36,1.97,.08,rng.choice(glass))
        for y in [5.4,7.4,9.5,11.6,13.7,15.2]:box('detail_atrium_transom',x,y,z+.52,10.5,.085,.14,frame)
    box('detail_canopy_roof',x,3.68,z+2.2,8.4,.18,5.6,'#a8b5b5')
    for zz in [z-.58,z+4.98]:box('detail_canopy_box_beam',x,3.38,zz,8.4,.55,.22,'#596e71')
    for xx in [x-4.08,x+4.08]:box('detail_canopy_side_beam',xx,3.38,z+2.2,.22,.55,5.6,'#596e71')
    for dx in [-3,-2,-1,0,1,2,3]:box('detail_canopy_soffit_rib',x+dx,3.50,z+2.2,.065,.14,5.25,frame)
    for dx in [-2.5,2.5]:box('detail_door_header',x+dx/2,3.01,z,2.45,.17,.25,'#b9c9c4')
    # Open leaves sit outside the 5 m opening; no hidden barrier across the doorway.
    for dx in [-2.72,2.72]:
        box('detail_open_door_frame',x+dx,1.52,z-.66,.13,3.02,1.32,frame)
        g.tube('detail_door_pull',(x+dx,1.05,z-.13),(x+dx,1.73,z-.13),.018,'#b9c9c4',n=6)
    ground(box('detail_entry_mat',x,.06,z+1.1,4.5,.035,1.7,'#657275'))
    for dx in [-4.8,4.8]:
        box('detail_entry_planter',x+dx,.39,z+3.3,1.35,.78,1.35,'#b9bdb1',True)
        box('detail_planter_soil',x+dx,.79,z+3.3,1.18,.035,1.18,'#79694f')

# Irregular small leaf clusters keep a young campus scale and replace smooth toy balls.
leaf_meshes={}
for color in ['#537647','#698847','#789450','#4b6b44']:
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)
    for v in bm.verts:v.co*=rng.uniform(.86,1.12)
    mesh=bpy.data.meshes.new('Detail_crown_'+color);bm.to_mesh(mesh);bm.free()
    vs=[tuple(v.co*.90) for v in mesh.vertices];fs=[tuple(p.vertices) for p in mesh.polygons]
    for i in range(82):
        az=rng.uniform(0,math.tau);h=rng.uniform(-.86,.86);r=math.sqrt(1-h*h)*rng.uniform(.88,1.04)
        p=Vector((r*math.cos(az),r*math.sin(az),h));u=Vector((-math.sin(az),math.cos(az),.25))*rng.uniform(.11,.19);v=Vector((math.cos(az)*.3,math.sin(az)*.3,1))*.09
        ix=len(vs);vs.extend(tuple(q) for q in [p-u,p+v,p+u,p-v]);fs.extend([(ix,ix+1,ix+2),(ix,ix+2,ix+3)])
    mesh.clear_geometry();mesh.from_pydata(vs,[],fs);mesh.update();mesh.materials.append(g.mat(color))
    for p in mesh.polygons:p.use_smooth=len(p.vertices)>3
    leaf_meshes[color]=mesh
for o in scene.objects:
    if o.name.startswith('campus_young_canopy'):
        color=rng.choice(list(leaf_meshes));o.data=leaf_meshes[color];o.rotation_euler.z=rng.uniform(0,math.tau)
for x,z in [(-9.8,14.2),(-.2,14.2),(79.2,18.8),(88.8,18.8)]:
    for i in range(5):
        o=bpy.data.objects.new('detail_entry_shrub',leaf_meshes['#4b6b44']);scene.collection.objects.link(o)
        o.location=g.bp(x+rng.uniform(-.4,.4),.94,z+rng.uniform(-.4,.4));o.scale=(.42,.42,.40)

# Photographed slatted benches and flush tree pits along the main forecourt.
for o in list(scene.objects):
    if not o.name.startswith('campus_bench_slat') or o.type!='MESH':continue
    if not o.name.endswith('.004') and o.name!='campus_bench_slat':continue
    e=extent(o);x=(e[0]+e[1])/2;z=(e[2]+e[3])/2
    for y in [.74,.90]:box('detail_bench_back_slat',x,y,z+.31,1.85,.11,.065,'#907553')
for x in [-8,19,48,76,102]:
    ground(box('detail_tree_pit',x,.042,38,2.1,.045,2.1,'#79694f'))
    for dx in [-1.06,1.06]:ground(box('detail_tree_pit_edging',x+dx,.070,38,.085,.06,2.2,'#b9bdb1'))
    for dz in [-1.06,1.06]:ground(box('detail_tree_pit_edging',x,.070,38+dz,2.2,.06,.085,'#b9bdb1'))

# RC windows get reveals and alternating pier strips instead of a flat brick box.
for id,h,n in [('1476045298',28,8),('1476045299',28,8)]:
    pts=poly(id);signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
    for a,b in zip(pts,pts[1:]+pts[:1]):
        ll=math.dist(a,b);dx=(b[0]-a[0])/ll;dz=(b[1]-a[1])/ll;nx,nz=(dz,-dx) if signed>0 else (-dz,dx)
        count=max(1,int(ll/3.1))
        for j in range(count):
            t=(j+.04)/count;x=a[0]+(b[0]-a[0])*t+nx*.09;z=a[1]+(b[1]-a[1])*t+nz*.09
            seg('detail_rc_vertical_pier',(x-dx*.12,z-dz*.12),(x+dx*.12,z+dz*.12),.17,h,'#cf9676')
            for floor in range(n):
                t=(j+.49)/count;x=a[0]+(b[0]-a[0])*t+nx*.13;z=a[1]+(b[1]-a[1])*t+nz*.13
                seg('detail_rc_window_divider',(x-dx*.035,z-dz*.035),(x+dx*.035,z+dz*.035),.20,2.05,'#b9c9c4',floor*h/n+.55)

# Window material transparency is toned down: frames stay legible while retaining lobby view.
g.mat('#98bac0').node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.47
for m in [g.mat('#537647'),g.mat('#698847'),g.mat('#789450'),g.mat('#4b6b44')]:
    m.use_backface_culling=False
for o in scene.objects:
    if o.name.startswith(('detail_forecourt','detail_granite','detail_drain','detail_walk','detail_campus_walk','detail_tree_pit','detail_entry_mat')):o['no_shadow']=True

world['solids'].extend(g.solids)
# The detailed pavers sit above the original campus plane. Keep walking and
# guide placement on their top surface, including the small grout gaps.
world['solids']=[s for s in world['solids'] if s['name']!='walk-floor_kentech_forecourt']
world['solids'].append(dict(name='walk-floor_kentech_forecourt',kind='box',position=[43,.0765,23],size=[146,.153,20],color='#c8c4b8',collision=False))
world['spawn']['height']=.153
world['provenance']['detailRevision']='v53 photo-led glazing, brise-soleil, granite forecourt and RC reveals'
world['provenance']['detailLimitations']='Facade/paving module sizes, foliage, door hardware and planters inferred from photos; existing map footprints retained.'
worldpath.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
scene.eevee.taa_render_samples=48
scene.view_settings.exposure=.25
editable_objects=len(scene.objects)
bpy.ops.wm.save_as_mainfile(filepath=str(target))
print('DETAIL editable revision saved',editable_objects,flush=True)
batch_and_export(scene,R/'public/models/bitgaram-kentech.glb')
raw=(R/'public/models/bitgaram-kentech.glb').read_bytes()
(R/'public/models/bitgaram-kentech.glb.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
metrics=dict(editableObjects=editable_objects,exportMeshes=sum(o.type=='MESH' for o in scene.objects),glbBytes=len(raw),gzipBytes=(R/'public/models/bitgaram-kentech.glb.gz').stat().st_size)
(R/'knowledge/sources/kentech-v52/detail-v53-metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf8')
print('DETAIL EXPORT',metrics,flush=True)
cam=scene.camera
for name,pos,aim,lens in [('main-building',(-64,36,118),(44,9,-4),35),('entrance',(-16,1.72,26),(-3,5.5,10),23),('campus-overview',(-410,420,560),(30,0,20),34)]:
    cam.location=g.bp(*pos);cam.rotation_euler=(Vector(g.bp(*aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    scene.render.filepath=str(O/(name+'-v53.png'));bpy.ops.render.render(write_still=True)
print('DETAIL COMPLETE',flush=True)
