"""Photo-informed museum rooms, independently detailed behind outdoor portals."""
import math, random
from yeongsanpo_geometry import Geometry, world_data, place

def shell(g,w,d,h,color,door_x=0):
    g.box('ground_floor_interior',0,-.06,0,w,.12,d,'#c4bca4')
    for x in (-w/2,w/2):g.box('museum-wall_side',x,h/2,0,.20,h,d,color,True)
    g.box('museum-wall_back',0,h/2,-d/2,w,h,.20,color,True)
    for a,b in [(-w/2,door_x-1),(door_x+1,w/2)]:g.box('museum-wall_front',(a+b)/2,h/2,d/2,b-a,h,.20,color,True)
    g.box('museum-wall_door_header',door_x,h-.35,d/2,2,.7,.2,color)
    g.box('cutaway_ceiling',0,h+.05,0,w,.12,d,'#343330',group='05_Cutaway_Roof')

def panel(g,title,x,z,width=3,height=2.65,color='#a58b74',rotation=0):
    g.box('exhibit_panel_'+title,x,1.5,z,width,height,.065,color,rotation=rotation,record=False)
    g.label(title,x,2.44,z+.045,width-.22,.25,rotation=rotation,color='#f3ebdb')
    # Original interpretation graphics, not unreadable imitations of copyrighted text.
    for j in range(4):
        g.box('exhibit_caption_rule',x,2.05-j*.12,z+.046,width*.62,.015,.02,'#d8c8af',rotation=rotation,record=False)

