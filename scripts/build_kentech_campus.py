"""KENTECH campus: mapped footprints, photo-informed facades, estimated 1F circulation.
Preserves older artist files. The editable scene is saved before export-only batching.
"""
import bpy,bmesh,sys,math,json,random,gzip,re
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];S=R/'knowledge/sources/kentech-v52';O=R/'outputs/kentech';O.mkdir(exist_ok=True)
target=O/'kentech-campus-v52.blend'
if target.exists():raise RuntimeError('Existing Blender revision preserved')
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(5209)
data=json.loads((S/'geometry.json').read_text(encoding='utf8'));ways={w['id']:w for w in data}
def geo(p):return ((p[0]-126.803269)*91175,(35.010582-p[1])*111195)
def poly(id):
    pts=[geo(p) for p in ways[str(id)]['points']]
    return pts[:-1] if pts[0]==pts[-1] else pts
def inside(p,pts):
    x,z=p;hit=False
    for a,b in zip(pts,pts[1:]+pts[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit
def box(n,x,y,z,w,h,d,c,collision=False,record=False):return g.box(n,x,y,z,w,h,d,c,collision,record=record or collision)
def seg(n,a,b,w,h,c,base=0,collision=False):return g.segment(n,a,b,w,h,c,base,collision,record=collision)
def path(n,pts,width=3,color='#c8c4b8',y=.036):
    for a,b in zip(pts,pts[1:]):seg(n,a,b,width,.045,color,y)
def circle(n,x,z,r,y,color):
    pts=[(x+r*math.cos(i*math.tau/64),z+r*math.sin(i*math.tau/64)) for i in range(64)]
    return g.polygon(n,pts,y,.015,color)
def line(n,pts,w=.10,y=.125,c='#f1efdf'):path(n,pts,w,c,y)
def solar(x,z,y,nx,nz):
    for i in range(nx):
        for j in range(nz):
            px=x+i*2.25;pz=z+j*3.2
            box('roof_solar_frame',px,y,pz,2.08,.15,2.68,'#a8b5b5')
            box('roof_solar_module',px,y+.10,pz,1.94,.08,2.51,'#24485d')
            for dx in [-.47,0,.47]:box('photovoltaic_cell_joint',px+dx,y+.15,pz,.013,.009,2.49,'#72909f')
            box('photovoltaic_cell_joint',px,y+.15,pz,1.93,.009,.02,'#72909f')
def bench(x,z,rot=0):
    for j in range(5):g.box('campus_bench_slat',x,.47,z+(j-2)*.11,1.85,.09,.095,'#907553',rotation=rot,record=False)
    for dx in [-.65,.65]:box('bench_support',x+dx,.23,z,.12,.46,.48,'#465355')
    g.collider('bench_obstacle',[(x-.96,z-.32),(x+.96,z-.32),(x+.96,z+.32),(x-.96,z+.32)],0,.56)
def lamp(x,z):
    g.tube('campus_lamp_post',(x,0,z),(x,4.5,z),.055,'#525b5a',n=6)
    box('campus_lamp_head',x+.23,4.46,z,.58,.13,.28,'#657275')
    box('campus_lamp_diffuser',x+.23,4.39,z,.42,.035,.20,'#fff0d0')
    g.collider('lamp_obstacle',[(x-.1,z-.1),(x+.1,z-.1),(x+.1,z+.1),(x-.1,z+.1)],0,4.5)
canopies={}
for color in ['#537647','#698847','#789450','#4b6b44']:
    mesh=bpy.data.meshes.new('Shared_young_tree_'+color);bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1);bm.to_mesh(mesh);bm.free();mesh.materials.append(g.mat(color))
    for face in mesh.polygons:face.use_smooth=True
    canopies[color]=mesh
def tree(x,z,h=5):
    g.tube('young_tree_trunk',(x,0,z),(x,h*.78,z),.105,'#79694f',n=7)
    for a in [0,2.1,4.2]:g.tube('young_tree_branch',(x,h*.5,z),(x+.95*math.cos(a),h*.85,z+.95*math.sin(a)),.055,'#827253',n=6)
    for dx,dz,hh,rr in [(0,0,.82,.25),(.65,.1,.75,.19),(-.5,.35,.73,.20),(.15,-.65,.72,.18)]:
        o=bpy.data.objects.new('campus_young_canopy',canopies[rng.choice(list(canopies))]);scene.collection.objects.link(o);o.location=g.bp(x+dx,h*hh,z+dz);o.scale=(h*rr,h*rr,h*rr*1.2)
    for a in [0,math.tau/3,math.tau*2/3]:g.tube('tree_tripod_stake',(x+.68*math.cos(a),0,z+.68*math.sin(a)),(x,1.65,z),.026,'#ad9170',n=5)
    g.collider('tree_trunk',[(x-.13,z-.13),(x+.13,z-.13),(x+.13,z+.13),(x-.13,z+.13)],0,h*.7)

# OSM coordinates remain north-up; all heights and surface treatments are estimates.
g.box('ground_floor_campus',40,-.14,0,620,.28,690,'#98a274')
g.box('campus_ground_context',30,-.4,-10,940,.3,980,'#99a184',record=False)
build_ids=['1065747586','1201084332','1460776854','1460776855','1476045296','1476045297','1476045298','1476045299','1476045300','1092517581','1265544133']
footprints=[poly(i) for i in build_ids]
roads=[]
for w in data:
    t=w['tags'];pts=[geo(p) for p in w['points']]
    if not pts:continue
    if t.get('highway'):
        kind=t['highway'];width=3 if kind in ['footway','path'] else 5 if kind=='service' else 12 if kind in ['residential','unclassified'] else 18
        for a,b in zip(pts,pts[1:]):
            if min(a[0],b[0])<-265 or max(a[0],b[0])>340 or min(a[1],b[1])<-340 or max(a[1],b[1])>320:continue
            seg('campus_road_verge',a,b,width+3,.05,'#cfcebf',.012)
            seg('campus_road_asphalt',a,b,width,.035,'#697373',.072)
            roads.append((a,b,width))
            if width>=12:
                ll=math.dist(a,b)
                for i in range(max(1,int(ll/10))):
                    t0=i/max(1,int(ll/10));t1=min(1,t0+3/ll)
                    line('road_center_dash',[[a[q]+(b[q]-a[q])*t for q in [0,1]] for t in [t0,t1]],.14,.113)
    if t.get('amenity')=='parking':
        if not all(-250<x<320 and -340<z<300 for x,z in pts):continue
        g.polygon('campus_parking_'+w['id'],pts,.023,.06,'#838b85')
        xs=[p[0] for p in pts];zs=[p[1] for p in pts]
        for x in range(math.ceil(min(xs))+3,math.floor(max(xs))-3,3):
            for z in range(math.ceil(min(zs))+6,math.floor(max(zs))-6,15):
                if all(inside(p,pts) for p in [(x,z),(x+2.4,z+5)]):
                    line('parking_bay',[(x,z+5),(x,z),(x+2.4,z)],.08,.102)
                    if rng.random()<.18:
                        box('parked_vehicle',x+1.15,.7,z+2.5,1.75,1.22,4.1,rng.choice(['#dcdedb','#e9e7dc','#63757b','#344f66']))
                        box('vehicle_roof',x+1.15,1.36,z+2.6,1.55,.54,2.15,'#799398')

print('BUILD terrain and mapped roads ready',len(scene.objects),flush=True)
# Main quad, reflecting the triangular paths visible in completed-building photographs.
box('campus_ground_main_plaza',43,.055,24,153,.11,20,'#d3d2c7')
for pts in [[(-20,34),(104,34),(104,89),(8,89)],[(121,111),(131,111),(131,292),(113,281)]]:g.polygon('campus_ground_lawn',pts,.018,.012,'#82945e')
for pts,w in [([(-18,22),(8,90),(104,90)],4),([(-18,22),(104,22)],6),([(8,90),(42,28)],3),([(8,90),(-10,35)],3),([(104,22),(104,105),(270,105)],4),([(122,104),(122,282)],6),([(5,107),(122,107),(272,107)],6),([(107,42),(132,14),(134,-24)],3)]:path('campus_quad_path',pts,w)
for z in [40,57,74]:bench(103,z);lamp(-21,z)
for x in [-8,19,48,76,102]:lamp(x,18);tree(x,38,rng.uniform(4.2,5.4))
for x,z in [(-13,61),(4,64),(29,49),(52,57),(75,60),(94,74),(36,77),(62,81),(-31,36),(-31,53),(-33,70),(118,121),(118,143),(118,165),(118,187),(118,213),(118,239),(118,267)]:tree(x,z,rng.uniform(4.4,6))

cream='#dddcd1';glass='#5f8890';darkglass='#345765';frame='#455e63';trim='#b9c9c4'
for c in [glass,darkglass]:
    bs=g.mat(c).node_tree.nodes['Principled BSDF'];bs.inputs['Metallic'].default_value=.28;bs.inputs['Roughness'].default_value=.24
transparent='#98bac0';m=g.mat(transparent);m.surface_render_method='DITHERED';m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.32;m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.16
landmarks=[]
def facade(id,height,floors,wall=glass,open_lobby=False,doors=None):
    pts=poly(id);landmarks.append(dict(osmWay=id,footprint=pts,height=height,floors=floors))
    if open_lobby:
        g.polygon('ground_floor_lobby_'+id,pts,-.015,.03,'#e0ddd1')
        body=g.polygon('campus_upper_envelope_'+id,pts,5.1,height-5.1,wall,False)
    else:body=g.polygon('campus_building_'+id,pts,0,height,wall,True)
    body['campus_landmark']=id
    for k in range(1,floors+1):
        y=height*k/floors
        g.polygon('campus_floor_slab_'+id,pts,y-.38,.38,cream)
    g.polygon('campus_roof_'+id,pts,height,.24,'#b9bdb1')
    for ei,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
        ll=math.dist(a,b);n=max(1,round(ll/1.7));dx=(b[0]-a[0])/ll;dz=(b[1]-a[1])/ll
        for k in range(1,floors+1):
            y=height*k/floors
            seg('cream_horizontal_band',a,b,.48,.48,cream,y-.48)
            seg('window_transom',a,b,.14,.07,trim,y-1.35)
        for j in range(n+1):
            p=(a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n)
            if open_lobby and doors and abs(p[1]-doors[1])<2 and abs(p[0]-doors[0])<2.4:continue
            g.tube('facade_window_mullion',(p[0],0,p[1]),(p[0],height-.5,p[1]),.047,frame,n=4)
            if j%2==0:g.tube('top_storey_white_fin',(p[0],height-height/floors+.1,p[1]),(p[0],height-.46,p[1]),.13,cream,n=4)
        if open_lobby:
            # Leave a full clear doorway; glass is a wall everywhere else.
            segments=[(a,b)]
            if doors and abs((a[1]+b[1])/2-doors[1])<2 and min(a[0],b[0])<doors[0]<max(a[0],b[0]):
                left=min(a[0],b[0]);right=max(a[0],b[0]);zz=(a[1]+b[1])/2
                segments=[((left,zz),(doors[0]-2.5,zz)),((doors[0]+2.5,zz),(right,zz))]
            for aa,bb in segments:
                seg('first_floor_curtain_glass',aa,bb,.10,4.9,transparent,0,True)
        # Full visible parapets in every viewing mode.
        seg('roof_parapet',a,b,.24,.65,cream,height+.15)
    return pts

print('BUILD landscape ready',len(scene.objects),flush=True)
facade('1065747586',20.8,4,open_lobby=True,doors=(-5,10.8))
facade('1201084332',20.8,4,open_lobby=True,doors=(84,15.4))
# Weatherproof glazed connecting passage; first-floor visitors can move between entrance halls.
box('glass_link_upper',32,13,0,9,15.6,24,darkglass)
g.box('ground_floor_connecting_passage',32,.005,0,10,.01,24,'#dfdfd4')
for z in [-12,12]:seg('link_first_floor_glass',(27,z),(36,z),.08,5,transparent,0,True)
# The east wall of the early building and west wall of the expansion have a framed access opening.
# Doorway proxies use a gate in those wall segments, supplied below after colliders are assembled.
for x,z in [(-5,10.9),(84,15.5)]:
    box('entrance_canopy',x,3.5,z+2.2,8,.32,5.3,'#596e71')
    for dx in [-3.65,3.65]:g.tube('entrance_steel_post',(x+dx,0,z+4.5),(x+dx,3.5,z+4.5),.09,'#81918d',n=6)
    for dx in [-2.5,2.5]:box('doorway_frame',x+dx,1.6,z,.12,3.2,.20,frame)
    g.label('KENTECH',x,3.15,z+4.87,5,.46,color='#eff0df')
    box('entrance_recess_atrium',x,12.85,z+.16,10.5,15.2,.25,darkglass)
    for xx in [-5.25,-2.62,0,2.62,5.25]:box('atrium_vertical_frame',x+xx,12.85,z+.32,.08,15.2,.08,frame)
    for yy in [7,9.5,12,14.5,17,19.5]:box('atrium_horizontal_frame',x,yy,z+.32,10.5,.08,.08,frame)
g.label('KENTECH',-5,21.35,11.55,21,1.8,color='#315f75')
g.label('한국에너지공과대학교',59,1.1,30.8,17,.63,color='#355868')
box('campus_name_wall',59,.85,30.45,20,1.7,.5,'#dedbcc',True)
g.label('KOREA INSTITUTE OF ENERGY TECHNOLOGY',59,.45,30.74,18,.24,color='#667675')
solar(-14,-10,21.7,15,4);solar(44,-4,21.7,25,4)
for x,z,w,d in [(4,-4,7,6),(66,3,8,5),(82,-59,7,8)]:
    box('roof_stair_headhouse',x,22.4,z,w,3,d,cream)
    box('roof_headhouse_cap',x,24,z,w+.5,.22,d+.5,'#8c9d9c')
for x,z in [(15,-10),(20,-10),(87,-40),(88,-49)]:box('roof_mechanical_plant',x,21.65,z,2.8,1.5,1.8,'#a9b3b1')
for x in range(39,101,5):box('roof_terrace_planter',x,21.12,9,2.9,.45,1.4,'#738655')
path('courtyard_walk',[(35,-15),(49,-40),(72,-32),(73,-15)],3)
g.polygon('courtyard_lawn',[(40,-17),(53,-44),(73,-32),(73,-16)],.015,.03,'#7d935a')
for x,z in [(52,-22),(62,-27),(67,-19)]:tree(x,z,4.7)

# 1F circulation only: rear partitions close unverified teaching/research rooms.
for x,z,w in [(2,-7,40),(71,-3,66)]:
    box('lobby_back_partition',x,2.5,z,w,5,.22,'#e3e0d4',True)
    box('lobby_reception_counter',x-9,.53,z+2.5,4.4,1.06,1.1,'#b49b75',True)
    box('reception_worktop',x-9,1.1,z+2.5,4.5,.10,1.2,'#64716e')
    g.label('KENTECH',x+5,2.8,z+.14,6,.67,color='#315f75')
    for xx in range(int(x-w/2)+3,int(x+w/2)-2,6):
        box('lobby_ceiling_light',xx,4.97,z+7,1.6,.055,.32,'#fff2d5')
        box('floor_joint',xx,.026,z+7,.01,.01,12,'#bcc2b8')
    for zz in [z+3,z+6,z+9,z+12]:box('floor_joint',x,.026,zz,w,.01,.01,'#bcc2b8')
    g.lights.append(dict(position=[x,4.4,z+7],color='#fff3dd',intensity=32,distance=25))
    for xx in [x-17,x+18]:bench(xx,z+9)
# Remove only the specific glass collider at the connecting passage, retaining narrow jambs.
for s in list(g.solids):
    if s['name']!='first_floor_curtain_glass':continue
    p=s['footprint'];cx=sum(q[0] for q in p)/4;cz=sum(q[1] for q in p)/4
    if (26<cx<29 or 35<cx<38) and -5<cz<8:
        g.solids.remove(s)
        # A visible closed pane would contradict the opening: remove its corresponding mesh below.
        for o in list(scene.objects):
            if o.name.startswith('first_floor_curtain_glass') and o.type=='MESH':
                center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
                if abs(center.x-cx)<.02 and abs(-center.y-cz)<.02:bpy.data.objects.remove(o,do_unlink=True)

print('BUILD main lecture buildings ready',len(scene.objects),flush=True)
# Mapped research/data buildings; heights/fin spacing are estimated from public aerial imagery.
for id,h,n in [('1460776854',20,5),('1460776855',15,3),('1476045296',14,3),('1265544133',8,2)]:facade(id,h,n)
# Aerial-confirmed circular library envelope (construction in July 2025). Its finish is interpretive.
cx,cz=145,-94;ro,ri=44,30
for i in range(80):
    a=i*math.tau/80;b=(i+1)*math.tau/80
    p=[(cx+rr*math.cos(aa),cz+rr*math.sin(aa)) for rr,aa in [(ro,a),(ro,b),(ri,b),(ri,a)]]
    g.polygon('library_annular_envelope',p,0,12,'#aebebc',True)
    g.polygon('library_annular_roof',p,12,.5,cream)
    aa=(cx+ro*math.cos(a),cz+ro*math.sin(a));bb=(cx+ro*math.cos(b),cz+ro*math.sin(b))
    seg('library_upper_glazing',aa,bb,.17,2.5,glass,8.8)
    for y in [4,8,12]:seg('library_ring_band',aa,bb,.32,.4,cream,y-.4)
    g.tube('library_fin',(aa[0],0,aa[1]),(aa[0],12,aa[1]),.11,cream,n=4)
circle('library_court',cx,cz,ri-.8,.025,'#b6bda1')
landmarks.append(dict(name='library',source='2025 aerial circular outline',height=12.5,estimatedFinish=True))
path('campus_library_approach',[(111,16),(125,-22),(119,-47)],5)
# RC residence: two brick-faced bars and a lower common link; no residential interiors.
for id,h,n in [('1476045298',28,8),('1476045299',28,8),('1476045300',11,3)]:
    pts=poly(id);g.polygon('rc_residence_'+id,pts,0,h,'#ad7057',True);g.polygon('rc_roof_'+id,pts,h,.24,'#b6b5a9')
    landmarks.append(dict(osmWay=id,footprint=pts,height=h,floors=n))
    for a,b in zip(pts,pts[1:]+pts[:1]):
        ll=math.dist(a,b);count=max(1,int(ll/3.1))
        for floor in range(n):
            for j in range(count):
                t0=(j+.18)/count;t1=(j+.83)/count;aa=[a[k]+(b[k]-a[k])*t0 for k in [0,1]];bb=[a[k]+(b[k]-a[k])*t1 for k in [0,1]]
                seg('rc_window',aa,bb,.14,2.05,darkglass,floor*h/n+.55)
                seg('rc_window_sill',aa,bb,.22,.08,'#d9cbb7',floor*h/n+.53)
            seg('rc_floor_joint',a,b,.15,.10,'#cf9676',(floor+1)*h/n-.15)
    xs=[p[0] for p in pts];zs=[p[1] for p in pts]
    if max(xs)-min(xs)>60:solar(min(xs)+5,min(zs)+3,h+.9,34,2)
facade('1476045297',8.5,2,wall='#718d93');solar(145,218,9.3,18,8)
for z in [145,155,167,203,267]:path('rc_garden_path',[(127,z),(267,z)],3)
for x in [135,258,278]:
    for z in [132,154,178,202,224,247,270]:tree(x,z,rng.uniform(4,6))
for z in [150,176,204,235,266]:lamp(130,z)
for x in [159,177,195,216,234]:bench(x,201)

print('BUILD research and residence ready',len(scene.objects),flush=True)
# Sports grounds from mapped field/court boundaries, with a rounded six-lane track.
def capsule(r,straight=83):
    return [(-155+r*math.cos(a),-10+sign*straight/2+r*math.sin(a)) for sign,start in [(-1,math.pi),(1,0)] for a in [start+i*math.pi/48 for i in range(49)]]
g.polygon('athletics_track_red',capsule(57),.025,.025,'#ad584b')
g.polygon('athletics_infield',capsule(48.5),.054,.015,'#557c51')
for r in [49.5,50.7,51.9,53.1,54.3,55.5,56.7]:
    pts=capsule(r);line('track_lane_marking',pts+[pts[0]],.075,.088)
soc=poly('1201084333');g.polygon('football_pitch',soc,.078,.022,'#467653')
xs=[p[0] for p in soc];zs=[p[1] for p in soc];x0,x1=min(xs),max(xs);z0,z1=min(zs),max(zs);mx=(x0+x1)/2;mz=(z0+z1)/2
for j in range(10):box('pitch_mown_stripe',mx,.105,z0+(j+.5)*(z1-z0)/10,x1-x0,.007,(z1-z0)/10,'#537e57' if j%2 else '#49734e')
line('football_touchline',soc+[soc[0]],.13,.125);line('football_halfway',[(x0,mz),(x1,mz)],.13,.13)
pts=[(mx+9.15*math.cos(i*math.tau/64),mz+9.15*math.sin(i*math.tau/64)) for i in range(65)];line('football_center_circle',pts,.12,.13)
for zz,sg in [(z0,1),(z1,-1)]:
    line('football_penalty_box',[(mx-20,zz),(mx-20,zz+16.5*sg),(mx+20,zz+16.5*sg),(mx+20,zz)],.13,.13)
    for xx in [mx-3.66,mx+3.66]:g.tube('goal_post',(xx,.1,zz),(xx,2.54,zz),.065,'#e9e8df',n=6)
    g.tube('goal_crossbar',(mx-3.66,2.54,zz),(mx+3.66,2.54,zz),.065,'#e9e8df',n=6)
for id,c in [('1092517582','#55958b'),('1092517583','#bd8a6b'),('1092517584','#4f7960')]:
    pts=poly(id);g.polygon('sports_court_'+id,pts,.08,.03,c);line('court_boundary',pts+[pts[0]],.10,.14)
    x0,x1=min(p[0] for p in pts),max(p[0] for p in pts);z0,z1=min(p[1] for p in pts),max(p[1] for p in pts)
    line('court_centre',[(x0,(z0+z1)/2),(x1,(z0+z1)/2)],.10,.14)
    for x in [x0+1,x1-1]:
        for z in [z0+1,z1-1]:g.tube('sports_fence_post',(x,.1,z),(x,3.2,z),.05,'#717f75',n=5)
    for a,b in zip(pts,pts[1:]+pts[:1]):
        for y in [.8,1.6,2.4,3.2]:seg('sports_fence_wire',a,b,.02,.02,'#8c9b8b',y)
facade('1092517581',4,1,wall='#819396')
# Border groves are deliberately sparse young campus planting, not mature forest.
for x,z in [(-227,z) for z in range(-140,125,17)]+[(x,285) for x in range(-35,260,17)]+[(285,z) for z in range(-220,105,18)]+[(x,-263) for x in range(-38,267,18)]:
    if not any(inside((x,z),p) for p in footprints):tree(x+rng.uniform(-2,2),z,rng.uniform(4.2,6.5))

print('BUILD complete geometry',len(scene.objects),flush=True)
world=dict(title='나주 산책',subtitle='KENTECH 캠퍼스와 1층',source='© OpenStreetMap contributors · ODbL 1.0',bounds=[-250,315,-320,305],spawn=dict(x=-5,z=27,yaw=0),solids=g.solids,signs=g.signs,verticalNavigation=True,requireFloor=True,lights=g.lights,lighting=dict(exposure=1.1,ambient=1.8,sun=2.3),sceneLinks=[dict(label='빛가람 안내 지도',target='bitgaram')],places=[
 dict(id='entrance',name='행정강의동 정문',description='긴 유리 외벽과 흰 수평 띠가 있는 강의동입니다.',position=[-5,25],radius=12,arrival=[-5,25]),
 dict(id='lobby',name='행정강의동 1층',description='실내 동선과 가구 배치는 추정입니다.',position=[-5,2],radius=7,footprint=[[-17,-6],[23,-6],[23,10],[-17,10]],arrival=[-5,3],indoor=True),
 dict(id='east-lobby',name='강의동 동쪽 1층',description='상층과 연구실은 외관으로 표현했습니다.',position=[84,7],radius=6,arrival=[84,7],indoor=True),
 dict(id='quad',name='캠퍼스 앞마당',description='보행로를 따라 운동장과 기숙사 주변을 둘러보세요.',position=[42,59],radius=23,arrival=[27,55]),
 dict(id='sports',name='운동장과 체육 공간',description='트랙, 축구장과 테니스·농구 코트입니다.',position=[-155,-10],radius=70,arrival=[-103,18]),
 dict(id='rc',name='RC 교육생활관 앞',description='생활관과 식당·체육시설 외관입니다.',position=[126,205],radius=23,arrival=[126,205]),
 dict(id='research',name='연구동과 도서관 주변',description='항공사진과 지도 윤곽을 참고했습니다. 도서관 마감은 추정입니다.',position=[124,-21],radius=17,arrival=[124,-21])],arrivals={'entrance':dict(x=-5,z=27,yaw=0),'lobby':dict(x=-5,z=3,yaw=0),'sports':dict(x=-103,z=18,yaw=1.57),'rc':dict(x=126,z=205,yaw=-1.57),'research':dict(x=124,z=-21,yaw=0)},provenance=dict(origin=[126.803269,35.010582],osmDate='2026-09-20',landmarks=landmarks,limitations='Mapped footprints; photo-informed envelope. Heights, furniture, trees and 1F circulation estimated. Library finish inferred; no claim of surveyed interiors.'),validationRoutes=[[[ -5,27],[-5,3],[-5,27]],[[84,28],[84,7],[84,28]],[[ -5,27],[-5,22],[20,22],[27,55],[8,90],[122,107],[126,205]]])
(R/'public/bitgaram-kentech-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(S/'model-metrics.json').write_text(json.dumps(dict(landmarks=landmarks,objects=len(scene.objects),colliders=sum(s.get('collision',False) for s in g.solids),treeCount=sum(s['name']=='tree_trunk' for s in g.solids)),ensure_ascii=False,indent=2),encoding='utf8')
for o in scene.objects:
    if re.match(r'^(ground_floor|campus_ground|campus_road|campus_parking|campus_quad_path|rc_garden_path|courtyard_walk|courtyard_lawn|athletics_|football_pitch|pitch_mown|football_touch|football_half|football_center|football_penalty|track_lane|court_boundary|court_centre|sports_court|parking_bay|road_center)',o.name):o['no_shadow']=True
scene.world=bpy.data.worlds.new('Campus daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.63,.76,.86,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.5;sun.rotation_euler=(.48,-.5,-.6);sun.data.angle=.08
bpy.ops.object.camera_add(location=g.bp(-280,250,370));cam=bpy.context.object;cam.data.lens=38;cam.data.clip_end=2200;cam.rotation_euler=(Vector(g.bp(34,3,30))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=24;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.4
scene.render.resolution_x=1400;scene.render.resolution_y=950;scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(target))
# Export-only opaque batching reduces browser object/draw overhead; editable .blend remains separate.
from kentech_export import batch_and_export
batch_and_export(scene,R/'public/models/bitgaram-kentech.glb')
raw=(R/'public/models/bitgaram-kentech.glb').read_bytes();(R/'public/models/bitgaram-kentech.glb.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
for name,pos,aim,lens in [('campus-overview',(-280,250,370),(34,3,30),38),('main-building',(-64,36,118),(44,9,-4),35),('first-floor',(-5,1.7,5),(7,2,-5),22)]:
    cam.location=g.bp(*pos);cam.rotation_euler=(Vector(g.bp(*aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.render.filepath=str(O/(name+'-v52.png'));bpy.ops.render.render(write_still=True)
print('KENTECH COMPLETE',len(raw),'bytes',len(scene.objects),'export objects',flush=True)
