"""Blender authors the present four-storey tower, real river geometry and walk floors."""
import bpy,math,json,sys,random,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry,world_data,place
from scene_export_v91 import surface,export,helpers
O=R/'outputs/neureoji-v92';O.mkdir(parents=True,exist_ok=True)
W=R/'work/neureoji-v92';D=json.loads((W/'mesh.json').read_text());G=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
B=D['padHeight'];TARGET=O/'neureoji-v92a.blend';rng=random.Random(9231)
if TARGET.exists():raise RuntimeError('Preserve saved revision; use a new refinement script')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;g=Geometry(s);route=[[3.2,14,B],[3.2,6,B]]
def keep(o):o['keep_web']=True;return o
def finish(o,kind='metal'):
    if kind=='metal':
        for m in o.data.materials:
            bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=.25;bs.inputs['Roughness'].default_value=.43
    else:surface(o,kind)
    return o
def floor(name,x,z,w,d,y):return finish(g.box('walk-floor_'+name,x,y-.07,z,w,.14,d,'#b7b6a2',record=True),'concrete')
def rail(a,b,ya,yb,name='stair'):
    g.tube('tower_'+name+'_handrail',(a[0],ya+1.08,a[1]),(b[0],yb+1.08,b[1]),.045,'#63482d',n=10)
    count=max(1,math.ceil(math.dist(a,b)/.22))
    for i in range(count+1):
        t=i/count;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t;y=ya+(yb-ya)*t
        g.box('tower_'+name+'_timber_baluster',x,y+.52,z,.055,1.04,.055,'#78583a',record=False)
    # Height-aware short collision spans prevent falling without blocking a flight below.
    for i in range(max(1,math.ceil(math.dist(a,b)/.7))):
        n=max(1,math.ceil(math.dist(a,b)/.7));t=i/n;v=(i+1)/n
        aa=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t);bb=(a[0]+(b[0]-a[0])*v,a[1]+(b[1]-a[1])*v)
        y=ya+(yb-ya)*(t+v)/2
        dx,dz=bb[0]-aa[0],bb[1]-aa[1];l=math.hypot(dx,dz);ux,uz=-dz/l*.06,dx/l*.06
        g.collider('tower_'+name+'_guard',[[aa[0]+ux,aa[1]+uz],[bb[0]+ux,bb[1]+uz],[bb[0]-ux,bb[1]-uz],[aa[0]-ux,aa[1]-uz]],y+.08,1.05,'#76593c')
# Original terrain finish is vector-derived; no aerial photography is embedded.
terrain=g.mesh('ground_native_DSM_interpreted',D['vertices'],D['faces'],'#a3af77',smooth=True);terrain['keep_web']=True;terrain['no_shadow']=True
mat=terrain.data.materials[0];img=bpy.data.images.load(str(W/'original-landcover.png'));img.pack();node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
uv=terrain.data.uv_layers.active
for li,loop in enumerate(terrain.data.loops):
    v=terrain.data.vertices[loop.vertex_index].co;uv.data[li].uv=((v.x+3100)/6200,(-v.y+2700)/5000)
water=keep(g.mesh('mapped_river_water_neureoji',D['waterVertices'],D['waterFaces'],'#447779'));finish(water,'water');water['no_shadow']=True
for p in G['water']:g.solids.append(dict(name='mapped_river_water_background',kind='building',position=[0,.06,0],size=[1,.02,1],footprint=p['points'],color='#447779',collision=False))
# Efficient true 3D canopy clusters follow mapped woodland / elevated DSM ground.
colors=['#486446','#52704b','#638451','#748c57','#56754d'];by=[([],[]) for _ in colors]
for x,y,z,h,c in D['forest']:
    verts,faces=by[c];r=h*.35;a=len(verts)
    for j in range(6):
        theta=math.pi*j/5;rr=math.sin(theta)*r;yy=y+h*.60+math.cos(theta)*h*.40
        for i in range(9):
            angle=math.tau*i/9;verts.append((x+rr*math.cos(angle),yy,z+rr*math.sin(angle)))
    for j in range(5):
        for i in range(9):q=a+j*9+i;faces.append((q,a+j*9+(i+1)%9,a+(j+1)*9+(i+1)%9,q+9))
