"""Aerial-photo revision. Preserve all previous editable Blender revisions."""
import bpy, json, math, random, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'outputs/bitgaram/bitgaram-park-aerial-detail.blend'
if target.exists() and '--replace-generated' not in sys.argv: raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/bitgaram/bitgaram-park-landscape.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
# Only replace explicitly named original exterior elements, leaving walking floors intact.
prefixes=('observatory_roof','silver_upper_rim','silver_lower_rim','tower_column')
for o in list(bpy.data.objects):
    if o.name.startswith(prefixes): bpy.data.objects.remove(o,do_unlink=True)
def ring(name,outer,inner,y,thickness,color,offset=(-2,0),wave=0):
    n=128;verts=[]
    for height in [y,y+thickness]:
        for rx,rz,cx,cz in [(outer[0],outer[1],0,0),(inner[0],inner[1],*offset)]:
            for i in range(n):
                a=i*math.tau/n;verts.append((cx+rx*math.cos(a),height+wave*math.cos(a+.5),cz+rz*math.sin(a)))
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    return g.mesh(name,verts,faces,color,smooth=True)
# Photo-observed open oval roof and layered curved silver skin. Exact dimensions estimated.
ring('aerial_roof_open_oval',(15.6,12.5),(5.4,3.9),35.65,.32,'#e3e5df')
ring('aerial_roof_edge',(15.7,12.6),(15.35,12.25),35.48,.22,'#b9c1c0',offset=(0,0))
ring('aerial_inner_reveal',(5.4,3.9),(5.22,3.72),34.05,1.6,'#8d9d9e',offset=(-2,0))
# Inner reveal is centered on the offset roof opening, unlike outer ring.
obj=bpy.data.objects['aerial_inner_reveal']
for v in obj.data.vertices:
    # outer loop in ring() was centered at origin; move it to the same opening center.
    if v.index%256<128:v.co.x-=2
ring('aerial_sweeping_fascia',(14.8,12.05),(14.45,11.7),32.85,1.35,'#c3c9c6',offset=(0,0),wave=.36)
ring('aerial_deck_edge',(14.3,11.85),(13.9,11.45),29.25,.66,'#aab4b1',offset=(0,0))
for i in range(144):
    a=i*math.tau/144
    x,z=14.84*math.cos(a),12.09*math.sin(a);y=32.85+.36*math.cos(a+.5)
    g.tube('aerial_fascia_seam',(x,y,z),(x,y+1.35,z),.013,'#a4afac',n=4)
# Tall structural columns visible in the supplied real aerial photograph.
for i,a in enumerate([.2,1.05,1.9,2.85,3.8,4.8]):
    x,z=8.8*math.cos(a),7.6*math.sin(a)
    top=(x+(1.2 if i%2 else -1.2),29.6,z-.6)
    g.tube('aerial_structural_column',(x,16,z),top,.42,'#c1c7c4',n=16)
    g.box('aerial_column_foot',x,16.13,z,1.05,.26,1.05,'#acb3ad',collision=True)
    # Conservative vertical envelope also prevents walking through the slanted support.
    g.collider('aerial_column_body',[(min(x,top[0])-.44,min(z,top[2])-.44),(max(x,top[0])+.44,min(z,top[2])-.44),(max(x,top[0])+.44,max(z,top[2])+.44),(min(x,top[0])-.44,max(z,top[2])+.44)],16,13.6)
for x in [-1.15,1.15]:
    g.box('aerial_ground_entry_glass',x,17.5,3.72,2.2,2.9,.05,'#55777a',record=False)
    g.tube('aerial_entry_handle',(x*.28,17,3.8),(x*.28,18,3.8),.035,'#b9c6c4')
g.box('aerial_entry_header',0,19.15,3.85,5,.4,.35,'#d6dad0',record=False)
g.label('빛가람 전망대',0,19.2,4.05,4,.3,color='#304d53')
# Shared mesh canopies add wooded coverage without thousands of Blender operators.
data=json.loads((ROOT/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
wood=next(w['points'] for w in data['ways'] if w['id']=='508048953')
def inside(x,z):
    yes=False
    for a,b in zip(wood,wood[1:]+wood[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
rng=random.Random(91540);templates=[]
for color in ['#4c6b3f','#597745','#68874c','#799258']:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
    o=bpy.context.object;o.data.materials.append(g.mat(color))
    for p in o.data.polygons:p.use_smooth=True
    templates.append(o.data);bpy.data.objects.remove(o,do_unlink=True)
count=0
for i in range(1600):
    x,z=rng.uniform(-140,140),rng.uniform(-140,145)
    if not inside(x,z) or math.hypot(x,z)<28 or (3<x<25 and z>12):continue
    h=min(16*math.exp(-((x/100)**2+(z/105)**2)*1.6),15.75)+.02
    radius=rng.uniform(2,3.6);height=rng.uniform(3.4,6.5)
    o=bpy.data.objects.new('aerial_woodland_canopy',templates[rng.randrange(4)])
    g.groups['03_Report_Burials'].objects.link(o);o.location=g.bp(x,h+height,z)
    o.scale=(radius,radius*rng.uniform(.7,1.2),radius*.8);o.rotation_euler.z=rng.random()*math.tau
    count+=1
worldpath=ROOT/'public/bitgaram-park-world.json'
world=json.loads(worldpath.read_text(encoding='utf-8'))
world['solids']=[s for s in world['solids'] if not s['name'].startswith('aerial_')]+g.solids
world['limitations']=['OSM plan and woodland boundary; supplied press aerial photo informs open oval roof and supports. Roof dimensions, support positions and vegetation are estimated; planning renderings are not treated as built conditions.']
worldpath.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;cam=s.camera;cam.location=g.bp(65,62,83)
cam.rotation_euler=(Vector(g.bp(0,26,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45
s.render.resolution_x=1280;s.render.resolution_y=900;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/bitgaram-park.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
s.render.filepath=str(ROOT/'outputs/bitgaram/bitgaram-park-aerial-detail.png')
if '--render' in sys.argv:bpy.ops.render.render(write_still=True)
print('Added woodland crowns:',count,flush=True)
