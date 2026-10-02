"""Separate first-floor walks. OSM footprints; public-photo facade/lobby details."""
import bpy, json, math, sys, random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/bitgaram';OUT.mkdir(exist_ok=True)
MODE=sys.argv[sys.argv.index('--place')+1];K=MODE=='bitgaram-kentech'
assert MODE in ['bitgaram-kentech','bitgaram-kepco']
TARGET=OUT/(MODE+'.blend')
if TARGET.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing model preserved')
data=json.loads((ROOT/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
way=next(w for w in data['ways'] if w['id']==('1065747586' if K else '594386007'))
raw=way['points'][:-1];center=[sum(p[i] for p in raw)/len(raw) for i in [0,1]]
# The local scene retains the actual footprint but rotates its dominant facade toward the visitor.
edge=max(zip(raw,raw[1:]+raw[:1]),key=lambda ab:math.dist(*ab));angle=math.atan2(edge[1][1]-edge[0][1],edge[1][0]-edge[0][0])
c,st=math.cos(angle),math.sin(angle)
pts=[[(x-center[0])*c+(z-center[1])*st,-(x-center[0])*st+(z-center[1])*c] for x,z in raw]
x0,x1=min(p[0] for p in pts),max(p[0] for p in pts);z0,z1=min(p[1] for p in pts),max(p[1] for p in pts)
w=x1-x0;d=z1-z0;h=18 if K else float(way['tags'].get('height',154));floorH=4.4 if K else 7.5
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;g=MuseumGeometry(s,(0,0),0);rng=random.Random(22)
g.box('ground_floor_plaza',0,-.1,0,w+50,.2,d+60,'#c7ccc6')
g.polygon('ground_floor_lobby',pts,-.08,.08,'#dddcd2')
podiumH=h if K else 17
g.polygon('upper_building_envelope',pts,floorH,podiumH-floorH,'#91aab0',True,group='05_Cutaway_Roof')
if not K:
    # OSM gives the combined podium outline. Satellite/photos distinguish a narrow tall central tower.
    g.box('central_tower',9,(h+17)/2,-5,49,h-17,38,'#6b8d9d',True,group='05_Cutaway_Roof')
    for x in range(-15,35,5):
        for z in [-24.2,14.2]:
            o=g.box('tower_vertical_fin',x,(h+17)/2,z,.5,h-17,.3,'#d5d8d4',record=False);o['hide_in_overview']=True
    for y in range(20,153,4):
        for z in [-24.2,14.2]:
            o=g.box('tower_storey',9,y,z,49,.35,.3,'#adc0c3',record=False);o['hide_in_overview']=True
    g.tube('diagonal_facade_fin',(-14,149,14.5),(-4,18,14.5),.3,'#e3e6db')
    g.label('한국전력 KEPCO',10,146,14.6,35,3,color='#f3efe2')
glass=g.mat('#91bdc3');glass.surface_render_method='DITHERED';glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.2
metal=g.mat('#a9b1ae');metal.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.75;metal.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.26
# Entrance on the southern perimeter segment closest to its centre.
edges=list(zip(pts,pts[1:]+pts[:1]));entrance=max(range(len(edges)),key=lambda i:(edges[i][0][1]+edges[i][1][1])/2)
ea,eb=edges[entrance];mid=((ea[0]+eb[0])/2,(ea[1]+eb[1])/2);doorwidth=min(4,math.dist(ea,eb)*.3)
for ei,(a,b) in enumerate(edges):
    length=math.dist(a,b);n=max(1,math.ceil(length/1.5))
    for j in range(n):
        t0=j/n;t1=(j+1)/n;pa=[a[q]+(b[q]-a[q])*t0 for q in [0,1]];pb=[a[q]+(b[q]-a[q])*t1 for q in [0,1]]
        atDoor=ei==entrance and abs((t0+t1)/2-.5)*length<doorwidth/2
        if not atDoor:g.segment('first_floor_glass',pa,pb,.08,floorH,'#91bdc3',collision=True)
        g.tube('facade_vertical_frame',(pa[0],0,pa[1]),(pa[0],podiumH,pa[1]),.075 if K else .14,'#ccd2c9')
        if not K and j%3==0:g.segment('facade_silver_fin',pa,pb,.25,podiumH-floorH,'#d7d9cf',base=floorH,record=False)
    for y in ([4.4,8.8,13.2,17.7] if K else [floorH+4.5*i for i in range(33)]):
        if y>podiumH:continue
        o=g.segment('floor_band',a,b,.7 if K else .16,.6 if K else .16,'#d5d4c8',base=y,record=False)
        o['hide_in_overview']=y>floorH
g.box('entry_canopy',mid[0],3.5,mid[1]+1.6,doorwidth+3,.22,3.6,'#7b8b8c',record=False)
for dx in [-doorwidth/2,doorwidth/2]:g.box('door_frame',mid[0]+dx,1.7,mid[1],.09,3.4,.12,'#53666b',True)
g.label('KENTECH' if K else '한국전력 KEPCO',mid[0],4.1,mid[1]+.2,doorwidth+6,.6,color='#264c65')
g.label('1층 로비',mid[0],2.8,mid[1]+.1,2,.25,color='#304e59')
if K:
    g.box('blue_facade_insert',2,9,mid[1]+.65,5.5,9,.6,'#518eaf',record=False)
    for y in [5,7,9,11,13]:g.box('blue_panel_joint',2,y,mid[1]+.97,5.5,.025,.03,'#385e75',record=False)
    g.box('ground_name_board',-9,.8,z1+1,4,1.6,.18,'#e7e6d7',True)
    g.label('KENTECH',-9,1,z1+1.12,3.6,.45,color='#285d77')
    g.label('한국에너지공과대학교',-9,.45,z1+1.12,3.7,.21,color='#405e64')
# Ceiling and joint lines; upper floors are architectural context only.
roof=g.polygon('lobby_ceiling',pts,floorH-.14,.14,'#e1e1d6',group='05_Cutaway_Roof')
for x in range(math.ceil(x0),math.floor(x1),3):
    for z in range(math.ceil(z0),math.floor(z1),3):
        # Only position furniture/lights well within the convex facade bounds below.
        if abs(x)<w*.35 and abs(z)<d*.32:
            g.box('ceiling_lamp',x,floorH-.2,z,.7,.035,.18,'#fff1ce',record=False)
            if (x//3+z//3)%4==0:g.lights.append(dict(position=[x,floorH-.55,z],color='#fff1dc',intensity=7,distance=12))
for x in range(math.ceil(x0),math.floor(x1),2):g.box('floor_joint',x,.003,0,.01,.004,d*.9,'#bfc6be',record=False)
for z in range(math.ceil(z0),math.floor(z1),2):g.box('floor_joint',0,.003,z,w*.9,.004,.01,'#bfc6be',record=False)
# Public circulation front portion; back wall deliberately closes unreferenced rooms.
back=z0+d*.38
g.box('public_lobby_back_wall',0,floorH/2,back,w*.72,floorH,.2,'#e3dfd2',True)
if not K:
    for x in [-w*.23,0,w*.23]:
        for z in [back+4,8]:g.tube('metal_lobby_column',(x,0,z),(x,floorH,z),.48,'#a9b1ae')
    g.box('information_counter',-w*.20,.55,back+1.4,5,1.1,1.2,'#e7e6da',True)
    g.box('information_worktop',-w*.20,1.13,back+1.4,5.1,.08,1.3,'#545d59',record=False)
    g.box('information_screen',0,3.7,back+.13,5.4,2.3,.08,'#537f9e',record=False)
    g.label('한국전력',0,3.8,back+.2,4,.55)
    for x in [w*.1,w*.16,w*.22]:g.box('entry_gate',x,.52,back+1.5,.25,1.04,1.2,'#9ca9a4',True)
else:
    # Only the exterior is directly photo verified; this small lobby is an explicit circulation estimate.
    g.box('entry_information',-w*.20,.48,back+1.1,3.6,.96,.9,'#af9772',True)
    g.label('KENTECH',0,2.7,back+.14,5,.65,color='#235b72')
    g.label('한국에너지공과대학교',0,1.95,back+.14,5,.28,color='#356777')
for x in [-w*.28,w*.28]:
    for z in [z1-3,back+3]:
        g.box('planter',x,.35,z,.8,.7,.8,'#d9d4bd',True)
        g.tube('palm_trunk',(x,.7,z),(x,2.4,z),.12,'#846950')
        for i in range(9):
            a=i*math.tau/9;g.mesh('palm_leaf',[(x,2.3,z),(x+.8*math.cos(a-.2),2.65,z+.8*math.sin(a-.2)),(x+1.1*math.cos(a),2.5,z+1.1*math.sin(a)),(x+.8*math.cos(a+.2),2.65,z+.8*math.sin(a+.2))],[(0,1,2,3)],'#43694b')
for x in [-w*.32,w*.32]:
    g.box('lobby_bench',x,.4,(z1+back)/2,2.3,.4,.75,'#8f9890',True)
for x in [-w*.35,w*.35]:
    g.box('entry_garden',x,.06,z1+10,8,.12,12,'#7d9467',True)
    for j in range(3):
        z=z1+6+j*4;g.tube('plaza_tree_trunk',(x,0,z),(x,3.8,z),.13,'#79684d')
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1.6,location=g.bp(x,4,z));bpy.context.object.data.materials.append(g.mat('#637f4b'))
spawn=dict(x=mid[0],z=mid[1]+9,yaw=0)
world=dict(title='나주 산책',subtitle=MODE,source=data['source'],bounds=[x0-14,x1+14,z0-12,z1+24],spawn=spawn,solids=g.solids,signs=g.signs,places=[dict(id='entrance',name=('KENTECH' if K else '한국전력 본사')+' 입구',description='정문을 통해 1층 로비를 둘러보세요.',position=[spawn['x'],spawn['z']],radius=8,arrival=[spawn['x'],spawn['z']]),dict(id='lobby',name='1층 로비',description='공개 사진 참고 · 치수와 세부 배치 추정',position=[mid[0],mid[1]-5],radius=5,arrival=[mid[0],mid[1]-5],indoor=True)],verticalNavigation=True,requireFloor=True,sceneLinks=[dict(label='빛가람 안내 지도',target='bitgaram')],lighting=dict(exposure=1.1,ambient=1.65,sun=1.4),lights=g.lights,provenance=dict(osmWay=way['id'],angle=angle,geographicOrigin=way['coordinates'][0],heightSource='OSM max height=154; podium/tower split photo-estimated' if not K else 'photo-estimated 4 floors',interiorPhotoAvailable=not K,limitations='1F circulation and dimensions estimated; no upper-floor access'))
(ROOT/'public'/f'{MODE}-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
s.world=bpy.data.worlds.new('Institution daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.75,.85,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=(0,0,100));bpy.context.object.data.energy=2;bpy.context.object.rotation_euler=(.4,-.4,-.4)
for pos in [(0,floorH-1,z1-4),(-w*.2,floorH-1,back+4),(w*.2,floorH-1,back+4)]:
    bpy.ops.object.light_add(type='AREA',location=g.bp(*pos));o=bpy.context.object;o.data.energy=1600;o.data.size=9
bpy.ops.object.camera_add(location=g.bp(w*.7,30 if K else 100,z1+(70 if K else 230)));cam=bpy.context.object;cam.data.lens=32;cam.data.clip_end=1500;cam.rotation_euler=(Vector(g.bp(0,h*.4,0))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1400;s.render.resolution_y=950;s.render.resolution_percentage=100
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models'/f'{MODE}.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
if '--render' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(TARGET));s=bpy.context.scene;s.render.filepath=str(OUT/f'{MODE}.png');bpy.ops.render.render(write_still=True)
    cam=s.camera;cam.location=g.bp(mid[0]+4,1.7,min(mid[1]-4,10));cam.data.lens=20;cam.rotation_euler=(Vector(g.bp(-w*.12,2.0,back+1))-cam.location).to_track_quat('-Z','Y').to_euler();s.view_settings.exposure=.8;s.render.filepath=str(OUT/f'{MODE}-lobby.png');bpy.ops.render.render(write_still=True)
print(MODE,'footprint',w,d,'entrance',mid,'objects',len(s.objects))