for c,(verts,faces) in enumerate(by):
    ob=keep(g.mesh('background_forest_canopy_'+str(c),verts,faces,colors[c],smooth=True));ob['no_shadow']=True
# Roads and mapped roofs remain distant context, outside every walk floor.
for p in G['roads']:
    if p['tags'].get('highway') not in ['secondary','tertiary','residential','unclassified']:continue
    for a,b in zip(p['points'],p['points'][1:]):
        # Sample the native prepared mesh by nearest grid vertex.
        x,z=(a[0]+b[0])/2,(a[1]+b[1])/2;i=max(0,min(248,round((x+3100)/25)));j=max(0,min(200,round((z+2700)/25)));hh=D['vertices'][j*249+i][1]+.16
        ob=g.segment('context_road',a,b,5,.025,'#a3a398',base=hh,record=False);ob['no_shadow']=True
for p in G['buildings']:
    points=p['points'];x=sum(q[0] for q in points)/len(points);z=sum(q[1] for q in points)/len(points);i=max(0,min(248,round((x+3100)/25)));j=max(0,min(200,round((z+2700)/25)));hh=D['vertices'][j*249+i][1]
    ob=g.polygon('context_mapped_building',points,hh,3.2,rng.choice(['#d4d1bb','#c3c8b8','#b9bdaf']));ob['no_shadow']=True
    ob=g.polygon('context_mapped_roof',points,hh+3.2,.08,rng.choice(['#64858c','#6c7771','#a38b6e']));ob['no_shadow']=True
# Ground approach and three alternating stair flights.
floor('tower_pad',1,4,12,28,B);floor('approach',3.2,17,2.2,10,B)
for x in (2,4.4):
    for z in (-3.25,7.25):
        finish(g.box('tower_steel_column',x,B+5.5,z,.26,11,.26,'#e5e7e1',True))
        for y in [B,B+3.6,B+7.2,B+10.8]:finish(g.box('tower_column_baseplate',x,y+.06,z,.42,.06,.42,'#c7cec9',record=False))
        for dz in [-.12,.12]:
            for dx in [-.12,.12]:g.vessel('tower_anchor_bolt',x+dx,B+.095,z+dz,.07,'#9da7a1',profile=[(0,.55),(.45,.55),(.45,.35),(.8,.35)])
for k in range(3):
    y0=B+k*3.6;start=5.6 if k%2==0 else -1.6;end=-1.6 if k%2==0 else 5.6
    if k==0:route.append([3.2,start,y0])
    for i in range(20):
        t=(i+.5)/20;z=start+(end-start)*t;y=y0+(i+1)*.18
        floor('stair_%d_%02d'%(k,i),3.2,z,2.16,.361,y);route.append([3.2,z,y])
        # Nosing, lower riser and two steel stringers are distinct close-up geometry.
        g.box('tower_tread_nosing',3.2,y+.012,z-.17*(1 if k%2==0 else -1),2.16,.023,.035,'#deded3',record=False)
        g.box('tower_tread_riser',3.2,y-.09,z+.17*(1 if k%2==0 else -1),2.16,.18,.025,'#aab3af',record=False)
    for x in [2.08,4.32]:
        finish(g.tube('tower_stair_stringer',(x,y0-.09,start),(x,y0+3.6-.09,end),.11,'#d2d8d4',n=8))
        rail((x,start),(x,end),y0,y0+3.6)
    zlanding=-2.4 if k%2==0 else 6.4;yy=y0+3.6
    floor('landing_%d'%k,3.2,zlanding,2.7,1.6,yy);route.append([3.2,zlanding,yy])
    for x in [1.85,4.55]:
        if k!=2 or x>3:rail((x,zlanding-.8),(x,zlanding+.8),yy,yy,'landing')
    outerz=zlanding+(-.8 if k%2==0 else .8);rail((1.85,outerz),(4.55,outerz),yy,yy,'landing')
    if k<2:
        route.append([3.2,end,yy])
    finish(g.box('tower_landing_crossbeam',3.2,yy-.2,zlanding,2.8,.28,1.7,'#dde2dd',record=False))
    for x in [2,4.4]:
        g.tube('tower_diagonal_tension_brace',(x,B+k*3.6,-3.25),(x,B+(k+1)*3.6,7.25),.035,'#a9b3ac',n=8)
