"""Give the aerial woodland shared-mesh trunks and branches for ground-level viewing."""
import bpy,math,random,sys,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
target=root/'outputs/bitgaram/bitgaram-park-forest-detail.blend'
if target.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-park-walkway-detail.blend'))
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
g=MuseumGeometry(bpy.context.scene,(0,0),0);rng=random.Random(916)
data=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
outline=next(w['points'] for w in data['ways'] if w['id']=='908801772')[:-1]
def in_building(x,z):
    inside=False
    for a,b in zip(outline,outline[1:]+outline[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside
bpy.context.view_layer.update()
for o in list(bpy.data.objects):
    if o.name.startswith(('tree_canopy','tree_trunk','aerial_woodland_canopy')):
        center=o.matrix_world @ (sum((Vector(v) for v in o.bound_box),Vector())/8)
        if in_building(center.x,-center.y):bpy.data.objects.remove(o,do_unlink=True)
templates=[]
for color in ['#685a48','#776653','#84745e']:
    # A tapered trunk unit along local Z, instanced across the woodland.
    n=7;vertices=[(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for z,r in [(0,1),(1,.48)] for i in range(n)]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    m=bpy.data.meshes.new('shared_bark');m.from_pydata(vertices,[],faces);m.materials.append(g.mat(color));m.update();templates.append(m)
def limb(name,a,b,r,mesh):
    o=bpy.data.objects.new(name,mesh);g.groups['03_Report_Burials'].objects.link(o)
    axis=Vector(b)-Vector(a);o.location=a;o.scale=(r,r,axis.length);o.rotation_euler=axis.to_track_quat('Z','Y').to_euler()
count=0
for tree in list(bpy.data.objects):
    if not tree.name.startswith('aerial_woodland_canopy'):continue
    x,ny,y=tree.location;z=-ny
    ground=min(16*math.exp(-((x/100)**2+(z/105)**2)*1.6),15.75)+.02
    top=max(ground+.6,y+.25);mesh=templates[rng.randrange(3)];r=rng.uniform(.1,.17)
    limb('woodland_trunk',(x,ny,ground),(x,ny,top),r,mesh)
    for j in range(2):
        a=rng.uniform(0,math.tau);reach=tree.scale.x*.55
        limb('woodland_branch',(x,ny,ground+(top-ground)*.6),(x+math.cos(a)*reach,ny+math.sin(a)*reach,y+.35),r*.48,mesh)
    count+=1
# Close the visible gap beneath the existing summit slab with a terrain-following stone base.
for i in range(96):
    a=i*math.tau/96;b=(i+1)*math.tau/96
    p=(22.96*math.cos(a),22.96*math.sin(a));q=(22.96*math.cos(b),22.96*math.sin(b))
    h=lambda t:min(16*math.exp(-((t[0]/100)**2+(t[1]/105)**2)*1.6),15.75)-.08
    g.mesh('summit_stone_foundation',[(p[0],h(p),p[1]),(q[0],h(q),q[1]),(q[0],15.85,q[1]),(p[0],15.85,p[1])],[(0,1,2,3)],['#9a9f8f','#a7ac9b','#a1a594'][i%3])
    g.collider('summit_stone_base',[(p[0]*.98,p[1]*.98),p,q,(q[0]*.98,q[1]*.98)],min(h(p),h(q)),15.85-min(h(p),h(q)))
for o in bpy.data.objects:
    if o.name.startswith('pathside_shrub'):
        for p in o.data.polygons:p.use_smooth=True
wpath=root/'public/bitgaram-park-world.json';w=json.loads(wpath.read_text(encoding='utf-8'))
w['solids']=[s for s in w['solids'] if s['name']!='summit_stone_base']+g.solids
wpath.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-park.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
print('Structured trees',count,flush=True)
