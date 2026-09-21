"""Mapped context around the detailed park, with approximate landscape fixtures."""
import bpy,math,json,random,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];target=root/'outputs/bitgaram/bitgaram-park-surroundings.blend'
if target.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-park-forest-detail.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
data=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'));ways=data['ways']
park=next(w['points'] for w in ways if w['id']=='508048299')
waters=[w['points'] for w in ways if w['tags'].get('natural')=='water']
def inside(x,z,pts):
    yes=False
    for a,b in zip(pts,pts[1:]+pts[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
def wet(x,z):return any(inside(x,z,p) for p in waters)
def height(x,z):
    if abs(x)>150 or abs(z)>150:return -.1
    u,v=(x+150)/6,(z+150)/6;i,j=min(49,int(u)),min(49,int(v));tx,tz=u-i,v-j
    def h(a,b):return min(16*math.exp(-(((-150+6*a)/100)**2+((-150+6*b)/105)**2)*1.6),15.75)+.02
    return (1-tx)*h(i,j)+(tx-tz)*h(i+1,j)+tz*h(i+1,j+1) if tx>=tz else (1-tz)*h(i,j)+(tz-tx)*h(i,j+1)+tx*h(i+1,j+1)
# One mesh fills mapped land only, leaving the real lake silhouettes unobscured.
verts=[];faces=[]
for x in range(-550,450,5):
    for z in range(-450,355,5):
        corners=[(x,z),(x+5,z),(x+5,z+5),(x,z+5)]
        if abs(x)<153 and abs(z)<153:continue
        if not all(inside(a,b,park) and not wet(a,b) for a,b in corners):continue
        n=len(verts);verts += [(a,-.085,b) for a,b in corners];faces.append((n,n+1,n+2,n+3))
g.mesh('surrounding_park_lawn',verts,faces,'#9eaf79')
# Replace the faint, short context paths with continuous wider mapped paths.
for o in list(bpy.data.objects):
    if o.name.startswith('mapped_context_path'):bpy.data.objects.remove(o,do_unlink=True)
verts=[];faces=[];treepoints=[];mapped=[]
for w in ways:
    pts=w['points'];kind=w['tags'].get('highway')
    if kind not in ['footway','path','steps','pedestrian','service']:continue
    used=False
    for a,b in zip(pts,pts[1:]):
        if max(abs(a[0]),abs(b[0]))>560 or max(abs(a[1]),abs(b[1]))>460:continue
        if min(math.hypot(*a),math.hypot(*b))<30:continue
        length=math.dist(a,b)
        if length<.05:continue
        width=5 if kind=='service' else 2.8
        ox,oz=-(b[1]-a[1])*width/2/length,(b[0]-a[0])*width/2/length
        for i in range(max(1,math.ceil(length/4))):
            count=max(1,math.ceil(length/4));u=[a[k]+(b[k]-a[k])*i/count for k in [0,1]];v=[a[k]+(b[k]-a[k])*(i+1)/count for k in [0,1]]
            n=len(verts);verts += [(p[0]+side*ox,height(p[0]+side*ox,p[1]+side*oz)+.14,p[1]+side*oz) for p,side in [(u,-1),(v,-1),(v,1),(u,1)]];faces.append((n,n+1,n+2,n+3));used=True
        if kind!='service':
            for i in range(int(length//20)):
                t=(i+.5)*20/length;x=a[0]+(b[0]-a[0])*t+ox*2.7;z=a[1]+(b[1]-a[1])*t+oz*2.7
                if (abs(x)>155 or abs(z)>155) and inside(x,z,park) and not wet(x,z):treepoints.append((x,z))
    if used:mapped.append(w['id'])
g.mesh('surrounding_mapped_paths',verts,faces,'#d9ccad')
parking=[];amenities=[]
for w in ways:
    pts=w['points'];cx=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
    if abs(cx)>450 or abs(cz)>450:continue
    if w['tags'].get('amenity')=='parking':
        g.polygon('surrounding_parking_'+w['id'],pts,-.04,.025,'#919d99');parking.append(w['id'])
        for x in range(math.ceil(min(p[0] for p in pts))+3,math.floor(max(p[0] for p in pts))-3,3):
            for z in range(math.ceil(min(p[1] for p in pts))+7,math.floor(max(p[1] for p in pts))-7,14):
                if all(inside(x+dx,z+dz,pts) for dx,dz in [(0,0),(2.5,0),(0,5),(2.5,5)]):
                    g.box('surrounding_parking_line',x,.004,z+2.5,.07,.014,5,'#e2e5d5',record=False)
                    g.box('surrounding_parking_line',x+1.25,.004,z+5,2.5,.014,.07,'#e2e5d5',record=False)
    if w['tags'].get('leisure') in ['playground','miniature_golf']:
        color='#bfaa7c' if w['tags']['leisure']=='playground' else '#829e60'
        g.polygon('surrounding_recreation_'+w['id'],pts,-.04,.045,color);amenities.append(w['id'])
        # Facility footprints are mapped; play equipment and golf layouts are not invented.
rng=random.Random(926);template=next(o.data for o in bpy.data.objects if o.name.startswith('aerial_woodland_canopy'))
for x,z in treepoints[::2]:
    size=rng.uniform(2,3);o=bpy.data.objects.new('surrounding_path_tree',template);g.groups['03_Report_Burials'].objects.link(o);o.location=g.bp(x,4.4,z);o.scale=(size,size,size*.8)
    g.tube('surrounding_tree_trunk',(x,0,z),(x,4.4,z),.14,'#786651',n=6)
    if rng.random()<.18:
        g.box('surrounding_bench',x+2,.48,z,1.8,.12,.5,'#9a7753',record=False)
        for dx in [1.4,2.6]:g.box('surrounding_bench_leg',x+dx,.22,z,.1,.44,.4,'#59635b',record=False)
# Visual context has no new walkable floors or obstacles in the existing detailed walking area.
wpath=root/'public/bitgaram-park-world.json';world=json.loads(wpath.read_text(encoding='utf-8'))
world['surroundings']={'parkOsmId':'508048299','pathOsmIds':mapped,'parkingOsmIds':parking,'recreationOsmIds':amenities,'walkableExpansion':False,'note':'Mapped footprints; estimated paving width, parking bays, trees and benches.'}
wpath.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;s.camera.location=g.bp(300,390,420);s.camera.rotation_euler=(Vector(g.bp(0,0,0))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=35
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-park.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
print('Mapped paths',len(mapped),'parking',parking,'recreation',amenities,flush=True)
s.render.filepath=str(root/'outputs/bitgaram/bitgaram-park-surroundings.png');bpy.ops.render.render(write_still=True)
