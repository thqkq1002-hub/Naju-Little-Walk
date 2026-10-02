"""2021–2024 photographed exhibit arrangement; original relief graphics, not archive scans."""
import math, random
from yeongsanpo_geometry import Geometry,world_data,place
from yeongsanpo_interiors import shell

def town_relief(g,x,y,z,w,h,seed=1):
    """Original monochrome port interpretation, explicitly distinguished from archival photos."""
    rng=random.Random(seed)
    g.box('original_port_graphic',x,y,z,w,h,.018,'#a5a39b',record=False)
    for i in range(14):
        xx=x-w*.46+i*w*.067;hh=rng.uniform(.12,.46)*h;ww=w*.061
        g.box('original_port_building',xx,y-h*.3+hh/2,z+.014,ww,hh,.025,rng.choice(['#5f625e','#787a71','#8c8c82']),record=False)
        g.mesh('original_port_roof',[(xx-ww*.65,y-h*.3+hh,z+.035),(xx+ww*.65,y-h*.3+hh,z+.035),(xx,y-h*.3+hh+ww*.3,z+.035)],[(0,1,2)],'#454b48')
        for j in (-.23,.23):g.box('original_port_window',xx+j*ww,y-h*.3+hh*.55,z+.035,ww*.18,hh*.22,.01,'#343b38',record=False)
    for j in range(4):g.box('original_river_line',x,y-h*.38-j*h*.024,z+.028,w*.95,.009,.013,'#777f77',record=False)

def rules(g,x,y,z,w,n=5,color='#b1a89b'):
    for j in range(n):g.box('interpretation_rule',x,y-j*.055,z,w*(.88 if j==n-1 else 1),.007,.008,color,record=False)

