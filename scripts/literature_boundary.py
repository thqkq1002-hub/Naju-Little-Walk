"""Photo-informed museum boundary and previously blank exterior returns.

JNFC 149488–149493 show timber fences, an east gable and a small service wing.
Alignment follows the existing satellite garden; dimensions remain estimates.
"""
import bpy,math,random
from yeongsanpo_geometry import Geometry
from literature_courtyard import finish,slab

def discard(g,prefixes):
    for o in list(g.scene.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
    g.solids[:]=[s for s in g.solids if not any(s['name'].startswith(p) for p in prefixes)]

def face(g,x,z,angle=0):return Geometry(g.scene,g.point(x,z),g.angle+angle)

def fence(g,a,b,pickets=False):
    length=math.dist(a,b);n=max(1,math.ceil(length/1.85))
    proxy=g.segment('hall-wall_literature_boundary',a,b,.19,1.12,'#554334',collision=True)
    # The collision envelope is solid; visible geometry is the photographed
    # open three-rail fence, not an opaque wall.
    proxy.hide_render=True
    g.segment('literature_boundary_stone_footing',a,b,.26,.12,'#92978b',record=False)
    for y in (.32,.67,1.0):g.segment('literature_boundary_horizontal_rail',a,b,.065,.095,'#59432f',base=y,record=False)
    for i in range(n+1):
        x=a[0]+(b[0]-a[0])*i/n;z=a[1]+(b[1]-a[1])*i/n
        g.box('literature_boundary_timber_post',x,.59,z,.14,1.18,.14,'#463829',record=False)
        g.box('literature_boundary_post_cap',x,1.195,z,.18,.035,.18,'#75654d',record=False)
        g.box('literature_boundary_post_shoe',x,.11,z,.19,.22,.19,'#989c90',record=False)
    if pickets:
        for i in range(max(1,int(length/.18))):
            t=(i+.5)/max(1,int(length/.18));x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t
            g.box('literature_boundary_vertical_picket',x,.61,z,.058,1.08,.058,'#66503b',record=False)
    return dict(a=g.point(*a),b=g.point(*b),height=1.18,kind='picket' if pickets else 'three-rail')

def boundaries(g):
    discard(g,('garden_neighbor_boundary','garden_boundary_coping'))
    # Join the previously disconnected edges while retaining the existing
    # southwest approach. The 5 m opening straddles that path's boundary crossing.
    spans=[([-12.5,-8.65],[12.8,-8.65],False),([12.8,-8.65],[12.6,9.5],False),
           ([12.6,9.5],[6.2,13],False),([6.2,13],[6.2,35.97],False),
           ([-12.5,-8.65],[-12.5,11.7],False),([-12.5,11.7],[-13.1,15],False),
           ([-13.1,15],[-17,23],False),([-17,23],[-16,39],False),
           ([-16,39],[-9.2,38.073],True),([-4.2,37.391],[6.2,35.97],True)]
    records=[fence(g,*s) for s in spans]
    # Open gateposts and a small place marker; no unsupported roofed gateway.
    for x,z in [(-9.2,38.073),(-4.2,37.391)]:
        g.box('literature_open_gate_post',x,.79,z,.22,1.58,.22,'#4a3e30',True)
        g.box('literature_gate_post_cap',x,1.59,z,.27,.06,.27,'#796b54',record=False)
    sign=face(g,-10.6,38.51,-.1355)
    sign.box('literature_gate_nameplate',0,1.06,0,2.3,.66,.09,'#344b42',record=False)
    sign.label('타오르는 강 문학관',0,1.16,.056,2.10,.17,color='#efe7d2')
    sign.label('정원 입구',0,.93,.056,1.1,.105,color='#d4d6c4');g.signs+=sign.signs
    # Tidy stone curb and a grated drain at the open entrance, flush for walking.
    for i in range(13):
        x=-9.05+i*.37;z=38.05-(x+9.05)*.136
        g.box('literature_gate_drain_frame',x,.055,z,.35,.018,.26,'#6e766e',record=False)
        for j in range(4):g.box('literature_gate_drain_slot',x-.13+j*.085,.066,z,.038,.004,.20,'#374c47',record=False)
    return records

def brick_band(f,width,height,base=0):
    f.box('literature_weathered_brick_base',0,base+height/2,.032,width,height,.07,'#765749',record=False)
    verts=[];faces=[]
    def rect(x,y,w,h):
        o=len(verts);verts.extend([(x,y,.074),(x+w,y,.074),(x+w,y+h,.074),(x,y+h,.074)]);faces.append((o,o+1,o+2,o+3))
    for j in range(math.ceil(height/.11)):
        y=base+j*.11;rect(-width/2,y,width,.012)
        for i in range(math.ceil(width/.29)):
            x=-width/2+i*.29+(j%2)*.145
            if x<width/2-.012:rect(x,y,.012,min(.11,base+height-y))
    f.mesh('literature_original_brick_mortar',verts,faces,'#b5ada0')

def sealed_gable_roof(g):
    discard(g,('literature_main_tile_roof',))
    x0,x1=-8.55,10.55;z0,z1=-7.55,5.95;mid=-.8;y=4.80;rise=2.40
    for edge in (z0,z1):
        v=[(x0,y,edge),(x1,y,edge),(x1,y+rise,mid),(x0,y+rise,mid)]
        g.mesh('literature_main_gable_roof',v+[(x,yy-.11,z) for x,yy,z in v],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'#53616b','05_Cutaway_Roof')
        for i in range(65):
            x=x0+i*(x1-x0)/64;g.tube('literature_main_gable_tile_rib',(x,y+.045,edge),(x,y+rise+.055,mid),.046,'#53616b',n=6)
        for i in range(1,14):
            t=i/14;g.tube('literature_main_gable_tile_course',(x0,y+rise*t+.04,edge+(mid-edge)*t),(x1,y+rise*t+.04,edge+(mid-edge)*t),.022,'#6e7880',n=5)
    for i in range(61):
        x=x0+i*(x1-x0)/61;g.tube('literature_main_ridge_cap',(x,y+rise+.09,mid),(x+.30,y+rise+.09,mid),.125,'#4b5862',n=10)
    # Solid wall behind each triangular gable and between both roof levels.
    for x in (-8.33,10.33):
        g.mesh('literature_sealed_upper_gable',[(x,y-.07,z0+.10),(x,y-.07,z1-.10),(x,y+rise-.08,mid),(x-.08,y-.07,z0+.10),(x-.08,y-.07,z1-.10),(x-.08,y+rise-.08,mid)],[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],'#514a3b')
        for i in range(59):
            z=z0+.2+i*(z1-z0-.4)/58;h=rise*(1-abs(z-mid)/((z1-z0)/2))-.13
            if h>.08:g.box('literature_upper_gable_vertical_batten',x+.045 if x>0 else x-.13,y+h/2,z,.055,h,.055,'#766247',record=False)
        for yy in (4.76,4.93):g.segment('literature_gable_horizontal_timber',[x,z0+.05],[x,z1-.05],.17,.095,'#766247',base=yy,record=False)
    for x in (-8.30,10.20):
        g.box('literature_closed_side_clerestory',x,4.10,-.8,.18,1.44,13.25,'#514a3b',record=False)
        for z in (-6.4,-3.4,-.4,2.6,5.6):g.box('literature_upper_side_timber_post',x+(.12 if x>0 else -.12),4.1,z,.11,1.45,.12,'#736149',record=False)
        for y in (3.45,4.73):g.box('literature_upper_side_timber_band',x+(.12 if x>0 else -.12),y,-.8,.11,.11,13.25,'#736149',record=False)
    for z in (-6.48,5.78):
        g.box('literature_clerestory_closed_wall',1,4.10,z,18.35,1.44,.13,'#9e9b88' if z<0 else '#605c4b',record=False)
        for x in (-6,-2,2,6):
            g.box('literature_upper_shadow_slot',x,4.38,z+(-.081 if z<0 else .081),2.9,.48,.04,'#343d36',record=False)
        if z>0:
            for x in (-8,-4.4,-.8,2.8,6.4,10):g.box('literature_upper_front_post',x,4.1,z+.12,.10,1.45,.12,'#756249',record=False)
            for y in (3.45,4.73):g.box('literature_upper_front_band',1,y,z+.12,18.35,.10,.12,'#756249',record=False)
    for x in (-8.4,10.3):
        for edge in (z0,z1):
            g.tube('literature_gable_bargeboard',(x,y,edge),(x,y+rise,mid),.092,'#777466',n=4)

def compressor(f,x,z):
    f.box('literature_service_compressor',x,.92,z,.94,1.82,.43,'#d5d8cb',record=False)
    for y in (.49,1.34):
        f.tube('literature_compressor_fan_rim',(x,y,z+.22),(x,y,z+.255),.34,'#838b81',n=28)
        f.tube('literature_compressor_fan_center',(x,y,z+.26),(x,y,z+.27),.10,'#d9dacc',n=18)
        for i in range(24):
            a=i*math.tau/24;f.tube('literature_compressor_fan_guard',(x+.11*math.cos(a),y+.11*math.sin(a),z+.275),(x+.32*math.cos(a+.19),y+.32*math.sin(a+.19),z+.275),.007,'#c3c7bd',n=4)
    for y in (.05,1.78):f.box('literature_compressor_edge',x,y,z+.235,.9,.028,.022,'#aab2a6',record=False)
    f.tube('literature_service_hose',(x+.5,.12,z),(x+.69,.25,z-.4),.065,'#bfc5b6',n=8)

def exterior_returns(g):
    sealed_gable_roof(g)
    right=face(g,9.14,0,-math.pi/2)
    # The exposed veranda return in 149491 has deep dark joinery and paper/glass.
    brick_band(right,12.9,.40)
    right.box('literature_side_window_shadow',-3.2,1.70,.042,5.70,2.40,.09,'#34392f',record=False)
    right.window('literature_side_veranda_window',-3.2,1.70,.12,5.70,2.40,lattice=True)
    for x in (-6.12,-3.2,-.28):right.box('literature_side_window_post',x,1.66,.21,.14,2.6,.17,'#493c2a',record=False)
    for y in (.48,2.12,2.9):right.box('literature_side_window_band',-3.2,y,.21,5.98,.12,.17,'#493c2a',record=False)
    for i in range(37):right.box('literature_side_external_window_grille',-5.95+i*.153,1.7,.24,.030,2.30,.034,'#493c2a',record=False)
    for y in (.9,1.55,2.15):right.box('literature_side_external_window_grille',-3.2,y,.24,5.56,.030,.034,'#493c2a',record=False)
    for x in (2.1,4.8):
        right.box('literature_side_small_recess',x,1.9,.12,1.3,.88,.12,'#242f2b',record=False)
        right.window('literature_side_small_window',x,1.9,.20,1.3,.88)
    # The small white service projection and pitched roof are shown in 149491.
    g.box('photo-building_literature_service_annex',10.27,1.52,-2.8,2.55,3.04,2.8,'#e0dfd2',True)
    service=face(g,11.60,-2.8,-math.pi/2)
    service.box('literature_annex_small_black_window',0,1.9,.025,1.08,.77,.06,'#26312c',record=False)
    for dx in (-.57,0,.57):service.box('literature_annex_window_frame',dx,1.9,.07,.045,.86,.08,'#504a3c',record=False)
    for yy in (1.48,2.32):service.box('literature_annex_window_frame',0,yy,.07,1.18,.045,.08,'#504a3c',record=False)
    compressor(right,4.9,.45)
    # Side canopy has a closed underside and structural timber, eliminating the
    # unsupported roof silhouette shown in the user's side screenshot.
    for edge in (-4.48,-1.12):
        g.mesh('literature_service_gabled_roof',[(8.7,3.02,edge),(12.1,3.02,edge),(12.1,4.08,-2.8),(8.7,4.08,-2.8)],[(0,1,2,3)],'#52606a')
        for i in range(14):
            x=8.7+i*3.4/13;g.tube('literature_annex_roof_tile',(x,3.05,edge),(x,4.12,-2.8),.045,'#606d76',n=6)
    g.mesh('literature_annex_closed_gable',[(11.63,3.0,-4.46),(11.63,3.0,-1.14),(11.63,4.06,-2.8)],[(0,1,2)],'#63523c')
    g.box('literature_side_soffit',10.0,2.91,1.0,1.8,.14,14.2,'#5c4d38',record=False)
    for z in (-5.9,-.6,6.3):
        g.box('literature_side_eave_column',10.67,1.42,z,.17,2.84,.17,'#51412e',True)
        g.box('literature_side_column_stone',10.67,.12,z,.34,.24,.34,'#b1b3a4',record=False)
    for z in [i*.40-5.8 for i in range(32)]:g.box('literature_side_exposed_rafter',10.01,2.77,z,1.87,.12,.074,'#746047',record=False)
    g.box('literature_side_gutter',10.94,2.94,1.0,.13,.14,14.45,'#484e44',record=False)
    g.tube('literature_side_downpipe',(10.93,.14,6.56),(10.93,2.94,6.56),.056,'#484e44',n=10)
    # Left wing: brick plinth, barred window, low deck and wall-mounted AC.
    left=face(g,-8.86,7.5,math.pi/2);brick_band(left,6.0,.86)
    left.box('literature_wing_side_shadow',0,1.95,.10,1.50,1.85,.04,'#36483f',record=False)
    left.window('literature_wing_side_window',0,1.95,.16,1.50,1.85,lattice=True)
    for i in range(10):left.box('literature_wing_window_security_bar',-.67+i*.15,1.95,.24,.028,1.81,.04,'#4b493c',record=False)
    for y in (.42,.54):left.box('literature_wing_ac_grille',-1.95,y,.32,.65,.44,.34,'#d3d5c8',record=False)
    for i in range(8):left.box('literature_wing_ac_slot',-2.23+i*.08,.5,.502,.025,.33,.015,'#718279',record=False)
    for z in (6.55,6.76,6.97,7.18,7.39,7.60,7.81,8.02):g.box('literature_wing_low_deck_board',-9.90,.42,z,1.80,.075,.19,'#6a5038',record=False)
    g.collider('exhibit-case_literature_wing_deck',[[-10.8,6.455],[-9.0,6.455],[-9.0,8.115],[-10.8,8.115]],0,.46)
    for x in (-10.65,-9.16):
        for z in (6.55,7.99):g.box('literature_wing_deck_leg',x,.20,z,.10,.40,.10,'#493e30',True)
    # 149489's service cabinet and conduit beside the rear windows.
    rear=face(g,0,-6.70,math.pi)
    for center in (7,3,-2,-6):
        for i in range(15):rear.box('literature_rear_external_window_grille',center-1.06+i*.151,1.8,.10,.033,1.78,.04,'#3e3b2e',record=False)
        for y in (1.18,1.7,2.32):rear.box('literature_rear_external_window_grille',center,y,.10,2.24,.034,.04,'#3e3b2e',record=False)
    rear.box('literature_rear_service_door',-.8,1.15,.03,.85,2.3,.06,'#78583f',record=False)
    rear.box('literature_rear_door_glazing',-.8,1.56,.076,.39,.60,.03,'#4b5d53',record=False)
    rear.box('literature_rear_service_cabinet',3.0,1.32,.14,.77,1.43,.24,'#b5bcb0',record=False)
    rear.box('literature_cabinet_inset',3.0,1.59,.275,.41,.49,.05,'#6b7a70',record=False)
    for x in (2.75,3.25):rear.tube('literature_cabinet_conduit',(x,.24,.06),(x,.69,.06),.022,'#4b5a4d',n=6)
    g.signs+=right.signs+left.signs+rear.signs
    # Low stone retaining courses step with the garden, rather than a single
    # unbroken cream plane around the house.
    rng=random.Random(8842)
    for i in range(24):
        x=1.8+i*.43;z=9.8+.30*math.sin(i*.4)
        g.rock('literature_side_garden_rock_edge',x,.14,z,.46,.29,.33,rng.choice(['#6e7b70','#8c9588','#a4a89a']),rng)
    # Ground path for the side inspection stays within the fence and outside columns.
    for z in [7.8-i*.7 for i in range(8)]:slab(g,10.05,z,.72,.46,.05,rng)

def add_boundary_detail(g):
    records=boundaries(g);exterior_returns(g)
    finish(g,'#e0dfd2','plaster');finish(g,'#59432f','wood');finish(g,'#92978b','boundary-stone')
    return dict(revision='literature-boundary-1',segments=records,entrance=[g.point(-9.2,38.073),g.point(-4.2,37.391)],
        sideRoute=[g.point(*p) for p in [(0,10),(7,10.7),(10.05,8),(10.05,3)]],
        sources=['JNFC 149487','149488','149489','149490','149491','149492','149493'],
        limitations='Fence type and exterior details follow photos; boundary alignment, opening width, service projection and joinery dimensions are estimates. No surveyed property line or roofed entrance gate is asserted.')