def history(scene):
    g=Geometry(scene);shell(g,12,19,3.5,'#302e2d',door_x=-3)
    # Dark, glossy, river-coloured floor observed in KTO interior photos.
    rng=random.Random(83)
    g.box('ground_floor_river_finish',0,.008,0,11.8,.015,18.8,'#365450')
    g.river_material('#365450')
    for x in range(-6,7,2):g.box('cutaway_black_ceiling_grid',x,3.43,0,.04,.07,19,'#1f2728',group='05_Cutaway_Roof',record=False)
    for z in range(-9,10,2):g.box('cutaway_black_ceiling_grid',0,3.43,z,12,.07,.04,'#1f2728',group='05_Cutaway_Roof',record=False)
    for x in (-3,3):
        for z in (-6,0,6):g.light(x,3.28,z,55)
    # Timeline wall with projecting white photo boxes.
    wall=Geometry(scene,(-5.85,0),-math.pi/2)
    for i,title in enumerate(['영산포의 시작','영산강과 포구','배가 드나들던 길','철도와 근대도시','영산포의 사람들']):
        xx=-7+i*3.4;panel(wall,title,xx,0,3.2,color='#737c80')
        wall.box('timeline_lit_box',xx,1.45,.15,1.75,.83,.2,'#e3dbc4',record=False)
        wall.label(str(1900+i*20)+'년대',xx,1.45,.265,1.4,.17,color='#404e50')
        for k in range(4):wall.box('original_town_silhouette',xx-.55+k*.36,1.23,.275,.25,.2+k%2*.16,.025,'#73827c',record=False)
    g.solids+=wall.solids;g.signs+=wall.signs
    wall=Geometry(scene,(5.84,0),math.pi/2)
    for i,title in enumerate(['영산포의 홍어','홍어와 사람들','포구의 맛','옹기와 살림']):panel(wall,title,-6.5+i*4,0,3.7,color=['#766e59','#ae8c6c','#887667','#756759'][i])
    # Skate silhouette on the interpretation wall.
    wall.mesh('skate_wall_silhouette',[(-7.6,1.3,.055),(-6.5,2.2,.055),(-5.4,1.3,.055),(-6.5,1.0,.055)],[(0,1,2,3)],'#384244')
    wall.tube('skate_tail',(-6.5,1,.055),(-6.5,.45,.055),.025,'#384244')
    g.solids+=wall.solids;g.signs+=wall.signs
    # Screen and a compact bow model are the exhibition's strongest visual anchor.
    g.box('boat_screen_frame',0,2.12,-9.12,4.3,2.25,.18,'#8f744a',record=False)
    g.box('boat_white_sail_screen',0,2.12,-9.0,3.95,1.95,.025,'#d8e2dc',record=False)
    g.label('영산강, 포구의 기억',0,2.2,-8.97,3.1,.21,color='#6d827c')
    boat=Geometry(scene,(0,-7.6),math.pi/2);boat.boat('exhibit_boat',0,0,.23,False,base=.17)
    g.signs+=boat.signs
    g.collider('exhibit-case_boat',[[-2.9,-8.4],[2.9,-8.4],[2.9,-6.8],[-2.9,-6.8]],0,1.0)
    # Low square stools leave a circulation aisle on both sides.
    for x in (-1.65,-.55,.55,1.65):
        g.box('square_brown_stool',x,.48,-1.9,.65,.17,.62,'#70523b',True)
        for dx in (-.23,.23):
            for dz in (-.21,.21):g.box('stool_metal_leg',x+dx,.23,-1.9+dz,.045,.46,.045,'#545d5a',record=False)
    for z in (1.4,3.4,5.4):
        g.box('exhibit-case_food',4.8,.65,z,1.3,1.3,1.6,'#56544c',True)
        g.glass('food_case_glass',4.8,1.55,z,1.25,.52,.04,math.pi/2)
        g.box('food_case_top',4.8,1.3,z,1.3,.04,1.6,'#d8d0ad',record=False)
        g.vessel('food_ceramic_plate',4.8,1.34,z,.43,'#e4daca',profile=[(0,.5),(.07,.6),(.13,.58)])
        for i in range(5):g.box('original_food_model',4.55+i*.1,1.43,z,.08,.06,.3,'#ba8280',record=False)
    for x in (-4.7,-3.5):
        g.vessel('straw_covered_onggi',x,0,5.1,1.25,'#5b4b3d');g.collider('exhibit-case_onggi',[[x-.55,4.55],[x+.55,4.55],[x+.55,5.65],[x-.55,5.65]],0,1.35)
        for j in range(18):
            a=j*math.tau/18;g.tube('onggi_straw', (x+math.cos(a)*.3,1.31,5.1+math.sin(a)*.3),(x+math.cos(a)*.64,.9,5.1+math.sin(a)*.64),.012,'#bd9c64',n=5)
    g.label('영산포 역사갤러리',-1.3,2.8,8.98,6.2,.36,rotation=math.pi,color='#d6c09a')
    g.label('홍어거리로 나가기',-3,2.52,9.38,1.8,.17,rotation=math.pi,color='#b5d5c4')
    g.box('walk-floor_exit',-3,-.04,10.0,2.2,.08,1.3,'#89847c')
    portals=[dict(id='history-exit',position=[-3,9.85],radius=.65,target='yeongsanpo',arrival='history-exit',label='문을 지나면 홍어거리로 나갑니다.')]
    places=[place('history-screen','배 모형과 돛 스크린',-2.5,-6,4,indoor=True),place('history-timeline','영산포의 시간',-3.5,0,4,indoor=True),place('history-food','홍어와 포구의 생활',2.7,4,4,indoor=True),place('history-entry','역사갤러리 입구',-3,7.5,3,indoor=True)]
    return g,world_data(g,'영산포 역사갤러리',[-6.1,6.1,-9.6,10.8],dict(x=-3,z=7.4,yaw=0),places,verticalNavigation=True,portals=portals,arrivals={'entry':dict(x=-3,z=7.4,yaw=0)},walkRoute=[[-3,7.4],[-2,5],[-2,0],[-2.5,0],[-2.5,-6],[-2.5,0],[2.7,0],[2.7,4],[0,7.4],[-3,7.4],[-3,9.85]])

