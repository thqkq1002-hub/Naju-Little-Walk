"""First-floor experience and campus detail helpers, executed by the school builder.
Room layouts are illustrative. No claim about the real classroom plan is made.
"""
ENTRY_U=27.0
ENTRY_HALF=1.75
ROOM_GROUP='05_Illustrative_Interior'

def overlaps_school_entry(edge,distance,width,length):
    return edge==22 and abs(distance-(length-ENTRY_U)) < ENTRY_HALF+width/2+.12

def build_school_first_floor(footprint):
    global frame_origin, frame_u, frame_v, frame_angle
    frame_origin=footprint[0]
    end=footprint[22]
    length=math.dist(frame_origin,end)
    frame_u=[(end[0]-frame_origin[0])/length,(end[1]-frame_origin[1])/length]
    frame_v=[frame_u[1],-frame_u[0]]
    frame_angle=math.atan2(-frame_u[1],frame_u[0])
    polygon('walk-floor_school_inside',footprint,.20,'#d9d4c5',group=ROOM_GROUP)
    polygon('school_first_floor_ceiling',footprint,.15,'#ede9dc',base=3.63,group=ROOM_GROUP)

    # Each window has a real hole through the wall. The low sill still blocks walking.
    for i,(a,b) in enumerate(zip(footprint,footprint[1:]+footprint[:1])):
        length=math.dist(a,b)
        if length<.01:continue
        direction=[(b[0]-a[0])/length,(b[1]-a[1])/length]
        def edge_span(name,start,end,base,height,collision=True):
            if end-start<.01 or height<.01:return
            pa=[a[0]+direction[0]*start,a[1]+direction[1]*start]
            pb=[a[0]+direction[0]*end,a[1]+direction[1]*end]
            segment(f'school-wall_{i}_{name}',pa,pb,.32,height,'#e5dfcd',collision,base,ROOM_GROUP)
        openings=[]
        if length>=3.5:
            bays=max(1,int(length/4.1))
            width=min(2.75,length/bays-.8)
            for j in range(bays):
                center=(j+.5)*length/bays
                if not overlaps_school_entry(i,center,width,length):
                    openings.append((center-width/2,center+width/2,1.05,2.95,'window_'+str(j)))
        if i==22:
            center=length-ENTRY_U
            openings.append((center-ENTRY_HALF,center+ENTRY_HALF,.20,3.04,'entrance'))
        previous=0
        for start,end,low,high,name in sorted(openings):
            edge_span(name+'_pier',previous,start,.20,3.43)
            edge_span(name+'_sill',start,end,.20,low-.20)
            edge_span(name+'_lintel',start,end,high,3.63-high,False)
            previous=end
        edge_span('end',previous,length,.20,3.43)

    # Upper window panes are translucent too; the solid second-floor mass stays closed.
    glass=mat('#486672')
    glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.24
    glass.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.2
    glass.diffuse_color=(*glass.diffuse_color[:3],.24)
    if hasattr(glass,'surface_render_method'):glass.surface_render_method='DITHERED'

    # Entrance frame and opened leaves leave a clear 3.1m passage.
    for u in (ENTRY_U-ENTRY_HALF-.03,ENTRY_U+ENTRY_HALF+.03):
        local_box('entrance_jamb',u,1.62,0,.12,2.84,.30,'#345e54',True)
    local_box('entrance_header',ENTRY_U,3.13,0,3.8,.24,.36,'#345e54')
    for u in (ENTRY_U-ENTRY_HALF+.16,ENTRY_U+ENTRY_HALF-.16):
        local_box('open_door_leaf',u,1.53,-.72,.10,2.6,1.45,'#537a6e',True)
        local_box('open_door_glass',u,1.80,-.74,.12,1.65,1.12,'#486672')
        local_box('door_handle',u,1.25,-1.25,.17,.35,.045,'#c7ccbc')
    local_box('walk-floor_entrance_mat',ENTRY_U,.22,.70,3.2,.025,1.0,'#65816c')
    local_box('entrance_name_board',ENTRY_U,3.35,-.29,3.8,.30,.10,'#28594b')
    local_label('다시초등학교',ENTRY_U,3.35,-.36,3.4,.22)
    local_box('entry_wayfinding',ENTRY_U+3.2,1.25,-4.8,2.6,.95,.15,'#28594b',True)
    local_label('학교 안으로 ↑',ENTRY_U+3.2,1.37,-4.90,2.3,.28)
    local_label('복도 · 교실 · 도서실',ENTRY_U+3.2,1.04,-4.90,2.3,.16)
    for du in (-1.05,1.05):local_box('wayfinding_leg',ENTRY_U+3.2+du,.45,-4.8,.07,.90,.12,'#627163')

    # The furnished visit occupies the front western wing's first floor.
    for u in (1.4,31.8):local_box('interior_end_wall',u,1.90,5.8,.20,3.40,11.5,'#e9e2ce',True)
    local_box('room_divider',15.7,1.90,7.25,.18,3.40,7.7,'#e9e2ce',True)
    local_box('classroom_back_wall',16.6,1.9,11.05,30.6,3.4,.18,'#e9e2ce',True)
    for name,left,right,door in [('classroom',1.4,15.7,3.1),('library',15.7,31.8,25.0)]:
        for lo,hi in ((left,door-.78),(door+.78,right)):
            local_box(name+'_partition',(lo+hi)/2,1.25,3.55,hi-lo,2.1,.16,'#d2dfd4',True)
            local_box(name+'_partition_glass',(lo+hi)/2,2.76,3.55,hi-lo,1.05,.055,'#486672')
        local_box(name+'_door_header',door,3.02,3.55,1.60,.3,.24,'#628473')
        for u in (door-.80,door+.80):local_box(name+'_door_jamb',u,1.52,3.55,.07,2.64,.25,'#628473',True)
        local_box(name+'_door_open',door+.85,1.52,4.20,.09,2.64,1.2,'#b29b73',True)
        local_box(name+'_room_sign',door,3.30,3.41,2.4,.32,.08,'#3f6759')
        local_label('체험 교실' if name=='classroom' else '작은 도서실',door,3.30,3.35,2.2,.23)
    local_box('corridor_wall_dado',16.6,.60,11.0,30.4,.8,.04,'#a6b9a1')
    local_box('corridor_floor_strip',16.5,.205,2.35,29.8,.009,.11,'#b29b6d')
    for u in range(3,31,2):
        local_box('corridor_floor_joint',u,.204,1.86,.015,.008,3.1,'#bfc1b1')

    # A twelve-seat classroom with board, clock, teacher desk and study materials.
    local_box('classroom_board_frame',9,2.03,10.84,7.1,1.70,.15,'#ae956f')
    local_box('classroom_chalkboard',9,2.03,10.73,6.85,1.48,.07,'#315e50')
    local_label('함께 배우는 교실',9,2.25,10.66,5.2,.38)
    local_label('다시초등학교 · 체험 공간',9,1.69,10.66,4.4,.24)
    local_box('chalk_tray',9,1.2,10.57,7.0,.09,.22,'#b4b7a4')
    for u in (7.2,8.0,10.3):local_box('chalk',u,1.26,10.55,.16,.03,.05,'#e8e5d6')
    for row,v in enumerate((5.3,7.25,9.2)):
        for col,u in enumerate((5.4,7.8,10.2,12.6)):
            desk(f'student_desk_{row}_{col}',u,v)
            chair(f'student_chair_{row}_{col}',u,v-.60)
            local_box('exercise_book',u-.17,.944,v,.28,.025,.36,('#daba6a','#6b9e96','#b98174')[(row+col)%3])
            local_box('book_page',u-.17,.96,v,.25,.010,.32,'#f2efdd')
            local_box('pencil',u+.17,.947,v,.018,.018,.25,'#bf9150')
    desk('teacher_desk',3.2,9.9,width=1.45,depth=.68)
    local_box('teacher_book_stack',3.1,.98,9.8,.42,.14,.31,'#a45e51')
    local_box('classroom_clock_board',14.4,2.83,10.75,.72,.65,.09,'#f3eedb')
    local_label('10 : 10',14.4,2.83,10.68,.62,.14,color='#456656')

    # Reading room: low shelving, visible book spines and two reading tables.
    for u in (18.0,21.1,24.2,27.3,30.0):
        bookshelf(u,10.5)
    for i,u in enumerate((19.4,28.1)):
        desk('reading_table_'+str(i),u,6.8,width=2.15,depth=1.12)
        for du in (-.65,.65):
            chair('reading_chair',u+du,5.85)
            chair('reading_chair',u+du,7.72,reverse=True)
        local_box('open_reading_book',u,.95,6.8,.61,.04,.43,'#e7d9b3')
        local_box('reading_book_spine',u,.98,6.8,.02,.014,.43,'#ab775d')
    local_box('library_carpet',24.2,.22,8.80,7.5,.025,2.0,'#bdc89b')
    local_label('책과 함께, 한 걸음',24,2.86,10.86,7.0,.39,color='#49685b')

    # Corridor furniture stays outside the clear circulation strip.
    for i in range(10):
        u=6+i*.85
        local_box('shoe_locker',u,.77,.49,.78,1.12,.55,'#bca47c',True)
        for y in (.52,1.02):
            local_box('locker_door',u,y,.80,.70,.44,.035,('#d7c7a0','#aebf9a')[i%2])
            local_box('locker_handle',u+.22,y,.83,.05,.11,.04,'#738376')
    local_box('welcome_notice_board',21.3,1.94,.19,3.4,1.55,.15,'#8f7659')
    local_box('notice_cork',21.3,1.94,.30,3.16,1.32,.04,'#c6b185')
    # This board faces inward, toward the corridor.
    local_label('어서 오세요',21.3,2.22,.35,2.7,.30,reverse=True,color='#364f43')
    local_label('1층 복도 · 교실 · 도서실',21.3,1.78,.35,2.8,.17,reverse=True,color='#364f43')

    lights=[]
    for u,v in ((7,2),(24,2),(8.7,7),(24,7)):
        local_box('ceiling_light_trim',u,3.52,v,1.65,.08,.45,'#bbc3b6')
        fixture=local_box('ceiling_light_diffuser',u,3.46,v,1.48,.035,.33,'#fff4d9')
        material=mat('#fff4d9')
        material.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(1,.88,.65,1)
        material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.25
        x,z=local_point(u,v)
        lights.append(dict(position=[x,3.25,z],color='#fff0ce',intensity=27,distance=14))
        bpy.ops.object.light_add(type='AREA',location=bp(x,3.40,z))
        light=bpy.context.object; light.name='Interior_ceiling_light'
        light.data.energy=120; light.data.shape='RECTANGLE'; light.data.size=2.6; light.data.size_y=1.3

    room_places=[room_place('classroom','체험 교실',1.6,15.5,3.72,10.95,'책상과 칠판을 둘러보세요. 실제 교실 배치와는 다른 체험 공간입니다.'),room_place('library','작은 도서실',15.9,31.6,3.72,10.95,'책장과 독서 테이블을 만든 가상의 도서실입니다.'),room_place('corridor','1층 복도',1.6,31.6,.10,3.70,'열린 문으로 교실과 도서실을 둘러볼 수 있어요.')]
    sx,sz=local_point(ENTRY_U,-10)
    return dict(source='Illustrative interior; not a surveyed school plan',spawn=dict(x=sx,z=sz,yaw=frame_angle),entry=local_point(ENTRY_U,0),places=room_places,lights=lights,walkRoute=[local_point(ENTRY_U,-10),local_point(ENTRY_U,2),local_point(25,2),local_point(25,6),local_point(25,2),local_point(3.1,2),local_point(3.1,5.4)],wallProbe=[local_point(8,2),local_point(8,4.5)],signOutward=[-frame_v[0],-frame_v[1]],frame=dict(origin=frame_origin,u=frame_u,v=frame_v))