# Short connector rises into the circular observation floor.
for i in range(8):
    x=3.2-(i+.5)*.25;y=B+10.8+(i+1)*.15
    floor('top_connector_%02d'%i,x,-2.4,.251,1.65,y);route.append([x,-2.4,y])
for z in [-3.24,-1.56]:rail((3.2,z),(1.2,z),B+10.8,B+12,'connector')
cx,cz=-.65,-2.4;top=B+12;r=2.8
circle=[(cx+math.cos(i*math.tau/64)*r,cz+math.sin(i*math.tau/64)*r) for i in range(64)]
deck=keep(g.polygon('walk-floor_top_deck',circle,top-.18,.18,'#bbbdb3'));finish(deck,'concrete');route.extend([[1.1,-2.4,top],[0,-2.4,top],[-1.6,-3.0,top]])
g.tube('tower_round_deck_central_support',(cx,B,cz),(cx,top-.18,cz),.20,'#e3e7df',n=24)
for x,z in [(cx-1.5,cz-1.1),(cx+1.5,cz-1.1),(cx,cz+1.8)]:
    finish(g.tube('tower_view_support',(x,B,z),(x,top-.12,z),.14,'#e0e5de',n=12))
for i in range(48):
    a=i*math.tau/48;b=(i+1)*math.tau/48
    if math.cos((a+b)/2)>.85:continue # connector opening to the east
    p=(cx+math.cos(a)*r,cz+math.sin(a)*r);q=(cx+math.cos(b)*r,cz+math.sin(b)*r)
    rail(p,q,top,top,'round_deck')
# White curved lower fascia, yellow/blue identity text; interior remains open.
v=[];f=[]
for i in range(65):
    a=i*math.tau/64
    for y in [top-.85,top-.08]:v.append((cx+math.cos(a)*r,y,cz+math.sin(a)*r))
for i in range(64):f.append((i*2,i*2+1,i*2+3,i*2+2))
finish(g.mesh('tower_curved_fascia',v,f,'#e8ebe3',smooth=True))
g.label('느러지',cx,top-.25,cz+r+.026,2.1,.26,color='#c6a848');g.label('전망대',cx,top-.62,cz+r+.026,2.1,.31,color='#37648b')
roofY=B+14.3
for i in range(6):
    a=i*math.tau/6;x=cx+math.cos(a)*2.45;z=cz+math.sin(a)*2.45
    g.tube('tower_roof_upright',(x,top,z),(x,roofY-.11,z),.055,'#dce3dd',n=10)
    g.tube('tower_canopy_radial_rib',(cx,roofY+.22,cz),(cx+math.cos(a)*3.2,roofY,z+(cz-z)*0),.045,'#e1e6e0',n=8)
g.vessel('tower_canopy',cx,roofY,cz,1,'#e0e5df',profile=[(0,3.30),(.075,3.30),(.20,.22),(.22,0)])
g.tube('tower_finial',(cx,roofY+.18,cz),(cx,B+15.35,cz),.032,'#bcc7bf',n=10)
for i in range(4):
    a=i*math.tau/4;g.tube('tower_finial_brace',(cx+math.cos(a)*.70,roofY+.13,cz+math.sin(a)*.70),(cx,B+15.1,cz),.025,'#ccd4cd',n=8)
for i in range(3):
    x=cx-1.2+i*1.05
    finish(g.box('tower_view_bench',x,top+.42,cz+1.85,.90,.07,.38,'#73583b',True),'wood')
    for dx in [-.33,.33]:g.box('tower_bench_leg',x+dx,top+.20,cz+1.85,.065,.4,.28,'#d8ded6',record=False)