def literature(scene):
    g=Geometry(scene);shell(g,18,18,3.15,'#e5dfcb',door_x=0)
    wood='#504333';lightwood='#796344';rng=random.Random(41)
    # A long glazed timber corridor along the garden; adjoining rooms are open.
    g.box('ground_floor_corridor',0,-.035,7.35,17.8,.07,3.0,wood)
    for i in range(65):g.box('corridor_plank_joint',0,.003,5.85+i*.048,17.8,.006,.009,'#8b7252',record=False)
    for x in (-7.5,-5.3,-3.1,3.1,5.3,7.5):g.window('garden_corridor_window',x,1.5,8.91,2.05,2.35)
    # Replace the front wall by glazed panels while retaining its collision boundary.
    for o in list(scene.objects):
        if o.name.startswith('museum-wall_front'):o.hide_render=True
    for x in (-9,-6,-3,0,3,6,9):
        if x not in (-6,0,6):g.box('timber_post',x,1.55,5.78,.14,3.1,.16,wood,True)
        if x not in (-6,0,6):g.window('corridor_lattice',x,1.4,5.78,2.6,2.35,lattice=True)
    g.box('corridor_lintel',0,2.74,5.78,18,.25,.20,wood)
    # Tatami joins, woven lines and dark patterned edge bands.
    for xi in range(9):
        for zi in range(7):
            x=-8+xi*2;z=-8+zi*2
            g.box('tatami_mat',x,.018,z,1.96,.035,1.96,['#a7a775','#b1af80','#a4a16d'][(xi+zi)%3],record=False)
            for dz in (-.96,.96):g.box('tatami_edge',x,.04,z+dz,1.96,.012,.055,'#505842',record=False)
            for j in range(13):g.box('tatami_weave',x,.04,z-.9+j*.15,1.86,.004,.006,'#949866',record=False)
    for x in (-8.85,0,8.85):
        for z in (-8.8,-3,2.8):g.box('room_timber_post',x,1.55,z,.14,3.1,.14,wood,True)
    # Central partitions have generous existing-style sliding door openings.
    for z in (-6.8,2):g.box('museum-wall_partition',0,1.3,z,.12,2.6,4.0,'#e7e0ca',True)
    for z in (-3,2.8):
        g.box('transom_beam',4.4,2.45,z,8.8,.2,.16,wood)
        for x in (1,3,5,7):g.window('geometric_transom',x,2.82,z,1.9,.48,lattice=True)
    for x in (-6,2,6):g.box('cutaway_ceiling_beam',x,3.06,0,.13,.17,18,wood,group='05_Cutaway_Roof',record=False)
    for z in (-7,-3,1,5):
        for a,b in ([(-9,-3.15),(-.85,9)] if z< -2.5 else [(-9,9)]):g.box('cutaway_crossbeam',(a+b)/2,3.04,z,b-a,.15,.12,wood,group='05_Cutaway_Roof',record=False)
    for x,z in [(4,3.8),(4,-1),(4,-6),(-5,2),(-5,-5),(0,7)]:g.light(x,2.95,z,65)
    for title,x,z in [('문순태와 타오르는 강',4.8,-8.82)]:
        panel(g,title,x,z,6.5,2.5,'#d6d0bb');g.label('문학과 영산포',x,1.7,z+.055,3.8,.21,color='#71594b')
        # Simple original river route diagram and book-cover blocks.
        for i in range(5):g.box('literary_timeline_node',x-2+i,1.08,z+.06,.14,.14,.025,'#938260',record=False)
        g.box('literary_timeline_line',x,1.08,z+.055,4,.016,.03,'#958368',record=False)
    east=Geometry(scene,(8.82,-1),math.pi/2)
    panel(east,'소설 속 영산강',0,0,6.4,2.5,'#d6d0bb')
    east.label('이야기를 따라 흐르는 강',0,1.7,.06,5,.24,color='#796448');g.signs+=east.signs
    # Library: open bookshelves on the west wall.
    for z in (-5.5,-2.7,0.1):
        g.box('exhibit-case_bookshelf',-8.25,1.25,z,1.1,2.5,2.5,wood,True)
        for shelf in range(5):
            y=.15+shelf*.48;g.box('bookshelf_shelf',-7.68,y,z,.08,.05,2.38,'#a08153',record=False)
            for k in range(16):
                h=rng.uniform(.26,.4);g.box('book_spine',-7.63,y+.05+h/2,z-1.06+k*.14,.07,h,.115,rng.choice(['#dedbc5','#cfb990','#80918c','#9d755d','#c6c7b3']),record=False)
    g.label('영산강 문학 서재',-7.58,2.66,-2.7,2.5,.22,rotation=math.pi/2,color='#514936')
    # Rear stairs photographed behind the library; height and dimensions estimated.
    stair_route=[];top=3.36
    for i in range(20):
        z=-2.75-i*.28;h=(i+1)*top/20
        g.box('walk-floor_literature_stair_'+str(i),-2,h/2,z,1.65,h,.3,'#796345')
        for x in (-2.94,-1.06):
            if x< -2 and i>=18:continue
            g.box('stair_side_guard',x,(h+.85)/2,z,.08,h+.85,.3,'#796345',True)
        stair_route.append([-2,z,h])
    g.box('walk-floor_attic_landing',-2,top-.06,-8.48,2.0,.12,1.0,wood)
    g.box('walk-floor_attic_reading',-5.6,top-.06,-2.9,5.4,.12,11.8,'#aaa575')
    g.box('walk-floor_attic_connector',-4,top-.06,-8.45,2.3,.12,1.05,wood)
    # Floor and furniture of the attic disappear for whole-house cutaway view.
    for o in scene.objects:
        if o.name.startswith('walk-floor_attic'):o['hide_in_overview']=True
    for side in (-1,1):
        g.tube('stair_handrail',(-2+side*.87,1.0,-2.6),(-2+side*.87,top+1,-8.35),.035,wood)
    g.railing('attic_open_edge',(-2.91,-7.85),(-2.91,3),top,glass=False)
    # Ceiling is removed above the upper room and stairwell; attic roof encloses it.
    ceiling=next(o for o in scene.objects if o.name.startswith('cutaway_ceiling') and 'beam' not in o.name)
    ceiling.hide_render=True
    for a,b in [(0.2,9)]:g.box('cutaway_east_room_ceiling',(a+b)/2,3.2,0,b-a,.13,18,'#39382f',group='05_Cutaway_Roof')
    g.box('cutaway_corridor_ceiling',0,3.2,7.4,18,.12,3,'#39382f',group='05_Cutaway_Roof')
    # Continuous opaque backing around the only opening: the actual stairwell.
    for name,x,z,w,d in [('west_edge',-8.65,-2.95,.7,12.1),('west_front',-4.4,4.5,9.2,3.1),('centre_front',-.35,1.45,1.1,8.9),('centre_rear',-.35,-5.8,1.1,6.4),('stair_front',-1.95,.25,2.3,5.5),('west_back',-5,-8.95,8.2,.18)]:
        g.box('cutaway_closed_ceiling_'+name,x,3.2,z,w,.14,d,'#39382f',group='05_Cutaway_Roof')
    # The stair opening reaches the attic, whose cap and high walls stop sky leaks.
    g.box('attic_stairwell_cap',-1.85,6.04,-5.75,2.35,.18,6.45,'#d3d1bb',group='05_Cutaway_Roof')
    g.box('attic_stairwell_east',-.76,4.63,-5.75,.16,2.9,6.45,'#ded7c0',True,group='05_Cutaway_Roof')
    for z in (-8.99,-2.53):g.box('attic_stairwell_end',-1.85,4.63,z,2.35,2.9,.16,'#ded7c0',True,group='05_Cutaway_Roof')
    # Seal the narrow seam between stairwell and reading-room ceiling.
    g.box('attic_cap_join',-2.8,5.87,-5.75,.3,.45,6.45,'#d3d1bb',group='05_Cutaway_Roof')
    g.roof('attic_roof',-4.55,top+2.35,-2.9,9,12,1.7,'#66665b')
    g.box('attic_wall',-8.85,top+1.05,-2.9,.12,2.1,11.8,'#ded7c0',True)
    g.box('attic_wall_door_opening',-2.9,top+1.05,-2.3,.12,2.1,10.6,'#ded7c0',True)
    for z in (-8.85,3):g.box('attic_wall_end',-5.6,top+1.05,z,5.4,2.1,.12,'#ded7c0',True)
    for z in (-5.5,-1.5,1):
        g.box('exhibit-case_low_reading_table',-5.65,top+.34,z,2.2,.1,1.1,'#a17b49',True)
        for dx in (-.85,.85):
            for dz in (-.35,.35):g.box('reading_table_leg',-5.65+dx,top+.145,z+dz,.075,.29,.075,wood,record=False)
        for x in (-6.35,-4.95):
            g.box('floor_chair_seat',x,top+.09,z+.95,.66,.14,.65,'#514838',record=False)
            g.box('floor_chair_back',x,top+.45,z+1.2,.7,.65,.07,wood,record=False)
        g.light(-5.6,top+2.2,z,50)
    for z in (-6,-3,0):
        g.window('attic_high_window',-8.76,top+1.7,z,1.7,.55,math.pi/2)
        for y in (.25,.9,1.55):g.box('attic_white_bookshelf',-3.22,top+y,z,.38,.045,2.6,'#dcded2',record=False)
        for zz in (z-1.3,z,z+1.3):g.box('attic_bookshelf_divider',-3.22,top+.85,zz,.38,1.5,.035,'#dcded2',record=False)
    g.box('attic_white_ceiling',-5.6,top+2.38,-2.9,5.6,.12,11.8,'#d3d1bb',group='05_Cutaway_Roof')
    for z in (-7,-2,2):
        for i in range(14):
            a=-8.4+i*.4;b=a+.4
            y1=top+2.1+.16*math.sin((a+8.4)/5.6*math.pi);y2=top+2.1+.16*math.sin((b+8.4)/5.6*math.pi)
            g.tube('attic_curved_dark_beam',(a,y1,z),(b,y2,z),.13,wood,'05_Cutaway_Roof',8)
    g.label('영산강 문학쉼터',-2,2.62,-2.55,1.6,.17,color='#514838')
    g.label('영산포 거리로 나가기',0,2.55,8.92,1.85,.17,rotation=math.pi,color='#65765b')
    g.box('walk-floor_exit',0,-.04,9.6,2.1,.08,1.4,wood)
    places=[place('lit-exhibit','문순태와 타오르는 강',4,1.5,4,indoor=True),place('lit-library','영산강 문학 서재',-5,-1,4,indoor=True),place('lit-reading','2층 문학쉼터',-5.6,-3.7,4,arrivalHeight=top,indoor=True),place('lit-corridor','정원을 향한 목조 복도',0,7.3,3,indoor=True)]
    return g,world_data(g,'타오르는 강 문학관',[-9.1,9.1,-9.1,10.4],dict(x=0,z=7.3,yaw=0),places,verticalNavigation=True,arrivals={'entry':dict(x=0,z=7.3,yaw=0)},portals=[dict(id='literature-exit',position=[0,9.65],radius=.6,target='yeongsanpo',arrival='literature-exit',label='현관을 지나면 영산포 거리로 나갑니다.')],stairs=stair_route,walkRoute=[[0,7.3],[6,7.3],[6,4],[4,0],[4,-5],[2,-4],[0,-4],[-2,-4.4]],limitations=['Room dimensions, transitions between photographed rooms and attic proportions are estimated.'])