def local_point(u,v):
    return [frame_origin[0]+u*frame_u[0]+v*frame_v[0],frame_origin[1]+u*frame_u[1]+v*frame_v[1]]

def local_box(name,u,y,v,w,h,d,color,collision=False):
    x,z=local_point(u,v)
    return box(name,x,y,z,w,h,d,color,collision,frame_angle,ROOM_GROUP)

def local_label(text,u,y,v,width,height,reverse=False,color='#fff4d9'):
    x,z=local_point(u,v)
    return label(text,x,y,z,width,frame_angle+(math.pi if reverse else 0),color,height)

def desk(name,u,v,width=.9,depth=.55):
    local_box(name+'_top',u,.90,v,width,.075,depth,'#c4a879',True)
    for du in (-width*.38,width*.38):
        for dv in (-depth*.34,depth*.34):
            local_box(name+'_leg',u+du,.52,v+dv,.035,.72,.035,'#65766e')
    local_box(name+'_shelf',u,.70,v,width*.75,.035,depth*.76,'#778379')

def chair(name,u,v,reverse=False):
    local_box(name+'_seat',u,.57,v,.44,.06,.43,'#afc099',True)
    back=v+(.20 if reverse else -.20)
    local_box(name+'_back',u,.82,back,.45,.36,.045,'#a8b58d')
    for du in (-.17,.17):
        for dv in (-.16,.16):local_box(name+'_leg',u+du,.39,v+dv,.027,.34,.027,'#65766e')

