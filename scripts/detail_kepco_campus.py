"""Restore complete headquarters silhouette and map the surrounding campus."""
import bpy,json,math,random,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-kepco-campus-detail.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-kepco.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
ways=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))['ways']
main=next(w for w in ways if w['id']=='594386007');raw=main['points'][:-1]
center=[sum(p[i] for p in raw)/len(raw) for i in [0,1]]
edge=max(zip(raw,raw[1:]+raw[:1]),key=lambda ab:math.dist(*ab));angle=math.atan2(edge[1][1]-edge[0][1],edge[1][0]-edge[0][0]);c,s=math.cos(angle),math.sin(angle)
def local(p):x,z=p[0]-center[0],p[1]-center[1];return [x*c+z*s,-x*s+z*c]
def inside(x,z,p):
    yes=False
    for a,b in zip(p,p[1:]+p[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
campus=[local(p) for p in next(w for w in ways if w['id']=='508052678')['points']]
footprint=[local(p) for p in raw]
wpath=root/'public/bitgaram-kepco-world.json';world=json.loads(wpath.read_text(encoding='utf-8'));entry=world['spawn']
# An outdoor overview must retain the tower and podium, not expose the ground-floor cutaway.
for o in bpy.data.objects:
    if o.get('hide_in_overview'):o['hide_in_overview']=False
g.box('campus_context_ground',0,-.4,0,1150,.3,1150,'#b7c2ae',record=False)
g.polygon('ground_floor_campus',campus,-.12,.12,'#c3cbb9')
# The full-height glass facades receive side mullions and floor bands as well as their existing front grid.
for x in [-15.65,33.65]:
    for z in range(-23,15,3):g.box('campus_tower_side_mullion',x,85.5,z,.24,137,.15,'#c4d0ce',record=False)
    for y in range(20,153,4):g.box('campus_tower_side_storey',x,y,-5,.2,.18,38,'#a2b8bb',record=False)
g.mesh('campus_tower_crown',[(-15.5,154,-24),(33.5,154,-24),(33.5,154,14),(-15.5,154,14),(-15.5,160,-24),(33.5,154,-24),(33.5,154,14),(-15.5,160,14)],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'#b3c4c8')
ids=[];roads=[];buildings=[]
for way in ways:
    p=[local(q) for q in way['points']];tags=way['tags']
    if not p or min(math.hypot(*q) for q in p)>490:continue
    if tags.get('building') and way['id']!=main['id'] and p[0]==p[-1]:
        height=float(tags.get('height',float(tags.get('building:levels',4))*3.2))
        g.polygon('campus_context_building_'+way['id'],p,0,height,'#a4b4b4',True);buildings.append(p);ids.append(way['id'])
        g.polygon('campus_context_roof_'+way['id'],p,height,.16,'#bac5c0')
    if tags.get('highway'):
        width=3 if tags['highway'] in ['footway','path','steps'] else 6 if tags['highway']=='service' else 11
        for a,b in zip(p,p[1:]):
            if max(math.hypot(*a),math.hypot(*b))>540:continue
            roads.append((a,b,width));g.segment('campus_mapped_road',a,b,width,.035,'#d8d4c2' if width==3 else '#929f9c',base=.015,record=False)
    if tags.get('amenity')=='parking' and p[0]==p[-1]:g.polygon('campus_mapped_parking',p,.015,.025,'#9ca7a1')
    if tags.get('aeroway')=='helipad' and p[0]==p[-1]:
        g.polygon('campus_mapped_helipad',p,.02,.025,'#9bac9a')
def nearpath(x,z):
    for a,b,width in roads:
        dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
        if math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)<width/2+3:return True
    return False
rng=random.Random(1531)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);template=bpy.context.object.data;template.materials.append(g.mat('#688453'));bpy.data.objects.remove(bpy.context.object,do_unlink=True)
count=0
for x0 in range(-320,321,13):
    for z0 in range(-320,321,13):
        x,z=x0+rng.uniform(-3,3),z0+rng.uniform(-3,3)
        if not inside(x,z,campus) or inside(x,z,footprint) or any(inside(x,z,p) for p in buildings):continue
        if nearpath(x,z) or (abs(x-entry['x'])<10 and z>entry['z']-12):continue
        if rng.random()>.58:continue
        radius=rng.uniform(1.8,3);o=bpy.data.objects.new('campus_tree_crown',template);g.groups['04_Estimated_Fixtures'].objects.link(o);o.location=g.bp(x,4,z);o.scale=(radius,radius,radius*.95)
        g.tube('campus_tree_trunk',(x,0,z),(x,4,z),.13,'#7e6e57',n=6)
        g.collider('campus_tree',[(x-.18,z-.18),(x+.18,z-.18),(x+.18,z+.18),(x-.18,z+.18)],0,4);count+=1
# Clear arrival axis, paving joints, low planters and solar streetlights inspired by the press photographs.
ez=entry['z']
for dx in [-16,16]:
    for offset in [15,35,55]:
        x,z=entry['x']+dx,ez+offset
        if not inside(x,z,campus):continue
        g.box('campus_planter',x,.25,z,5,.5,8,'#a6b291',True)
        g.box('campus_planting_soil',x,.505,z,4.7,.015,7.7,'#758962',record=False)
        g.tube('campus_solar_light',(x+4,0,z),(x+4,5,z),.08,'#788c8b',n=8)
        g.box('campus_solar_panel',x+4,5.1,z,1.7,.09,1,'#375e72',record=False)
        g.box('campus_light_head',x+4,4.6,z+.55,1,.1,.25,'#ece7d0',record=False)
world['solids']+=g.solids
world['bounds']=[min(p[0] for p in campus),max(p[0] for p in campus),min(p[1] for p in campus),max(p[1] for p in campus)]
world['provenance']['campusOsmWay']='508052678';world['provenance']['contextBuildingIds']=ids
world['provenance']['limitations']='Mapped campus, roads and surrounding footprints; tower/podium split, crown, planting and finishes estimated. Upper floors exterior only.'
wpath.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;s.camera.location=g.bp(280,210,370);s.camera.rotation_euler=(Vector(g.bp(0,55,0))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=35
s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-kepco.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
print('Campus trees',count,'context buildings',len(ids),flush=True)
s.render.filepath=str(root/'outputs/bitgaram/kepco-campus-review.png');bpy.ops.render.render(write_still=True)
