"""Photo-informed Bitgaram park and observatory, with OSM plan geometry.
Generated separately from all earlier city and user-edited Blender projects.
"""
import bpy, sys, json, math, random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/bitgaram';OUT.mkdir(exist_ok=True)
DATA=json.loads((ROOT/'knowledge/sources/bitgaram/geometry.json').read_text(encoding='utf-8'))
WAYS={w['id']:w for w in DATA['ways']}
MODE=sys.argv[sys.argv.index('--place')+1] if '--place' in sys.argv else 'bitgaram-park'
TARGET=OUT/(MODE+('-detail' if MODE=='bitgaram-park' else '')+'.blend')
if TARGET.exists() and '--replace-generated' not in sys.argv:raise RuntimeError('Existing model preserved. Use --replace-generated only for generated files.')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;g=MuseumGeometry(s,(0,0),0);rng=random.Random(915)
for old,new in [('01_OSM_Envelope','01_OSM_Plan'),('02_Photo_Interior','02_Photo_Architecture'),('03_Report_Burials','03_Estimated_Landscape'),('04_Estimated_Fixtures','04_Estimated_Fixtures')]:g.groups[old].name=new
def disk(name,x,y,z,rx,rz,h,color,collision=False,n=64):
    return g.polygon(name,[(x+rx*math.cos(i*math.tau/n),z+rz*math.sin(i*math.tau/n)) for i in range(n)],y,h,color,collision)
def tree(x,y,z,k=1):
    g.tube('tree_trunk',(x,y,z),(x,y+4*k,z),.16*k,'#766149')
    for dx,dy,dz,sc in [(0,4,0,1.8),(-1,3.7,.3,1.3),(1,3.8,-.3,1.4)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=k*sc,location=g.bp(x+dx*k,y+dy*k,z+dz*k))
        o=bpy.context.object;o.name='tree_canopy';o.scale=(1,1,.8);o.data.materials.append(g.mat(rng.choice(['#4b6941','#6c874d','#789554'])))
def bench(x,y,z,rot=0):
    for dz in [-.24,-.08,.08,.24]:g.box('bench_wood',x,y+.48,z+dz,1.8,.09,.13,'#967450',rotation=rot,record=False)
    for dx in [-.65,.65]:g.box('bench_leg',x+dx,y+.23,z,.06,.46,.5,'#495251',record=False)
    g.box('bench_back',x,y+.82,z-.3,1.8,.48,.08,'#967450',record=False)
def hill(x,z):return 16*math.exp(-((x/100)**2+(z/105)**2)*1.6)
def curved(name,rx,rz,y,h,color,thick=.18,start=0,end=math.tau,panels=64,collide=False):
    for i in range(panels):
        a=start+(end-start)*i/panels;b=start+(end-start)*(i+1)/panels
        g.segment(name,(rx*math.cos(a),rz*math.sin(a)),(rx*math.cos(b),rz*math.sin(b)),thick,h,color,base=y,collision=collide,record=collide)