# Hydrangeas and nearby trees are observed categories with inferred individual planting.
for side in [-1,1]:
    for i in range(13):
        x=3.2+side*rng.uniform(1.8,3.6);z=8+i*.72;y=B
        g.rock('hydrangea_bush',x,y+.47,z,1.15,.86,1.1,rng.choice(colors),rng)
        for j in range(8):
            xx=x+rng.uniform(-.43,.43);zz=z+rng.uniform(-.43,.43);yy=y+rng.uniform(.62,.93)
            for k in range(7):
                a=k*math.tau/7;g.rock('hydrangea_floret',xx+.08*math.cos(a),yy+rng.uniform(-.025,.025),zz+.08*math.sin(a),.08,.05,.07,rng.choice(['#bbc4de','#d8c3d9','#9dabc9']),rng)
for i in range(24):
    a=rng.random()*math.tau;rr=rng.uniform(12,45);x=math.cos(a)*rr;z=math.sin(a)*rr
    if z>5 and abs(x-3.2)<4:continue
    size=rng.uniform(1.5,2.25);treeg=Geometry(s);treeg.tree('near_deciduous_tree',x,z,size,i+92)
    for ob in list(treeg.groups['02_Photo_Interior'].objects):ob.location.z+=B-2;ob['vegetation_lod']='near'
    # Use the existing authored leaf geometry/atlas, never a source photograph.
helpers['key']='neureoji';helpers['vegetation']()
for o in s.objects:
    if o.type=='MESH' and ('timber_baluster' in o.name or 'handrail' in o.name):finish(o,'wood')
for f in bpy.data.fonts:
    if f.filepath and Path(f.filepath).is_file() and not f.packed_file:f.pack()
places=[place('tower-entry','계단 입구',3.2,12,3,arrivalHeight=B),place('tower-third','중간 전망 쉼터',3.2,6.4,1,arrivalHeight=B+7.2),place('peninsula-view','한반도 지형 전망',-1.6,-3,1,arrivalHeight=top)]
world=world_data(g,'느러지 전망대',[-7,8,-7,23],dict(x=3.2,z=14,yaw=0,height=B),places,
    verticalNavigation=True,requireFloor=True,walkRoute=route,arrivals={'top':dict(x=-1.6,z=-3,yaw=.76,height=top)},
    lighting=dict(exposure=1.12,ambient=1.8,sun=3),sceneLinks=[],
    architectureViews=[dict(id='tower',label='전망대 전체',center=[.7,B+7,1],radius=29,elevation=.35,angle=-.6),dict(id='peninsula',label='정상에서 보는 한반도',center=[-1.6,top+1.72,-3],radius=.01,elevation=.045,angle=.76,fov=58)],
    geographicOrigin=G['originWGS84'],backgroundBounds=G['bounds'],towerHeightMetres=15.35,topDeckHeightMetres=top,
    revision='neureoji-v92a',limitations=['현재 4층 철골 전망대. 향후 계획된 45m 전망타워와 구분.', '계단·난간·원형 데크 치수와 개별 식재는 사진 기반 추정.', '30m DSM에서 수관 8m를 감한 지면 추정. 지면 측량 자료 아님.', '영산강 윤곽은 OSM, 지형은 Copernicus GLO-30. 들판 재질과 작물 색상은 자체 제작 해석.'])
(R/'public/neureoji-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
s['reference_basis']='OSM node 6572786690 / mapped river / GLO-30 DSM / 2024 visitor photos, inferred tower dimensions'
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
stats=export('neureoji',O)
report=dict(revision='neureoji-v92a',blend=str(TARGET.relative_to(R)),geography='knowledge/sources/neureoji-v92/geography.json',terrain='knowledge/sources/neureoji-v92/native-terrain.json',
    origin=G['originWGS84'],waterArea=D['waterArea'],padHeight=B,topHeight=top,walkingBounds=world['bounds'],backgroundBounds=G['bounds'],export=stats,assumptions=world['limitations'])
(R/'knowledge/sources/neureoji-v92/model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NEUREOJI_COMPLETE',json.dumps(stats),flush=True)
