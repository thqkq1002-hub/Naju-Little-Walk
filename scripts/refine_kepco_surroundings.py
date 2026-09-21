"""Mapped parking detail and facade context, synchronized into the city overview."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
root=Path(__file__).resolve().parents[1];overview='--overview' in sys.argv
ways=json.loads((root/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))['ways']
raw=next(w['points'][:-1] for w in ways if w['id']=='594386007');center=[sum(p[i] for p in raw)/len(raw) for i in [0,1]]
a,b=max(zip(raw,raw[1:]+raw[:1]),key=lambda ab:math.dist(*ab));angle=math.atan2(b[1]-a[1],b[0]-a[0]);c,s=math.cos(angle),math.sin(angle)
def local(p):x,z=p[0]-center[0],p[1]-center[1];return [x*c+z*s,-x*s+z*c]
def inside(x,z,p):
    yes=False
    for a,b in zip(p,p[1:]+p[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes
out=root/f'outputs/bitgaram/bitgaram-{"overview-kepco" if overview else "kepco-surroundings"}.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
if overview:
    bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-overview-soft-woodland.blend'))
    w=json.loads((root/'public/bitgaram-kepco-world.json').read_text(encoding='utf-8'))
    remove={'building_594386007'}|{'building_'+i for i in w['provenance']['contextBuildingIds']}
    for o in list(bpy.data.objects):
        if o.name in remove or o.name.startswith(('narrow_tower','tower_window_band')):bpy.data.objects.remove(o,do_unlink=True)
    with bpy.data.libraries.load(str(root/'outputs/bitgaram/bitgaram-kepco-surroundings.blend'),link=False) as (source,dest):
        dest.objects=[n for n in source.objects if not n.startswith(('Camera','Sun','Area','Light','campus_context_ground'))]
    transform=Matrix.Translation((center[0],-center[1],.02))@Matrix.Rotation(-angle,4,'Z')
    for o in dest.objects:
        if o and o.type in {'MESH','FONT'}:
            bpy.context.scene.collection.objects.link(o);o.matrix_world=transform@o.matrix_world
else:
    bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-kepco-photo-video.blend'))
    g=MuseumGeometry(bpy.context.scene,(0,0),0)
    campus=[local(p) for p in next(w['points'] for w in ways if w['id']=='508052678')]
    buildings=[[local(p) for p in w['points']] for w in ways if w['tags'].get('building')]
    count=0
    for way in ways:
        p=[local(q) for q in way['points']]
        if way['tags'].get('service')=='parking_aisle':
            for a,b in zip(p,p[1:]):
                length=math.dist(a,b)
                if length<8 or max(math.hypot(*a),math.hypot(*b))>400:continue
                ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
                for i in range(2,int(length)-2,3):
                    for side in [-1,1]:
                        x,z=a[0]+ux*i-uz*4*side,a[1]+uz*i+ux*4*side
                        ex,ez=x-uz*4.5*side,z+ux*4.5*side
                        if not inside(ex,ez,campus) or any(inside(ex,ez,q) or inside(x,z,q) for q in buildings):continue
                        g.segment('surroundings_parking_mark',(x,z),(ex,ez),.09,.009,'#edead8',base=.06,record=False);count+=1
        if way['tags'].get('building') and way['id']!='594386007':
            name='campus_context_building_'+way['id']
            if name not in bpy.data.objects:continue
            o=bpy.data.objects[name];height=max(v.co.z for v in o.data.vertices)
            for a,b in zip(p,p[1:]):
                if math.dist(a,b)<5:continue
                for y in range(3,min(60,int(height)),4):
                    g.segment('surroundings_window_band',a,b,.16,1.45,'#7b9298',base=y,record=False)
    # Paving joints and drainage alongside the existing clear arrival axis.
    wpath=root/'public/bitgaram-kepco-world.json';w=json.loads(wpath.read_text(encoding='utf-8'));ex,ez=w['spawn']['x'],w['spawn']['z']
    for z in range(math.ceil(ez),math.ceil(ez)+50,2):
        if inside(ex,z,campus):g.box('surroundings_paving_joint',ex,.025,z,12,.004,.018,'#a3afa7',record=False)
    for dx in [-6,6]:
        for z in range(math.ceil(ez),math.ceil(ez)+45,5):
            if not inside(ex+dx,z,campus):continue
            g.box('surroundings_drain',ex+dx,.035,z,.28,.014,1,'#6a7a74',record=False)
            for q in [-.3,-.1,.1,.3]:g.box('surroundings_drain_slot',ex+dx,.043,z+q,.23,.004,.045,'#3b4d48',record=False)
    w['provenance']['surroundingFinish']='Parking-aisle OSM lines used for estimated parking marks; window bands and paving finishes estimated. Walking elevations and collisions unchanged.'
    wpath.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print('Parking marks',count,flush=True)
    sc=bpy.context.scene;sc.camera.location=g.bp(270,200,330);sc.camera.rotation_euler=(Vector(g.bp(0,45,0))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/f'public/models/bitgaram-{"overview" if overview else "kepco"}.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
if not overview:
    bpy.context.scene.render.filepath=str(root/'outputs/bitgaram/kepco-surroundings-review.png');bpy.ops.render.render(write_still=True)