def tower(base,interior=False):
    # Elliptical glazing and broad silver rim from exterior photographs; dimensions estimated.
    if not interior:
        disk('tower_core',0,base,0,3.7,3.7,13.7,'#bdc0b9',True)
        for a in [0,math.pi/2,math.pi,3*math.pi/2]:g.tube('tower_column',(8*math.cos(a),base,7*math.sin(a)),(8*math.cos(a),base+14,7*math.sin(a)),.34,'#b7bbb4')
    deck=0 if interior else base+14
    disk('ground_floor_observatory',0,deck-.20,0,13.8,11.4,.20,'#d6d4c9')
    curved('silver_lower_rim',14.1,11.7,deck-.8,.8,'#b4b8b6',.5)
    curved('silver_upper_rim',14.5,12.0,deck+4.5,1.0,'#c8cdca',.6)
    glass=g.mat('#a5cbd1');bs=glass.node_tree.nodes['Principled BSDF'];bs.inputs['Alpha'].default_value=.2;bs.inputs['Roughness'].default_value=.15;glass.surface_render_method='DITHERED'
    curved('panoramic_glazing',13.7,11.3,deck+.12,4.4,'#a5cbd1',.045,collide=True)
    for i in range(48):
        a=i*math.tau/48;x,z=13.7*math.cos(a),11.3*math.sin(a)
        g.tube('window_mullion',(x,deck,z),(x,deck+4.55,z),.055,'#62716f')
    curved('window_transom',13.7,11.3,deck+2.7,.06,'#687671',.08)
    roof=disk('observatory_roof',0,deck+5.4,0,14.5,12,.3,'#d6dbd5');roof['hide_in_overview']=True
    # Central lift core, entrance opening facing south.
    g.box('lift_back',0,deck+1.8,-2.2,5.8,3.6,.18,'#cbc9bc',True)
    for x in [-2.8,2.8]:g.box('lift_side',x,deck+1.8,0,.16,3.6,4.4,'#cbc9bc',True)
    for x in [-2.2,2.2]:g.box('lift_front',x,deck+1.8,2.2,1.1,3.6,.16,'#cbc9bc',True)
    g.box('lift_door',0,deck+1.4,1.9,2.1,2.8,.06,'#878f8d',True)
    g.label('전망실',0,deck+3,2.32,2,.35,color='#344a50')
    for x in range(-12,13,2):
        for z in range(-10,11,2):
            if (x/13.3)**2+(z/11)**2<1:g.box('tile_joint',x,deck+.005,z,.014,.005,1.96,'#b8beb9',record=False)
    for x,z in [(-9,2),(-7,-6),(8,4)]:
        bench(x,deck,z)
        g.tube('telescope_stand',(x+1,deck,z),(x+1,deck+1.2,z),.065,'#777f7c')
        g.tube('telescope',(x+.85,deck+1.35,z+.25),(x+1.35,deck+1.5,z-.5),.14,'#9da6a3')
    for a,text in [(2.8,'호수공원'),(3.7,'한국전력'),(.3,'빛가람동')]:
        x,z=10*math.cos(a),8*math.sin(a)
        g.box('view_guide_stand',x,deck+.56,z,.055,1.12,.07,'#6c7775',record=False)
        g.box('view_guide_panel',x,deck+1.15,z,1.4,.36,.08,'#33585d',record=False)
        g.label(text,x,deck+1.15,z+.055,1.2,.16)
    for x in [-8,0,8]:
        for z in [-6,6]:
            g.box('ceiling_light',x,deck+5.05,z,1.6,.035,.3,'#fff3d8',record=False)
    return deck
def context():
    g.box('context_ground',0,-.6,0,2600,1,2600,'#b4bea4',record=False)
    for way in DATA['ways']:
        tags=way['tags'];pts=way['points'];cx=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
        if abs(cx)>800 or abs(cz)>750:continue
        if tags.get('natural')=='water' and pts[0]==pts[-1]:g.polygon('lake_osm_'+way['id'],pts,-.1,.1,'#447b83')
        elif tags.get('building') and way['id'] not in ['656235304','908801772'] and math.hypot(cx,cz)>160:
            levels=tags.get('building:levels','');height=float(levels)*3 if levels.replace('.','').isdigit() else (38 if tags.get('building')=='apartments' else 13)
            g.polygon('context_building_'+way['id'],pts,0,height,'#a7b2b0')
        elif tags.get('highway') in ['primary','secondary','tertiary','residential']:
            for a,b in zip(pts,pts[1:]):g.segment('context_road',a,b,10,.05,'#8a9493',record=False)
