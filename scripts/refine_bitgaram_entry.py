"""Second photo comparison: asymmetrical wrap and circular glazed entrance."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];target=root/'outputs/bitgaram/bitgaram-park-entry-detail.blend'
if target.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-park-aerial-detail.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
for o in list(bpy.data.objects):
    if o.name.startswith(('aerial_sweeping_fascia','aerial_fascia_seam','aerial_ground_entry','aerial_entry_header','aerial_entry_handle')) or o.name=='label_빛가람 전망대.001':bpy.data.objects.remove(o,do_unlink=True)
    elif o.name.startswith(('panoramic_glazing','window_mullion')) and o.type=='MESH':
        # Meet the higher replacement roof rather than leaving a slit above the old glazing.
        for v in o.data.vertices:
            if v.co.z>34.3:v.co.z+=.92
def skin(name,a,b,lowA,lowB,highA,highB):
    verts=[]
    for rx,rz in [(14.9,12.1),(14.65,11.85)]:
        verts.extend([(rx*math.cos(a),lowA,rz*math.sin(a)),(rx*math.cos(b),lowB,rz*math.sin(b)),(rx*math.cos(b),highB,rz*math.sin(b)),(rx*math.cos(a),highA,rz*math.sin(a))])
    return g.mesh(name,verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)],'#cbd2cf',smooth=True)
# A broad cladding wrap on one side with a long rounded opening; the opposite side is glazed.
N=100
def opening(a):
    t=max(0,1-(a/1.06)**2)
    return 32.65-1.05*math.sqrt(t),32.65+1.05*math.sqrt(t)
for i in range(N):
    a=-1.4+2.8*i/N;b=-1.4+2.8*(i+1)/N
    la,ha=opening(a);lb,hb=opening(b)
    skin('photo_wrap_lower',a,b,29.9,29.9,la,lb)
    skin('photo_wrap_upper',a,b,ha,hb,35.45,35.45)
    if i%4==0:
        x,z=14.925*math.cos(a),12.125*math.sin(a)
        g.tube('photo_wrap_joint',(x,29.92,z),(x,la,z),.009,'#a4afad',n=4)
        g.tube('photo_wrap_joint',(x,ha,z),(x,35.42,z),.009,'#a4afad',n=4)
# Curved entrance drum observed in the 2017 ground-level photograph. Dimensions inferred.
pts=[(5.4*math.cos(i*math.tau/64),1.2+5.1*math.sin(i*math.tau/64)) for i in range(64)]
g.polygon('photo_entry_drum',pts,16,3.2,'#386981',True)
g.polygon('photo_entry_silver_band',pts,19.2,1.55,'#cbd0cb',True)
for i in range(48):
    a=i*math.tau/48;x,z=5.43*math.cos(a),1.2+5.13*math.sin(a)
    g.tube('photo_entry_mullion',(x,16.05,z),(x,19.2,z),.04,'#bac7c6',n=6)
    g.tube('photo_entry_panel_joint',(x,19.25,z),(x,20.7,z),.012,'#9baaa7',n=4)
for i in range(64):
    a=i*math.tau/64;b=(i+1)*math.tau/64
    g.segment('photo_blue_safety_band',(5.45*math.cos(a),1.2+5.15*math.sin(a)),(5.45*math.cos(b),1.2+5.15*math.sin(b)),.02,.095,'#1687b9',base=17.2,record=False)
for x in [-1.65,1.65]:g.box('photo_entry_door_frame',x,17.6,6.25,.13,3.2,.5,'#c6d0ca',record=False)
g.box('photo_entry_portico',0,19.36,6.3,3.65,.4,.7,'#d2d7ce',record=False)
g.box('photo_entry_door_divider',0,17.6,6.5,.065,3.2,.07,'#b6c6c6',record=False)
g.label('빛가람 전망대',0,19.98,6.72,3.5,.42,color='#284f8a')
g.box('photo_entry_tactile',0,16.011,7,2.7,.02,.45,'#d6b448',record=False)
for x in range(-12,13):
    for z in range(-11,15):
        if math.hypot(x,z)>7 and math.hypot(x,z)<19:
            # Paving seams stay on the existing walkable summit floor.
            g.box('photo_summit_paving_joint',x,16.004,z,.012,.006,.99,'#a7aa9f',record=False)
            g.box('photo_summit_paving_joint',x+.5,16.004,z+.5,.99,.006,.012,'#a7aa9f',record=False)
for o in bpy.data.objects:
    if o.name.startswith('tree_canopy'):
        for p in o.data.polygons:p.use_smooth=True
# The lower exhibition building retains its real mapped footprint and gains a sloping metal shell.
data=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
outline=next(w['points'] for w in data['ways'] if w['id']=='908801772')[:-1]
for o in list(bpy.data.objects):
    if o.name.startswith(('exhibition_osm','exhibition_front_glass')):bpy.data.objects.remove(o,do_unlink=True)
roofheight=lambda z:5.5+(z-104)/38*3.1
n=len(outline)
verts=[(x,y,z) for y in [0] for x,z in outline]+[(x,roofheight(z),z) for x,z in outline]
g.mesh('photo_exhibition_sloped_shell',verts,[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],'#c1c7bf')
g.collider('photo_exhibition_shell',outline,0,8.7)
for a,b in zip(outline,outline[1:]+outline[:1]):
    length=math.dist(a,b)
    if length<2:continue
    count=max(1,round(length/2.4))
    for i in range(count):
        t=(i+.05)/count;u=(i+.95)/count
        p=[a[k]+(b[k]-a[k])*t for k in [0,1]];q=[a[k]+(b[k]-a[k])*u for k in [0,1]]
        # Thin overlays follow the actual footprint, including its angled bays.
        g.segment('photo_exhibition_window',p,q,.10,3.6,'#345761',base=.4,record=False)
        if (a[1]+b[1])/2>130:g.segment('photo_exhibition_orange_panel',p,q,.12,1.0,'#b77948',base=4.15,record=False)
        g.tube('photo_exhibition_panel_joint',(p[0],4.1,p[1]),(p[0],roofheight(p[1])-.1,p[1]),.018,'#9aa69f',n=4)
worldfile=root/'public/bitgaram-park-world.json';w=json.loads(worldfile.read_text(encoding='utf-8'))
w['solids']=[s for s in w['solids'] if not s['name'].startswith(('photo_','exhibition_osm'))]+g.solids
worldfile.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;s.camera.location=g.bp(42,37,56);s.camera.rotation_euler=(Vector(g.bp(0,25,0))-s.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-park.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
s.render.filepath=str(root/'outputs/bitgaram/bitgaram-park-entry-detail.png');bpy.ops.render.render(write_still=True)
