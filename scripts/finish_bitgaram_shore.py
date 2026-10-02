"""Finish mapped park edges without changing the detailed walking area."""
import bpy,math,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1]
overview='--overview' in sys.argv
source='overview-surroundings-final' if overview else 'park-surroundings'
target=root/f'outputs/bitgaram/bitgaram-{"overview" if overview else "park"}-shore-finish.blend'
if target.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/f'outputs/bitgaram/bitgaram-{source}.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
ways=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))['ways']
park=next(w['points'] for w in ways if w['id']=='508048299')
waters=[w['points'] for w in ways if w['tags'].get('natural')=='water']
def inside(x,z,p):
    yes=False
    for a,b in zip(p,p[1:]+p[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
def land(x,z):return inside(x,z,park) and not any(inside(x,z,p) for p in waters)
def distance(x,z,a,b):
    dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
    return math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)
paths=[(a,b) for w in ways if w['tags'].get('highway') for a,b in zip(w['points'],w['points'][1:])]
facilities=[w['points'] for w in ways if w['tags'].get('amenity')=='parking' or w['tags'].get('building') or w['tags'].get('leisure') in ['playground','miniature_golf']]
for o in list(bpy.data.objects):
    if o.name=='surrounding_park_lawn':bpy.data.objects.remove(o,do_unlink=True)
# Finer coastal silhouette; continuous lawn under the hill removes the square cutout.
verts=[];faces=[]
for x in range(-550,450,2):
    for z in range(-450,355,2):
        if abs(x)<140 and abs(z)<140:continue
        corners=[(x,z),(x+2,z),(x+2,z+2),(x,z+2)]
        if not all(land(a,b) for a,b in corners):continue
        n=len(verts);verts.extend((a,-.075,b) for a,b in corners);faces.append((n,n+1,n+2,n+3))
g.mesh('surrounding_park_lawn',verts,faces,'#a8b886')
# Estimated planting in the circled shore area. Mapped paths and facility footprints stay clear.
rng=random.Random(91528)
template=next(o.data for o in bpy.data.objects if o.name.startswith('aerial_woodland_canopy'))
count=0
for x0 in range(-245,246,9):
    for z0 in range(-240,276,9):
        x,z=x0+rng.uniform(-3,3),z0+rng.uniform(-3,3)
        if abs(x)<157 and abs(z)<157:continue
        if not land(x,z) or any(inside(x,z,p) for p in facilities):continue
        if any(distance(x,z,a,b)<5 for a,b in paths):continue
        if rng.random()>.68:continue
        size=rng.uniform(1.6,3.2);h=rng.uniform(2.8,4.2)
        o=bpy.data.objects.new('shore_finish_tree',template);g.groups['04_Estimated_Fixtures'].objects.link(o)
        o.location=g.bp(x,h,z);o.scale=(size,size,size*.85)
        g.tube('shore_finish_trunk',(x,0,z),(x,h,z),.12,'#756550',n=5);count+=1
        if rng.random()<.35:
            shrub=bpy.data.objects.new('shore_finish_shrub',template);g.groups['04_Estimated_Fixtures'].objects.link(shrub)
            shrub.location=g.bp(x+2,.65,z+1);shrub.scale=(1.1,1.1,.65)
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/f'public/models/bitgaram-{"overview" if overview else "park"}.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
print('Shore planting:',count,flush=True)