def bookshelf(u,v):
    local_box('library_shelf_back',u,1.16,v,2.50,1.90,.12,'#bd9c70',True)
    for du in (-1.25,1.25):local_box('library_shelf_side',u+du,1.16,v-.22,.10,1.90,.56,'#bd9c70')
    for y in (.28,.84,1.40,1.96):local_box('library_shelf_board',u,y,v-.20,2.5,.065,.56,'#c7b186')
    colors=('#7b9c81','#a56b59','#6d8e9d','#c1a35c','#a998ad','#e0c294')
    for row in range(3):
        for j in range(11):
            bu=u-1.07+j*.20
            height=.35+(j%3)*.035
            local_box('book_spine',bu,.33+row*.56+height/2,v-.26,.145,height,.33,colors[(j+row)%len(colors)])
            local_box('book_spine_label',bu,.43+row*.56,v-.44,.095,.045,.01,'#eee4c6')

def room_place(id,name,u0,u1,v0,v1,description):
    return dict(id=id,name=name,description=description,position=local_point((u0+u1)/2,(v0+v1)/2),radius=20,indoor=True,footprint=[local_point(u0,v0),local_point(u1,v0),local_point(u1,v1),local_point(u0,v1)])

def detail_school_campus():
    # Individual tree positions are approximate within the aerially observed grove.
    for row,z in enumerate((23,31,41)):
        for col,x in enumerate((-36,-25,-14,-3,8,16)):
            if col==5 and row==0:continue
            tx=x+(row%2)*1.3; tz=z+(col%2)*1.6
            tree(tx,tz,1.75+(row+col)%3*.15,100+row*6+col)
            box(f'grove_trunk_base_{row}_{col}',tx,.28,tz,.66,.54,.66,'#7c6450',True)
    # Parking bays are visible in the aerial photo; exact markings/cars are illustrative.
    for i in range(9):
        x=-73+i*3.15
        segment('parking_bay_line',[x,-8],[x-1,0],.08,.006,'#e4e2d4',base=.092)
    segment('parking_end_line',[-74,0],[-46,3],.08,.006,'#e4e2d4',base=.094)
    for i,x in enumerate((-68,-57,-48)):
        box('parked_car_body',x,.65,-4.1,1.85,.70,4.3,('#d6dcd6','#70848a','#b8bab0')[i],True)
        box('parked_car_cabin',x,1.15,-4.3,1.60,.56,2.25,'#657a7d')
        box('parked_car_roof',x,1.46,-4.3,1.58,.08,1.70,('#d6dcd6','#70848a','#b8bab0')[i])
        for dx in (-.88,.88):
            for dz in (-1.25,1.25):box('car_tire',x+dx,.40,-4.1+dz,.18,.56,.59,'#45534e')
        for dx in (-.61,.61):box('car_headlight',x+dx,.71,-1.92,.30,.16,.055,'#ece2bc')
    # Green ball-stop fence, leaving the field-facing west edge open.
    for side,(a,b) in enumerate([([44,-8.3],[68,-8.3]),([68,-8.3],[68,12.3]),([68,12.3],[44,12.3])]):
        segment(f'court_fence_base_{side}',a,b,.12,.22,'#56794e',True)
        for y in (.55,1.1,1.65,2.2,2.75,3.3,3.85):segment('court_wire_horizontal',a,b,.018,.018,'#698962',base=y)
        length=math.dist(a,b)
        for j in range(int(length/.65)+1):
            t=j/max(1,int(length/.65))
            x,z=a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t
            cylinder('court_wire_vertical',x,2.0,z,.014,3.9,'#698962',6)
        for j in range(5):
            t=j/4
            cylinder('court_fence_post',a[0]+(b[0]-a[0])*t,2.10,a[1]+(b[1]-a[1])*t,.055,4.2,'#3f6e47',8)
    # Basketball equipment is a simplified interpretation of the court photo.
    for i,x in enumerate((45.5,66.5)):
        inward=1 if i==0 else -1
        cylinder('basketball_post',x,1.85,2,.11,3.7,'#4d7753',12)
        box('basketball_backboard',x+inward*.38,3.42,2,.10,1.05,1.8,'#eeead9')
        for z in (1.7,2.3):box('backboard_target',x+inward*.45,3.39,z,.018,.39,.035,'#697968')
        for y in (3.2,3.58):box('backboard_target',x+inward*.45,y,2,.018,.025,.63,'#697968')
        center=x+inward*.77
        for j in range(16):
            ang=j*math.tau/16; next_ang=(j+1)*math.tau/16
            segment('basketball_ring',[center+.23*math.cos(ang),2+.23*math.sin(ang)],[center+.23*math.cos(next_ang),2+.23*math.sin(next_ang)],.035,.035,'#b36d40',base=3.04)
        for j in range(8):
            ang=j*math.tau/8
            cylinder('basketball_net',center+.20*math.cos(ang),2.87,2+.20*math.sin(ang),.008,.34,'#e2e0c9',6)
    # Court center circle and lane markings.
    for j in range(40):
        a=j*math.tau/40; b=(j+1)*math.tau/40
        segment('court_center_circle',[56+2.15*math.cos(a),2+2.15*math.sin(a)],[56+2.15*math.cos(b),2+2.15*math.sin(b)],.075,.006,'#eee3c8',base=.105)
    for x,direction in ((45,1),(67,-1)):
        for z in (-.7,4.7):segment('court_key_line',[x,z],[x+direction*4.4,z],.075,.006,'#eee3c8',base=.105)
        segment('court_free_throw',[x+direction*4.4,-.7],[x+direction*4.4,4.7],.075,.006,'#eee3c8',base=.105)
    # Flagpoles and low railings visible in the ground-level references.
    for i in range(3):
        x,z=-11+i*1.5,-2.5
        cylinder('flagpole',x,3.2+(i%2)*.4,z,.045,6.4+(i%2)*.8,'#bbc4b8',12)
        box('flagpole_base',x,.18,z,.55,.25,.55,'#c3c6b5',True)
    for i in range(6):
        x=-32+i*1.25
        for dx in (-.38,.38):cylinder('grove_tree_guard',x+dx,.38,18,.025,.70,'#cbd2bd',8)
        segment('grove_tree_guard_top',[x-.38,18],[x+.38,18],.05,.05,'#cbd2bd',base=.74)
    # Rainwater pipes and small foundation plinths refine the visible facades.
    for i in (0,3,11,12,19,20,22):
        a,b=main[i],main[(i+1)%len(main)]
        length=math.dist(a,b); nx,nz=(b[1]-a[1])/length,-(b[0]-a[0])/length
        for t in (.07,.93):
            x=a[0]+(b[0]-a[0])*t+nx*.25; z=a[1]+(b[1]-a[1])*t+nz*.25
            cylinder(f'drainpipe_{i}_{t}',x,4.15,z,.065,8.2,'#b1a08a',10)
        # Do not run a plinth across the open entrance.
        if i!=22:segment(f'foundation_plinth_{i}',a,b,.45,.22,'#b5ab94',base=.07)
    for i in range(9):
        u=3.0+i*2.4
        local_box('front_paving_joint',u,.185,-2.1,.025,.008,3.9,'#a5997b')
    for u in (3,15,30):
        x,z=local_point(u,-6.0)
        box('flower_planter',x,.35,z,1.4,.65,.7,'#a59677',True,frame_angle)
        box('planter_soil',x,.69,z,1.22,.035,.53,'#5e5a43',rotation=frame_angle)
        for j in range(5):
            px,pz=local_point(u-.5+j*.25,-6)
            cylinder('flower_stem',px,.90,pz,.016,.38,'#66824f',6)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.115,location=bp(px,1.10,pz))
            flower=bpy.context.object; flower.name='planter_flower'
            for collection in list(flower.users_collection):collection.objects.unlink(flower)
            groups['03_Estimated_Details'].objects.link(flower)
            flower.data.materials.append(mat(('#d5ba68','#c78883')[j%2]))