def history(scene):
    g=Geometry(scene);shell(g,12,19,3.5,'#3c3031',door_x=-3);rng=random.Random(83)
    for o in scene.objects:
        if o.name.startswith('cutaway_ceiling'):o.data.materials.clear();o.data.materials.append(g.mat('#111617'))
    floor=g.box('ground_floor_river_finish',0,.008,0,11.8,.015,18.8,'#334541');g.river_material('#334541')
    # Mottled finish is scaled over a large floor, with fine mineral detail.
    for uv in floor.data.uv_layers.active.data:uv.uv*=.46
    for x in range(-6,7,2):g.box('cutaway_black_ceiling_grid',x,3.43,0,.065,.10,19,'#141a1a',group='05_Cutaway_Roof',record=False)
    for z in range(-9,10,2):g.box('cutaway_black_ceiling_grid',0,3.43,z,12,.10,.065,'#141a1a',group='05_Cutaway_Roof',record=False)
    for i in range(61):g.box('cutaway_ceiling_mesh_x',-6+i*.2,3.46,0,.012,.025,19,'#23292a',group='05_Cutaway_Roof',record=False)
    for i in range(96):g.box('cutaway_ceiling_mesh_z',0,3.46,-9.5+i*.2,12,.025,.012,'#23292a',group='05_Cutaway_Roof',record=False)
    for x in (-4.5,4.5):
        g.box('cutaway_spotlight_track',x,3.3,0,.07,.06,18,'#151919',group='05_Cutaway_Roof',record=False)
        for z in (-7,-3,1,5,8):
            g.tube('cutaway_spot_stalk',(x,3.32,z),(x,3.08,z),.025,'#151919','05_Cutaway_Roof')
            g.tube('cutaway_spot_body',(x,3.08,z),(x+math.copysign(.19,x),2.9,z),.10,'#292e2b','05_Cutaway_Roof')
            g.light(x,3.04,z,40)
    for z in (-6,0,6):g.light(0,3.3,z,65)
    g.box('ceiling_projector',0,3.05,-4.7,.45,.17,.36,'#a8aaa3',record=False)
    g.tube('projector_lens',(0,3.02,-4.85),(0,3.02,-4.99),.055,'#34454c')
    west=Geometry(scene,(-5.81,0),-math.pi/2)
    # Long blue-grey timeline, with the observed three-over-four lightbox rhythm.
    west.box('timeline_backing',-1,1.7,0,10.7,2.35,.17,'#435e68',record=False)
    west.label('영산포 역사',-5.3,2.6,.1,1.6,.23,color='#e5e3d5')
    for i,(x,y,w,h) in enumerate([(-3.1,2.15,1.2,.77),(-.15,2.27,1.08,1.02),(2.65,2.19,1.1,.79),(-2.4,1.12,1.2,.76),(-.65,1.12,1.2,.70),(1.1,1.22,1.03,.68),(2.8,1.31,1.03,.95)]):
        west.box('timeline_lightbox_'+str(i),x,y,.27,w,h,.35,'#dddeda',record=False)
        town_relief(west,x,y,.451,w*.9,h*.87,i+11)
        west.label(['포구','정착','교역','시장','철도','영산포','오늘'][i],x,y-h/2-.105,.11,w,.12,color='#e0ddd0')
    points=[(-5.6,2.37),(-5.05,2.08),(-5.26,1.74),(-4.95,1.41),(-4.6,1.11),(-4.25,.82),(-3.4,.68)]
    for (x,y),(xx,yy) in zip(points,points[1:]):west.tube('timeline_diagonal',(x,y,.11),(xx,yy,.11),.01,'#bac9c5',n=5)
    for i,(x,y) in enumerate(points):
        west.tube('timeline_year_point',(x,y,.11),(x,y,.135),.035,'#c2d0c8',n=12)
        west.label(['고려','조선','1904','1910','1914','1937','1981'][i],x+.3,y,.12,.5,.09,color='#e1e2d7')
    for x in (-2.7,.3,3.2):rules(west,x,1.86,.11,1.12,6)
    town_relief(west,-1,.32,.02,10.7,.58,21)
    # Adjacent literary panels vary in height, size and projection.
    for i,(x,y,w,h) in enumerate([(5.3,2.2,1.4,1.35),(7,1.8,1.3,.95),(5.4,.85,1.5,.66),(7.2,2.65,1.2,.48)]):
        west.box('literary_staggered_panel',x,y,.15+i*.035,w,h,.12,'#8b7662' if i%2==0 else '#645650',record=False)
        west.label(['포구의 문학','영산강 이야기','사람들의 기억','남도의 풍경'][i],x,y+h*.32,.23+i*.035,w*.9,.13)
        rules(west,x,y,.23+i*.035,w*.8,5)
    g.signs+=west.signs
    east=Geometry(scene,(5.80,0),math.pi/2)
    for i,title in enumerate(['영산포의 유래','홍어와 사람들','포구의 맛','옹기와 살림']):
        x=-6.6+i*4.05
        east.box('full_height_interpretation_wall',x,1.72,0,4.0,3.38,.08,['#8b7770','#615550','#786160','#6a5554'][i],record=False)
        east.label(title,x,2.8,.051,3.2,.30,color='#e4d8bf');rules(east,x-.25,2.38,.051,2.8,7)
        town_relief(east,x,.45,.055,3.85,.85,i+30)
    for x in (-6.5,-2.5):
        east.box('recessed_monitor_border',x+1.12,1.77,.065,.74,.59,.07,'#151b1c',record=False)
        east.box('recessed_monitor',x+1.12,1.77,.105,.66,.49,.014,'#41605d',record=False)
        east.label('영산강',x+1.12,1.78,.118,.55,.11,color='#a9bbb3')
    east.mesh('skate_wall_relief',[(-3.4,1.4,.08),(-2.5,2.4,.08),(-1.6,1.4,.08),(-2.5,1.13,.08)],[(0,1,2,3)],'#283d3c')
    east.tube('skate_tail',(-2.5,1.15,.08),(-2.5,.75,.08),.02,'#283d3c')
    g.signs+=east.signs
    # Square projection screen with a timber vessel directly beneath it.
    g.box('boat_screen_frame',0,2.12,-9.05,3.5,2.60,.18,'#8e7047',record=False)
    g.box('boat_white_sail_screen',0,2.12,-8.94,3.13,2.32,.03,'#cbd6d3',record=False)
    g.label('영산강, 포구의 기억',0,2.3,-8.918,2.65,.21,color='#68807b')
    g.label('강을 따라 살아온 사람들',0,1.98,-8.917,2.35,.13,color='#68807b')
    boat=Geometry(scene,(0,-7.9),math.pi/2);boat.boat('exhibit_boat',0,0,.22,False,base=.18)
    g.signs+=boat.signs
    g.collider('exhibit-case_boat',[[-2.9,-8.5],[2.9,-8.5],[2.9,-6.85],[-2.9,-6.85]],0,1.0)
    for x in (-1.65,-.55,.55,1.65):
        g.box('square_brown_stool',x,.48,-1.9,.66,.17,.63,'#563b2d',True)
        for dx in (-.23,.23):
            for dz in (-.21,.21):g.box('stool_metal_leg',x+dx,.23,-1.9+dz,.045,.46,.045,'#434c49',record=False)
    # Three adjoining vitrines and an onggi alcove, as seen in close-up photographs.
    g.box('exhibit-case_food_base',4.87,.48,3.8,1.50,.96,5.45,'#474745',True)
    for k,z in enumerate((2,3.8,5.6)):
        g.box('food_case_cream_plinth',4.86,1.0,z,1.36,.08,1.63,'#d1cbb0',record=False)
        for x in (4.13,5.59):g.glass('vitrine_long_glass',x,1.32,z,1.72,.63,.02,math.pi/2)
        for zz in (z-.86,z+.86):g.glass('vitrine_end_glass',4.86,1.32,zz,1.44,.63,.02)
        topglass=g.box('vitrine_glass_lid',4.86,1.65,z,1.44,.015,1.72,'#97b6be',record=False)
        for x in (4.13,5.59):
            for zz in (z-.86,z+.86):g.tube('vitrine_corner',(x,1.01,zz),(x,1.65,zz),.012,'#4b5953',n=6)
        g.vessel('food_ceramic_plate',4.75,1.055,z,.63,'#e0ddd0',profile=[(0,.5),(.04,.6),(.075,.62),(.09,.57)])
        for j in range(15):
            a=j*math.tau/15;r=.17 if j<6 else .28
            g.box('food_slice',4.75+math.cos(a)*r,1.14,z+math.sin(a)*r,.075,.04,.16,['#b8746b','#997246','#bdb39a'][(j//5+k)%3],rotation=a,record=False)
        for zz in (z-.56,z+.56):g.vessel('food_small_bowl',5.24,1.05,zz,.24,'#d6d5c7',profile=[(0,.3),(.15,.4),(.24,.48),(.26,.43),(.15,.32)])
        g.label(['홍어회','홍어 삼합','홍어찜'][k],4.85,1.79,z+.75,.9,.13,color='#dedacb')
    x,z=4.88,7.8
    g.box('exhibit-case_onggi_plinth',x,.045,z,1.65,.09,1.9,'#665441',True)
    g.vessel('onggi_glazed_body',x,.09,z,1,'#555044',profile=[(0,.39),(.07,.47),(.5,.67),(1.02,.73),(1.30,.60),(1.48,.34),(1.52,.34),(1.54,.28),(1.45,.26)])
    g.collider('exhibit-case_onggi',[[x-.78,z-.8],[x+.78,z-.8],[x+.78,z+.8],[x-.78,z+.8]],0,1.65)
    for y,r in [(1.12,.72),(1.18,.70),(1.24,.67)]:
        for i in range(80):
            a=i*math.tau/80;b=(i+1)*math.tau/80
            g.tube('onggi_incised_band',(x+math.cos(a)*r,y,z+math.sin(a)*r),(x+math.cos(b)*r,y,z+math.sin(b)*r),.007,'#82765b',n=5)
    for j in range(100):
        zz=z+rng.uniform(-.14,.14);yy=1.65+rng.uniform(-.045,.045)
        g.tube('onggi_straw_bundle',(x-rng.uniform(.48,.78),yy,zz),(x+rng.uniform(.50,.8),yy+rng.uniform(-.035,.045),zz+.07),.0045,rng.choice(['#a38c53','#c5af70','#8e804f']),n=4)
    g.label('영산포 역사갤러리',-1.3,2.8,8.98,6.2,.36,rotation=math.pi,color='#d6c09a')
    g.label('홍어거리로 나가기',-3,2.52,9.38,1.8,.17,rotation=math.pi,color='#b5d5c4')
    g.box('walk-floor_exit',-3,-.04,10,2.2,.08,1.3,'#89847c')
    places=[place('history-screen','배 모형과 돛 스크린',-2.5,-6,4,indoor=True),place('history-timeline','영산포의 시간',-3.5,0,4,indoor=True),place('history-food','홍어와 포구의 생활',2.7,4,4,indoor=True),place('history-entry','역사갤러리 입구',-3,7.5,3,indoor=True)]
    return g,world_data(g,'영산포 역사갤러리',[-6.1,6.1,-9.6,10.8],dict(x=-3,z=7.4,yaw=0),places,verticalNavigation=True,portals=[dict(id='history-exit',position=[-3,9.85],radius=.65,target='yeongsanpo',arrival='history-exit',label='문을 지나면 홍어거리로 나갑니다.')],arrivals={'entry':dict(x=-3,z=7.4,yaw=0)},walkRoute=[[-3,7.4],[-2,5],[-2,0],[-2.5,0],[-2.5,-6],[-2.5,0],[2.7,0],[2.7,4],[0,7.4],[-3,7.4],[-3,9.85]],limitations=['Photographed arrangement and three-over-four timeline boxes recreated. Room dimensions are estimated. Original monochrome relief graphics replace copyrighted archival photographs and long panel text.'])
