"""Photo-observed timber guards and roof garden; previous Blender edits preserved."""
import bpy,bmesh,json,math,random,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];target=root/'outputs/bitgaram/bitgaram-park-walkway-detail.blend'
if target.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Previous edit preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-park-entry-detail.blend'))
g=MuseumGeometry(bpy.context.scene,(0,0),0)
for o in list(bpy.data.objects):
    if o.name.startswith(('path_post','path_handrail')):bpy.data.objects.remove(o,do_unlink=True)
    elif o.name.startswith(('walk-floor_approach','walk-floor_turnaround')):o.data.materials.clear();o.data.materials.append(g.mat('#a37a53'))
route=[]
for i in range(121):
    z=16+i*.68;x=12+6*math.sin(i/35);y=16 if z<23 else 16*math.exp(-((z*z-23*23)/105**2)*1.6)
    route.append((x,y,z))
for i,(a,b) in enumerate(zip(route,route[1:])):
    if a[2]<25:continue  # Keep the summit plaza entrance open from either side.
    # Collision guards follow each tread height so they cannot become overhead blockers downhill.
    for side in [-1,1]:
        x1,x2=a[0]+side*1.51,b[0]+side*1.51
        obj=g.segment('timber_walk_guard',(x1,a[2]),(x2,b[2]),.12,1.12,'#916542',base=min(a[1],b[1]),collision=True)
        # Record guards only; the visible multi-rail system below remains open between slats.
        bpy.data.objects.remove(obj,do_unlink=True)
        if i%3==0:
            g.box('timber_guard_post',x1,a[1]+.56,a[2],.12,1.12,.12,'#9a714b',record=False)
            g.box('timber_post_cap',x1,a[1]+1.15,a[2],.17,.06,.17,'#52615b',record=False)
            ground=min(16*math.exp(-((x1/100)**2+(a[2]/105)**2)*1.6),15.75)
            if a[1]-.12>ground:
                g.box('timber_deck_pier',x1,(ground+a[1]-.12)/2,a[2],.14,a[1]-.12-ground,.14,'#6b6556',record=False)
        for h in [.15,.38,.65,.91,1.08]:
            # Four horizontal infill rails and a broad top rail, observed in site photographs.
            p=Vector((x1,a[1]+h,a[2]));q=Vector((x2,b[1]+h,b[2]))
            mid=(p+q)/2;length=(q-p).length
            o=g.box('timber_horizontal_rail',0,0,0,length+.03,.075,.09,'#aa7d50',record=False)
            o.location=g.bp(*mid);direction=Vector(g.bp(*(q-p)))
            o.rotation_euler=direction.to_track_quat('X','Z').to_euler()
        g.tube('timber_deck_stringer',(x1,a[1]-.16,a[2]),(x2,b[1]-.16,b[2]),.1,'#735a40',n=4)
    # Small riser boards close the exposed step faces on the descending route.
    drop=a[1]-b[1]
    if drop>.005:g.box('timber_step_riser',(a[0]+b[0])/2,b[1]+drop/2-.025,b[2],3.14,drop+.05,.065,'#8f6948',record=False)
# Model the open roof garden photographed above the lower exhibition building.
shell=bpy.data.objects['photo_exhibition_sloped_shell'];bm=bmesh.new();bm.from_mesh(shell.data)
bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[1]],context='FACES_ONLY')
for v in bm.verts:
    if v.co.z>5:v.co.z=max(7.4,v.co.z)
bm.to_mesh(shell.data);bm.free()
data=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
outline=next(w['points'] for w in data['ways'] if w['id']=='908801772')[:-1]
g.polygon('context_roof_garden_paving',outline,6.1,.12,'#c7cbc0')
g.box('roof_garden_wood_border',13,6.3,120,18,.18,11,'#79634d',record=False)
g.box('roof_garden_lawn',13,6.42,120,17.5,.15,10.5,'#71854b',record=False)
for i in range(2):g.box('roof_garden_step',13,6.2+i*.07,126+i*.32,19+i*.45,.1,.36,'#8d6c4b',record=False)
for x in [5,13,21]:
    g.box('roof_garden_light',x,6.94,124.5,.13,1.0,.13,'#46524c',record=False)
    g.box('roof_garden_light_lens',x,7.25,124.57,.09,.24,.03,'#f0ebcf',record=False)
for x in range(-14,32,2):
    for z in range(111,136,2):
        inside=False
        for a,b in zip(outline,outline[1:]+outline[:1]):
            if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        if not inside:continue
        if 3<x<23 and 113<z<127:continue
        g.box('roof_garden_paving_joint',x,6.225,z,.016,.005,1.95,'#a4afa8',record=False)
# Native woodland undergrowth along the authored route: keep the walk clear.
rng=random.Random(91553)
for i in range(0,120,3):
    x,y,z=route[i]
    if z<26:continue
    for side in [-1,1]:
        px=x+side*rng.uniform(2.6,4.2);pz=z+rng.uniform(-.8,.8)
        h=min(16*math.exp(-((px/100)**2+(pz/105)**2)*1.6),15.75)
        g.rock('pathside_shrub',px,h+.33,pz,rng.uniform(.8,1.4),.6,1,'#6f814c',rng)
wpath=root/'public/bitgaram-park-world.json';w=json.loads(wpath.read_text(encoding='utf-8'))
w['solids']=[s for s in w['solids'] if s['name'] not in ['timber_walk_guard','context_roof_garden_paving']]+g.solids
wpath.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s=bpy.context.scene;s.camera.location=g.bp(27,22,72);s.camera.rotation_euler=(Vector(g.bp(9,21,14))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=38
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-park.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
s.render.filepath=str(root/'outputs/bitgaram/bitgaram-park-walkway-detail.png');bpy.ops.render.render(write_still=True)
