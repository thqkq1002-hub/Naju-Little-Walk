"""Photo-informed interior finishes in a preserved revision of the observatory."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-observatory-interior-finish.blend'
if out.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-observatory-entry-detail.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
def ring(name,rx,rz,y,width,height,color,n=96,roof=False):
    for i in range(n):
        a=i*math.tau/n;b=(i+1)*math.tau/n
        o=g.segment(name,(rx*math.cos(a),rz*math.sin(a)),(rx*math.cos(b),rz*math.sin(b)),width,height,color,base=y,record=False)
        if roof:o['hide_in_overview']=True
def disc(name,x,y,z,r,h,color,n=24):return g.polygon(name,[(x+r*math.cos(i*math.tau/n),z+r*math.sin(i*math.tau/n)) for i in range(n)],y,h,color)
# Fine, continuous tile joints clipped to the floor footprint.
for o in list(bpy.data.objects):
    if o.name.startswith('tile_joint'):bpy.data.objects.remove(o,do_unlink=True)
for x in range(-13,14):
    half=11.25*math.sqrt(max(0,1-(x/13.65)**2))
    if half:g.box('finish_floor_joint',x,.009,0,.008,.003,half*2,'#b6b9b3',record=False)
for z in range(-11,12):
    half=13.65*math.sqrt(max(0,1-(z/11.25)**2))
    if half:g.box('finish_floor_joint',0,.009,z,half*2,.003,.008,'#b6b9b3',record=False)
for o in bpy.data.objects:
    if o.name=='ground_floor_observatory':
        m=o.data.materials[0].copy();m.name='Polished_observation_tile';m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.3;o.data.materials[0]=m
# Window sill, slim protective inner rail, joints and fixing feet.
ring('finish_window_sill',13.35,10.95,.12,.28,.10,'#c3c8c5')
ring('finish_guard_handhold',12.85,10.45,1.03,.045,.05,'#697c7c')
ring('finish_guard_lower',12.85,10.45,.19,.035,.045,'#82918f')
for i in range(48):
    a=i*math.tau/48;x,z=12.85*math.cos(a),10.45*math.sin(a)
    g.tube('finish_guard_post',(x,.06,z),(x,1.07,z),.026,'#748683',n=8)
    disc('finish_guard_foot',x,.015,z,.075,.025,'#657471',n=12)
    b=(i+1)*math.tau/48
    g.collider('finish_guard',[(12.79*math.cos(a),10.39*math.sin(a)),(12.91*math.cos(a),10.51*math.sin(a)),(12.91*math.cos(b),10.51*math.sin(b)),(12.79*math.cos(b),10.39*math.sin(b))],0,1.08)
# Shallow annular ceiling panels retain the central architectural opening.
for i in range(96):
    a=i*math.tau/96;b=(i+1)*math.tau/96
    o=g.mesh('finish_ceiling_panel',[(rx*math.cos(t),4.13,rz*math.sin(t)) for rx,rz,t in [(13.3,10.9,a),(13.3,10.9,b),(6.0,4.9,b),(6.0,4.9,a)]],[(0,1,2,3)],'#e1e2da')
    o['hide_in_overview']=True
    if i%4==0:
        o=g.tube('finish_ceiling_seam',(6*math.cos(a),4.11,4.9*math.sin(a)),(13.3*math.cos(a),4.11,10.9*math.sin(a)),.009,'#b4bcb6',n=4);o['hide_in_overview']=True
ring('finish_ceiling_inner_trim',6,4.9,4.05,.09,.12,'#c6ccc6',roof=True)
ring('finish_ceiling_cove',12.9,10.5,4.04,.14,.07,'#f0ebd5',roof=True)
for i in range(16):
    a=i*math.tau/16
    o=disc('finish_downlight',10.7*math.cos(a),4.02,8.6*math.sin(a),.12,.018,'#fff2cd');o['hide_in_overview']=True
    mat=o.data.materials[0];bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Emission Color'].default_value=(1,.87,.62,1);bs.inputs['Emission Strength'].default_value=1.3
# Lift reveals, stainless door split, call buttons and display; existing wall colliders retained.
for x in [-1.14,1.14]:g.box('finish_lift_reveal',x,1.45,1.98,.12,2.9,.13,'#aab1ae',record=False)
g.box('finish_lift_header',0,2.94,1.98,2.4,.13,.14,'#aab1ae',record=False)
g.box('finish_lift_split',0,1.4,1.946,.018,2.75,.01,'#505e5c',record=False)
g.box('finish_lift_display',0,3.43,2.29,.6,.21,.045,'#253938',record=False)
g.label('5F',0,3.43,2.32,.4,.13,color='#d7e8c9')
for x in [-1.43,1.43]:g.box('finish_lift_infill',x,1.8,2.19,.57,3.6,.16,'#cbc9bc',collision=True)
g.box('finish_lift_call_plate',1.52,1.23,2.3,.15,.32,.04,'#9ea7a2',record=False)
for y in [1.17,1.29]:g.box('finish_lift_button',1.52,y,2.328,.065,.065,.012,'#e8ece2',record=False)
for x in [-2.8,2.8]:g.box('finish_core_skirting',x,.085,0,.19,.17,4.4,'#9baba4',record=False)
# Refine the existing three telescope/bench positions, avoiding new room obstructions.
for x,z in [(-9,2),(-7,-6),(8,4)]:
    disc('finish_scope_base',x+1,.01,z,.27,.06,'#6c7977')
    g.tube('finish_scope_eyepiece',(x+.78,1.33,z+.34),(x+.88,1.37,z+.19),.08,'#273e40',n=16)
    g.tube('finish_scope_lens',(x+1.30,1.48,z-.42),(x+1.37,1.51,z-.54),.12,'#244c55',n=16)
    g.tube('finish_scope_handle',(x+.64,1.13,z+.05),(x+1.40,1.13,z+.05),.026,'#697c7b',n=8)
    g.collider('finish_bench_body',[(x-.94,z-.37),(x+.94,z-.37),(x+.94,z+.34),(x-.94,z+.34)],0,1.08)
    g.collider('finish_scope_body',[(x+.72,z-.32),(x+1.28,z-.32),(x+1.28,z+.32),(x+.72,z+.32)],0,1.5)
    for dx in [-.82,.82]:
        g.box('finish_bench_arm',x+dx,.67,z,.06,.07,.57,'#5d706b',record=False)
        for dz in [-.23,.23]:g.tube('finish_bench_arm_post',(x+dx,.48,z+dz),(x+dx,.68,z+dz),.025,'#5d706b',n=6)
# A readable panorama guide on the existing central-core face, no invented exhibition content.
g.box('finish_panorama_panel',0,1.8,-2.315,3.8,1.15,.035,'#436566',record=False)
o=g.label('빛가람 호수공원',0,2.05,-2.34,3.3,.27,color='#eceddf');o.rotation_euler.z+=math.pi
o=g.label('호수 · 산책로 · 혁신도시',0,1.66,-2.34,3.3,.16,color='#d4dfd5');o.rotation_euler.z+=math.pi
wpath=root/'public/bitgaram-observatory-world.json';w=json.loads(wpath.read_text(encoding='utf-8'))
w['solids']=[s for s in w['solids'] if not s['name'].startswith('finish_')]+[s for s in g.solids if s.get('collision')]
w['limitations']=['Curved glazing, tiled floor and viewing rail informed by public interior photographs; dimensions, finish joints, lighting and furniture details estimated.']
wpath.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;s.camera.location=g.bp(6,1.65,7);s.camera.rotation_euler=(Vector(g.bp(-5,1.7,-5))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=20
s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-observatory.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
s.render.filepath=str(root/'outputs/bitgaram/observatory-interior-finish-review.png');bpy.ops.render.render(write_still=True)