if MODE=='bitgaram-park':
    context()
    verts=[];faces=[];N=51
    for j in range(N):
        z=-150+j*6
        for i in range(N):
            x=-150+i*6;verts.append((x,min(hill(x,z),15.75)+.02,z))
    for j in range(N-1):
        for i in range(N-1):a=j*N+i;faces.extend([(a,a+1,a+N+1),(a,a+N+1,a+N)])
    g.mesh('estimated_hill',verts,faces,'#6f8654',smooth=True)
    disk('ground_floor_summit',0,15.84,0,23,23,.16,'#b9b5a4')
    tower(16)
    # Summit path descends to the exhibition building; stair-sized height intervals are navigable.
    route=[]
    for i in range(121):
        z=16+i*.68;x=12+6*math.sin(i/35);y=16 if z<23 else 16*math.exp(-((z*z-23*23)/105**2)*1.6)
        route.append((x,y,z))
    for i,(a,b) in enumerate(zip(route,route[1:])):
        # Overlap adjoining treads slightly so curved joints cannot open a collision seam.
        g.box('walk-floor_approach',(a[0]+b[0])/2,a[1]-.05,(a[2]+b[2])/2,math.dist(a[::2],b[::2])+.18,.10,3.2,'#baa58a',rotation=math.atan2(b[2]-a[2],b[0]-a[0]))
        if i%8==0:
            for dx in [-1.5,1.5]:g.tube('path_post',(a[0]+dx,a[1],a[2]),(a[0]+dx,a[1]+1.05,a[2]),.045,'#665b48')
        for t in [.25,.5,.75]:
            x=a[0]+(b[0]-a[0])*t;z=a[2]+(b[2]-a[2])*t
            g.box('deck_plank_joint',x,a[1]+.004,z,3.08,.008,.016,'#75644d',rotation=math.atan2(b[2]-a[2],b[0]-a[0])+math.pi/2,record=False)
        if i%20==0:
            g.box('path_bollard',a[0]-1.8,a[1]+.45,a[2],.16,.9,.16,'#45524c',record=False)
            g.box('path_bollard_lens',a[0]-1.8,a[1]+.78,a[2],.18,.14,.18,'#f0e5be',record=False)
    for i in range(0,120,8):
        a=route[i];b=route[min(i+8,120)]
        for dx in [-1.5,1.5]:g.tube('path_handrail',(a[0]+dx,a[1]+1.05,a[2]),(b[0]+dx,b[1]+1.05,b[2]),.05,'#8c7454')
    end=route[-1]
    disk('walk-floor_turnaround',end[0],end[1]-.1,end[2],2.4,2.4,.1,'#baa58a')
    bench(end[0]+1,end[1],end[2]+1)
    for x,z in [(-19,5),(-18,-8),(12,-16)]:bench(x,16,z)
    for i in range(320):
        x=rng.uniform(-115,115);z=rng.uniform(-110,130)
        if math.hypot(x,z)<27 or (4<x<23 and z>12):continue
        tree(x,hill(x,z),z,rng.uniform(1.25,1.95))
    pts=WAYS['908801772']['points'];g.polygon('exhibition_osm',pts,0,6.2,'#c9ccbf',True)
    for x in range(-17,20,3):g.box('exhibition_front_glass',x,2.4,143,2.6,4.3,.08,'#536f73',record=False)
    g.label('빛가람 전망대',0,5.3,143.1,18,1,color='#215d77')
    g.box('entry_sign',10,17.5,16,2.1,1.1,.12,'#284f4c',record=False)
    g.label('전망실 들어가기',10,17.5,16.09,1.9,.2)
    bounds=[-32,34,-30,125];spawn=dict(x=0,z=21,yaw=0);arrivals={'start':dict(x=0,z=21,yaw=0,height=16)}
    places=[dict(id='summit',name='전망대 앞 쉼터',description='전망실 푯말을 누르면 내부로 들어갑니다.',position=[0,20],radius=25,arrival=[0,21],arrivalHeight=16)]
    links=[dict(label='전망실 들어가기',target='bitgaram-observatory'),dict(label='빛가람 안내 지도',target='bitgaram')]
elif MODE=='bitgaram-observatory':
    tower(0,True)
    # Distant city uses the same geographic layout, lowered relative to the high observation floor.
    before=set(bpy.data.objects);context()
    for o in set(bpy.data.objects)-before:o.location.z-=30
    bounds=[-14,14,-12,12];spawn=dict(x=0,z=7,yaw=math.pi);arrivals={}
    places=[dict(id='view',name='빛가람 전망실',description='곡면 유리창을 따라 호수와 시가지를 바라보세요.',position=[0,0],radius=16,indoor=True,arrival=[0,7],arrivalHeight=0)]
    links=[dict(label='전망대 밖으로',target='bitgaram-park'),dict(label='빛가람 안내 지도',target='bitgaram')]
else:raise ValueError(MODE)
world=dict(title='나주 산책',subtitle=MODE,source=DATA['source'],bounds=bounds,spawn=spawn,arrivals=arrivals,solids=g.solids,signs=g.signs,places=places,verticalNavigation=True,requireFloor=True,sceneLinks=links,lighting=dict(exposure=1.1,ambient=1.6,sun=2.3),limitations=['OSM plan geometry; photo-informed architecture; estimated heights and furnishings.'])
if MODE=='bitgaram-park':world['spawn']['height']=16
(ROOT/'public'/f'{MODE}-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
bpy.ops.object.light_add(type='SUN',location=(0,0,150));sun=bpy.context.object;sun.data.energy=2;sun.rotation_euler=(.5,-.4,-.6)
s.world=bpy.data.worlds.new('Bitgaram daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.65,.8,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.5
eye=(60,60,85) if MODE=='bitgaram-park' else (7,1.7,7);target=(0,24,0) if MODE=='bitgaram-park' else (8,1.7,-5)
bpy.ops.object.camera_add(location=g.bp(*eye));cam=bpy.context.object;cam.rotation_euler=(Vector(g.bp(*target))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.clip_end=3000;s.camera=cam
if MODE=='bitgaram-observatory':cam.data.lens=22
s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1400;s.render.resolution_y=950;s.render.resolution_percentage=100
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models'/f'{MODE}.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
if '--render' in sys.argv:
    bpy.ops.wm.open_mainfile(filepath=str(TARGET));bpy.context.scene.render.filepath=str(OUT/f'{MODE}.png');bpy.ops.render.render(write_still=True)
print(MODE,len(world['solids']))
