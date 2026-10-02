"""Bogam museum: mapped envelope, observed interior, report-traced burial positions.

Blender --background --python scripts/build_bogam_museum.py -- --render
Current interior wall, bridge and elevation dimensions remain explicitly estimated.
"""
import bpy
import json
import math
import random
import sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from museum_geometry import MuseumGeometry
from bogam_museum_detail import materials as detail_materials, stone_wall as detailed_stone_wall, flagstone_floor, finish_hall
OUTPUT=ROOT/'outputs/bogam-museum.blend'
if '--output-blend' in sys.argv:
    OUTPUT=ROOT/Path(sys.argv[sys.argv.index('--output-blend')+1])
if OUTPUT.exists() and '--replace' not in sys.argv:raise RuntimeError('Preserve your edits; existing output requires explicit --replace.')
frame=json.loads((ROOT/'knowledge/sources/bogam-museum-hall-frame.json').read_text(encoding='utf-8'))
trace=json.loads((ROOT/'knowledge/sources/bogam-museum-burials.json').read_text(encoding='utf-8'))
layout=json.loads((ROOT/'knowledge/sources/bogam-museum-layout.json').read_text(encoding='utf-8'))
scene=bpy.data.scenes.new('Bogam_Museum_Interior');bpy.context.window.scene=scene;scene.unit_settings.system='METRIC'
g=MuseumGeometry(scene,frame['hallFrame']['center'],frame['hallFrame']['worldXZangle'])
rng=random.Random(20162024)
box,mesh,segment,label=g.box,g.mesh,g.segment,g.label
detail_materials(g)
BASE=.12;BRIDGE=3.52
footprint=frame['completeBuildingFootprintInHallLocal'][:-1]
box('ground_base',0,-.5,14,160,1,180,'#9cac86',group='01_OSM_Envelope')
g.polygon('ground_floor_museum',footprint,0,BASE,'#829da5',group='01_OSM_Envelope')
g.mat('#829da5').node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.27

# Mapped envelope, with a photo-informed entrance gap in the southern visitor wing.
for i,(a,b) in enumerate(zip(footprint,footprint[1:]+footprint[:1])):
    height=10.5 if i in (0,1,6) else 7.4
    pieces=[(a,b)]
    if i==3:
        at=lambda t:[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]
        pieces=[(a,at(.54)),(at(.67),b)]
        segment('entrance_lintel',at(.54),at(.67),.35,3.9,'#cec9bb',base=3.5,collision=True)
        for t in (.54,.67):
            p=at(t);box('entrance_frame',p[0],1.75,p[1],.13,3.5,.15,'#5d6667',True)
    for j,(aa,bb) in enumerate(pieces):segment(f'museum-wall_{i}_{j}',aa,bb,.34,height,'#c9c6b9',collision=True,group='01_OSM_Envelope')
    # Horizontal joints in the pale stone cladding seen in interior photographs.
    if i in (0,1,6):
        for yy in (1.2,2.4,3.6,4.8,6,7.2,8.4,9.6):segment('wall_cladding_joint',a,b,.38,.014,'#b1b1a8',base=yy,record=False)
label('나주복암리고분전시관',-13,3.18,57.2,18,.55,color='#43554c')
label('NAJU BOGAM-RI TOMBS MUSEUM',-13,2.62,57.2,16,.23,color='#43554c')
box('information_desk',-20,.70,48,6,1.2,1.2,'#b28b62',True)
label('안내  INFORMATION',-20,1.1,48.62,4.8,.23,color='#f2ecdd')
label('전시실  ↑',-20,2.15,44.5,5,.45,color='#526667')

# Fine original material grain is supplied by bogam_museum_detail; no photo textures.

# The original excavation centres supply horizontal positions. Current replica elevations
# and exposed pit sizes are inferred, and are not the dimensions of the original chambers.
burials=[]
for i,b in enumerate(trace['burials']):
    x,z=b.get('mainChamberAnchor_xz_m',b['xz_m']);ew,ns=b['visibleEnvelope_m']
    if b['category']=='stone_burial':
        w=min(4.8,max(1.0,ew*.69));d=min(5.4,max(1.2,ns*.61));depth=.80
    else:w=min(2.9,max(.8,ew));d=min(3.1,max(.85,ns));depth=.42
    y=BASE+max(.25,3.1-(abs(x)/21)**1.3*1.5-(abs(z)/23)**1.8*2.0)+(i%3)*.20
    if b['id']=='S96':w=3.3;d=4.6;y=1.65;depth=1.25
    burials.append(dict(**b,model_center=[x,z],replica_floor=y,modelOpening=[w,d],opening_depth=depth,vertical_source='Estimated display level from photographs, not measured'))

bridge_path=[[-21.5,17.8],[-21.5,-19],[-6.7,-19],[-6.7,-3.8],[20.7,-3.8],[20.7,17.8]]
def distance_segment(x,z,a,b):
    dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)))
    return math.hypot(x-a[0]-dx*t,z-a[1]-dz*t)
def beneath_bridge(x,z):
    # Include the full square landing and a terrain-cell margin at each bend.
    # A circular path buffer alone leaves tall soil colliders beside outer corners.
    return (any(distance_segment(x,z,a,b)<1.18 for a,b in zip(bridge_path,bridge_path[1:]))
            or any(abs(x-p[0])<1.35 and abs(z-p[1])<1.35 for p in bridge_path[1:-1]))
for b in burials:
    if beneath_bridge(*b['model_center']):b['replica_floor']=min(b['replica_floor'],1.2)

def terrain(x,z):
    # Rounded base with deliberately exposed rectilinear excavation terraces.
    radius=(abs(x/20.1)**5+abs(z/22)**5)**.2
    h=BASE+4.25*min(1,max(0,(1-radius)/.43))
    # Broad level changes and a lightly irregular earth surface, visible in photos.
    h-=.20*(.5+.5*math.sin(x*.24+z*.11))*min(1,max(0,1-radius)*3)
    if -3<x<5 and -19<z<-14:h=BASE+5.6
    for b in burials:
        bx,bz=b['model_center'];w,d=b['modelOpening']
        if abs(x-bx)<w/2+.95 and abs(z-bz)<d/2+.95:
            h=min(h,b['replica_floor']+(1.62 if b['category']=='stone_burial' else .55))
        if abs(x-bx)<w/2+.32 and abs(z-bz)<d/2+.35:h=b['replica_floor']
    if beneath_bridge(x,z):h=min(h,2.5)
    return h

# Closed stepped height cells share the same heights as navigation collision proxies.
verts=[];faces=[];step=.25;nx=164;nz=180
vertex_heights=[[terrain(-20.5+i*step,-22.5+j*step) for i in range(nx+1)] for j in range(nz+1)]
heights=[[math.ceil(max(vertex_heights[j][i],vertex_heights[j+1][i],vertex_heights[j][i+1],vertex_heights[j+1][i+1])*10)/10 for i in range(nx)] for j in range(nz)]
for j in range(nz+1):
    for i in range(nx+1):verts.append((-20.5+i*step,vertex_heights[j][i],-22.5+j*step))
for j in range(nz):
    z=-22.5+j*step
    for i in range(nx):
        x=-20.5+i*step;h=heights[j][i]
        if h<=BASE:continue
        k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
    # Combine adjacent cells at equal height into long collision strips.
    start=0
    while start<nx:
        end=start+1;h=heights[j][start]
        while end<nx and heights[j][end]==h:end+=1
        if h>BASE:g.collider(f'replica_collision_{j}_{start}',[[-20.5+start*step,z],[-20.5+end*step,z],[-20.5+end*step,z+step],[-20.5+start*step,z+step]],BASE,h-BASE)
        start=end
soil_model=mesh('replica_excavation_surface',verts,faces,'#c28c56',smooth=True)
soil_model['elevation_source']='Photo-informed stepped exhibition surface, all heights estimated'
g.solids.append(dict(name='replica_outline',kind='building',position=[0,BASE,0],size=[1,6,1],footprint=[g.point(*p) for p in [[-20,-22],[20,-22],[20,22],[-20,22]]],color='#c59665',collision=False))

stone_colors=['#b9b5a8','#aaa99e','#989e99','#c1bdad','#929a99']
def stone_wall(name,x,z,w,d,y,levels=3):
    detailed_stone_wall(g,name,x,z,w,d,y,levels,rng,stone_colors)

for i,b in enumerate(burials):
    x,z=b['model_center'];w,d=b['modelOpening'];y=b['replica_floor'];bid=b['id']
    box('earth_support_'+bid,x,(BASE+y)/2,z,w+.12,y-BASE,d+.12,'#c28c56',record=False)
    if b['category']=='stone_burial':
        box('burial_floor_'+bid,x,y-.055,z,w,.11,d,'#ae9a7c',record=False)
        levels=5 if bid in ('S96','S12','S9') else (3+i%2)
        stone_wall(bid,x,z,w*.91,d*.92,y,levels)
        flagstone_floor(g,bid,x,z,w*.91,d*.92,y,rng,stone_colors)
        for k in range(2+(i%3)):
            g.vessel(bid+'_vessel',x-w*.25+k*w*.15,y+.12,z+d*.13,.18+.10*(k%3),'#65615a')
        if bid=='S96':
            # Recorded chamber interior is 3.80m long and 2.40–2.60m wide.
            b['recorded_chamber_internal']={'length':3.8,'southWidth':2.4,'northWidth':2.6,'preservedHeight':2.6,'source':'2001 report printed p138'}
            for k in range(4):
                g.vessel('S96_internal_jar_'+str(k),x-.67+(k//2)*1.34,y+.56,z+(-.77 if k%2==0 else .77),1.4,'#c9c2a9',horizontal=True,rotation=0 if k%2==0 else math.pi,profile=[(0,.10),(.10,.29),(.32,.40),(.74,.38),(1,.28),(1.1,.28),(1.1,.23),(.8,.26)])
        title='96 돌방무덤' if bid=='S96' else bid[1:]+'호 돌방무덤'
        box('burial_label_base_'+bid,x,y+.25,z+d/2+.48,min(1.35,w),.32,.065,'#473e32',record=False)
        label(title,x,y+.26,z+d/2+.516,min(1.28,w),.14,color='#f0e0bd',group='03_Report_Burials')
    elif b['category']=='jar_coffin':
        s=max(.38,min(1.3,max(w,d)*.42))
        angle=math.pi/2 if w>d else 0
        profile=[(0,.10),(.10,.24),(.25,.34),(.56,.40),(.87,.39),(1.1,.27),(1.12,.27),(1.12,.20),(.85,.30)]
        # Two mouths meet at the burial anchor. Earlier lid placement met the base.
        offset=.57*s
        g.vessel('burial_'+bid,x+math.sin(angle)*offset,y+.4*s,z-math.cos(angle)*offset,s,'#bcb8a2',horizontal=True,rotation=angle,profile=profile)
        g.vessel('burial_'+bid+'_lid',x-math.sin(angle)*offset*.94,y+.4*s,z+math.cos(angle)*offset*.94,s*.94,'#c8c4af',horizontal=True,rotation=angle+math.pi,profile=profile)
    else:
        box('burial_W1_wood_coffin',x,y+.16,z,1.8,.32,.78,'#75624a',record=False)
        for side in (-1,1):box('coffin_rim',x,y+.36,z+side*.37,1.8,.12,.09,'#574f40',record=False)

# Same-direction two-flight wooden stairs with a landing, as visible in 2024 photos.
def staircase(name,x,start_z,start_y,sign= -1,total=20,width=2.15):
    z=start_z;h=start_y;route=[]
    for i in range(total):
        run=1.2 if i==total//2 else .30
        if i!=total//2:h+=.17
        box('walk-floor_'+name+str(i),x,h-.08,z+sign*run/2,width,.16,run+.015,'#b68c55')
        route.append([x,z+sign*run/2,h]);z+=sign*run
    for side in (-1,1):
        xx=x+side*(width/2+.06)
        g.tube(name+'_sloping_handrail',(xx,start_y+1.06,start_z),(xx,h+1.06,z),.047,'#966e42')
        segment(name+'_side_collision',[xx,start_z],[xx,z],.09,h-start_y+1.1,'#8f9998',base=start_y,collision=True,record=True).hide_render=True
        o=scene.objects.get(name+'_side_collision')
        if o:bpy.data.objects.remove(o,do_unlink=True)
        for j in range(8):
            t=j/7;zz=start_z+(z-start_z)*t;hh=start_y+(h-start_y)*t
            g.tube(name+'_steel_post',(xx,hh,zz),(xx,hh+1.05,zz),.025,'#a2acab')
    return route,h,z

stair_route,h,end_z=staircase('main_stair_',-21.5,25,BASE,total=21)
# 20 risers × 0.17m = 3.40m above the 0.12m floor.
bridge_path[0]=[-21.5,end_z]
half_width=1.1
directions=[]
for a,b in zip(bridge_path,bridge_path[1:]):
    length=math.dist(a,b);directions.append(((b[0]-a[0])/length,(b[1]-a[1])/length))

# Separate square landings and straight decks share edges, never overlapping top faces.
# This closes the missing outside quadrant at each bend without flickering board joints.
for j,p in enumerate(bridge_path[1:-1],1):
    box('walk-floor_bridge_landing_'+str(j),p[0],BRIDGE-.09,p[1],2.2,.18,2.2,'#b39873')
    ux,uz=directions[j-1];nx,nz=-uz,ux
    for k in range(1,9):
        t=-half_width+k*2.2/9
        aa=[p[0]+ux*t+nx*1.04,p[1]+uz*t+nz*1.04]
        bb=[p[0]+ux*t-nx*1.04,p[1]+uz*t-nz*1.04]
        segment('bridge_landing_board_joint',aa,bb,.006,.003,'#6f6250',base=BRIDGE+.001,record=False)

for j,(a,b) in enumerate(zip(bridge_path,bridge_path[1:])):
    dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz);ux,uz=dx/length,dz/length;nx,nz=-uz,ux
    start=half_width if j else 0
    end=length-(half_width if j<len(directions)-1 else 0)
    aa=[a[0]+ux*start,a[1]+uz*start];bb=[a[0]+ux*end,a[1]+uz*end]
    segment('walk-floor_bridge_'+str(j),aa,bb,2.2,.18,'#b39873',base=BRIDGE-.18)
    for k in range(int(length/2)+1):
        t=k/max(1,int(length/2));x=a[0]+dx*t;z=a[1]+dz*t
        for side in (-1,1):box('bridge_black_support',x+nx*.83*side,(BRIDGE-.18)/2,z+nz*.83*side,.085,BRIDGE-.18,.085,'#303736',record=False)
    for k in range(int((end-start)/.25)):
        t=start+(k+.5)*.25;aa=[a[0]+ux*t+nx*1.04,a[1]+uz*t+nz*1.04];bb=[a[0]+ux*t-nx*1.04,a[1]+uz*t-nz*1.04]
        segment('bridge_board_joint',aa,bb,.006,.003,'#6f6250',base=BRIDGE+.001,record=False)

# Offset the complete path: outer rails extend around corners, inner rails meet at
# their intersection. Keep the stair entry open and close only the actual dead end.
rail_paths=[]
for side in (-1,1):
    points=[]
    for j,p in enumerate(bridge_path):
        before=directions[max(0,j-1)];after=directions[min(j,len(directions)-1)]
        den=1+before[0]*after[0]+before[1]*after[1]
        x=p[0]+side*1.04*(-before[1]-after[1])/den
        z=p[1]+side*1.04*(before[0]+after[0])/den
        if j==len(bridge_path)-1:x-=after[0]*.06;z-=after[1]*.06
        points.append([x,z])
    rail_paths.append(points)
    for j,(a,b) in enumerate(zip(points,points[1:])):
        name=f'bridge_rail_{j}_{side}'
        g.railing(name,a,b,BRIDGE,start_post=(j==0))
        segment(name+'_edge_fascia',a,b,.075,.22,'#8d7555',base=BRIDGE-.23,record=False)
        segment(name+'_glass_shoe',a,b,.045,.055,'#a2acab',base=BRIDGE+.055,record=False)
    # Small timber collars cover the handrail butt joints at each turn.
    for p in points[1:-1]:
        g.tube('bridge_corner_handrail_cap',(p[0],BRIDGE+1.025,p[1]),(p[0],BRIDGE+1.095,p[1]),.057,'#9e784c',n=16)
    sx=bridge_path[0][0]+side*1.135
    g.tube('bridge_stair_handrail_join',(sx,BRIDGE+1.06,end_z),(points[0][0],BRIDGE+1.06,points[0][1]),.045,'#9e784c')
end_a,end_b=rail_paths[0][-1],rail_paths[1][-1]
g.railing('bridge_terminal_rail',end_a,end_b,BRIDGE,start_post=False,end_post=False)
segment('bridge_terminal_fascia',end_a,end_b,.08,.22,'#8d7555',base=BRIDGE-.23,record=False)
segment('bridge_terminal_glass_shoe',end_a,end_b,.045,.055,'#a2acab',base=BRIDGE+.055,record=False)

# Main exhibit case: the post-2024 dark display wall and pale stepped ceramic shelf.
box('exhibit-case_pottery',23.6,1.85,5,1.5,3.5,16,'#302e29',True)
box('pottery_shelf',22.76,.63,5,1.24,.32,15.5,'#eee4d0',True)
label('고대인이 만든 무덤',22.80,3.05,5,11,.52,rotation=-math.pi/2,color='#e2cc96')
for i in range(29):
    z=-2.1+i*.5;y=.81
    if i%5==0:box('pottery_riser',22.45,1.01,z,.8,.40,.45,'#eee4d0',record=False);y=1.21
    g.vessel('display_pottery_'+str(i),22.4,y,z,.20+(i%5)*.14,['#615548','#716551','#968063','#b18b63'][i%4])
    box('small_object_caption',21.93,.83,z,.12,.025,.29,'#f2eadb',record=False)
case_glass=box('pottery_case_glass',21.85,1.77,5,.016,2.0,15.6,'#92b2b4',record=False)
label('토기와 옹관에 담긴 고대의 생활',22.80,2.65,5,11,.24,rotation=-math.pi/2)
for i in range(5):
    x=-13+i*6
    box('historical_exhibit_panel',x,2.2,-23.22,5.7,3.6,.16,'#48453c',record=False)
    label(['복암리 3호분','여러 모양의 무덤','영산강과 마한','옹관을 만들다','고대인이 살던 마을'][i],x,3.48,-23.08,4.9,.37)
    # Original line diagrams, not copied exhibition artwork or tiny fabricated paragraphs.
    for k in range(5):
        a=[x-1.9+k*.22,-23.03];b=[x+1.9-k*.22,-23.03]
        segment('panel_diagram_rule',a,b,.025,.018,'#bdb098',base=1.20+k*.21,record=False)
    g.vessel('panel_sample_'+str(i),x,BASE,-22.1,.7,'#93826b')

# South visitor wing: room locations follow the official scheme, dimensions are inferred.
def partition_room(name,x,z,w,d,door_side='south'):
    for side in (-1,1):segment(name+'_wall',[x+side*w/2,z-d/2],[x+side*w/2,z+d/2],.15,3.15,'#c9c6b9',collision=True)
    segment(name+'_back',[x-w/2,z-d/2],[x+w/2,z-d/2],.15,3.15,'#c9c6b9',collision=True)
    for side in (-1,1):segment(name+'_front',[x+side*w/2,z+d/2],[x+side*1.3,z+d/2],.15,3.15,'#c9c6b9',collision=True)
    box(name+'_lintel',x,2.88,z+d/2,2.6,.54,.15,'#c9c6b9',True)

partition_room('theatre',-8,34,14,13)
box('theatre_screen',-8,2.05,27.68,9.2,2.45,.08,'#d9ded6',record=False)
box('theatre_stage',-8,.24,28.5,11,.24,1.6,'#a88050',True)
label('영상실',-8,2.80,40.59,3,.38,color='#4c605d')
for row,count in enumerate([8,8,8,7,7]):
    for seat in range(count):
        x=-13.2+seat*1.45;z=30.4+row*1.65
        box('theatre_seat_'+str(row)+'_'+str(seat),x,.58,z,.58,.18,.58,'#a64438',True)
        box('theatre_seat_back',x,1.03,z+.3,.64,.87,.13,'#333b3c',True)
        for side in (-1,1):box('theatre_arm',x+side*.35,.82,z,.07,.08,.62,'#574c43',record=False)
label('복암리, 고대의 시간을 만나다',-8,2.2,27.74,7,.40,color='#465955')

partition_room('digital',10,32,14,10)
for a,b in [([4,28],[16,28]),([4,28],[4,34]),([16,28],[16,34])]:
    segment('digital_screen_frame',a,b,.10,2.4,'#303c47',base=.28,record=False)
label('디지털 실감 영상관',10,2.87,37.09,6,.31,color='#4c605d')
label('마한의 풍경',10,1.8,28.07,8,.47,color='#d5ccac')
label('화면 구성 재현 · 원본 영상 미포함',10,.72,28.07,8,.23,color='#d5ccac')

partition_room('experience',4,44,10,9)
label('교육체험실',4,2.83,48.59,4,.34,color='#4c605d')
for x in (1.3,6.5):
    for z in (41.5,45.2):
        box('experience_table',x,.73,z,3.1,.13,1.3,'#bc9d73',True)
        for side in (-1,1):box('experience_bench',x,.4,z+side*.94,2.8,.14,.36,'#be9b69',True)

# The upper book cafe uses the photographed grid bookshelf and low reading tables.
box('walk-floor_cafe',-13.25,BRIDGE-.11,51,38.5,.22,10,'#b19979')
box('walk-floor_cafe_west',-36.05,BRIDGE-.11,51,1.9,.22,10,'#b19979')
box('walk-floor_cafe_stair_landing',-33.8,BRIDGE-.11,47.35,2.6,.22,2.7,'#b19979')
for edge in [([-37,46],[6,46]),([-37,56],[6,56]),([6,46],[6,56])]:g.railing('cafe_glass_rail',*edge,BRIDGE)
label('역사 북카페',-15,BRIDGE+2.45,55.7,10,.48,rotation=math.pi,color='#5f5b47')
for x in range(-28,2,3):
    box('cafe_bookshelf_back',x,BRIDGE+1.25,55.4,2.85,2.5,.20,'#ad8961',True)
    for h in (.12,.72,1.34,1.96,2.54):box('cafe_bookshelf_shelf',x,BRIDGE+h,55.0,2.9,.06,.72,'#ba9871',record=False)
    for side in (-1,0,1):box('cafe_bookshelf_divider',x+side*.96,BRIDGE+1.3,55.0,.055,2.5,.72,'#ba9871',record=False)
    for k in range(20):
        xx=x-1.3+k*.132;yy=BRIDGE+.76+(k%3)*.62
        box('cafe_book',xx,yy+.2,54.93,.095,.39+(k%4)*.045,.29,['#6e7c70','#c2ad7e','#9d7461','#aaa596'][k%4],record=False)
for x in (-20,-12,-4,3):
    box('cafe_reading_mat',x,BRIDGE+.025,50,3.5,.05,3.4,'#c6bb9d',record=False)
    box('cafe_low_table',x,BRIDGE+.39,50,2,.14,1.2,'#a58050',True)
    for side in (-1,1):box('cafe_floor_cushion',x,BRIDGE+.10,50+side*1.03,1.2,.17,.59,'#82937b',record=False)
cafe_stairs,cafe_height,cafe_end=staircase('cafe_stair_',-34,55.9,BASE,total=21)
# Entry to the upper floor is reached through the cafe's open western edge.

# Black exposed trusses, spot fixtures and roof separate cleanly for the overhead view.
g.polygon('cutaway_main_roof',[[-25.15,-23.64],[25.45,-23.64],[25.45,23.64],[-25.15,23.64]],10.4,.25,'#353b39',group='05_Cutaway_Roof')
g.polygon('cutaway_visitor_roof',[[-25.12,23.64],[25.44,23.64],[10.008,54.649],[-39.196,57.952],[-40.359,45.108],[-25.055,43.196]],7.4,.22,'#ddd7c8',group='05_Cutaway_Roof')
for z in range(-22,24,4):
    g.tube('cutaway_truss_beam',(-25,9.7,z),(25,9.7,z),.065,'#303735','05_Cutaway_Roof')
    g.tube('cutaway_truss_top',(-25,10.25,z),(25,10.25,z),.065,'#303735','05_Cutaway_Roof')
    for x in range(-24,25,3):g.tube('cutaway_truss_diagonal',(x,9.7,z),(x+1.5,10.25,z),.025,'#303735','05_Cutaway_Roof')
for x in range(-24,26,4):g.tube('cutaway_longitudinal',(x,9.98,-23),(x,9.98,23),.055,'#303735','05_Cutaway_Roof')
for x in (-17,-6,6,17):
    for z in (-17,-3,13):
        g.tube('cutaway_spot_housing',(x,9.6,z),(x,9.31,z),.16,'#272f30','05_Cutaway_Roof',16)
        o=box('cutaway_spot_lens',x,9.29,z,.22,.035,.22,'#fff0ce',group='05_Cutaway_Roof',record=False)
        bsdf=g.mat('#fff0ce').node_tree.nodes['Principled BSDF'];bsdf.inputs['Emission Color'].default_value=(1,.85,.6,1);bsdf.inputs['Emission Strength'].default_value=3
        wx,wz=g.point(x,z);g.lights.append(dict(position=[wx,8.9,wz],color='#ffe6bd',intensity=190,distance=20))
        light_data=bpy.data.lights.new('Museum_area','AREA');light_data.energy=850;light_data.shape='DISK';light_data.size=7
        light=bpy.data.objects.new('Museum_area',light_data);scene.collection.objects.link(light);light.location=g.bp(x,9.1,z)
for x,z in [(-18,46),(-8,34),(10,32),(-15,51),(4,44)]:
    wx,wz=g.point(x,z);g.lights.append(dict(position=[wx,6.8,wz],color='#fff1d4',intensity=160,distance=17))
    data=bpy.data.lights.new('Visitor_wing_area','AREA');data.energy=600;data.size=8
    o=bpy.data.objects.new('Visitor_wing_area',data);scene.collection.objects.link(o);o.location=g.bp(x,6.8,z)

detail_manifest=finish_hall(g,scene,burials,BRIDGE,terrain)

def place(pid,name,arrival,position=None,height=0,radius=4,description=''):
    return dict(id=pid,name=name,position=g.point(*(position or arrival)),arrival=g.point(*arrival),arrivalHeight=height,radius=radius,indoor=True,description=description)
places=[
    place('bridge','3호분 관람교량',[-6.7,-10],[1,-4],BRIDGE,12,'석실과 옹관 사이로 이어지는 상부 관람로입니다. 교량의 높이와 세부 경로는 사진 기반 추정입니다.'),
    place('cafe','2층 역사 북카페',[-15,47.5],[-15,51],BRIDGE,18,'공식 사진의 격자 책장, 낮은 독서상과 매트를 참고했습니다. 가구 배치는 추정입니다.'),
    place('pottery','고대인이 만든 무덤',[20.5,7],[22,5],0,7,'2024년 개편 후 사진의 짙은 진열장과 밝은 선반, 토기를 재현했습니다.'),
    place('replica-front','3호분 재현 모형 앞',[-17.5,23.1],[0,14],0,26,'발굴도의 매장시설 위치와 현재 전시실 사진을 대조했습니다. 각 시설의 전시 높이와 절개 형상은 추정입니다.'),
    place('theatre','영상실',[-8,39],[-8,34],0,7,'공식 안내의 38석, 사진의 붉은 좌석과 전면 스크린을 반영했습니다. 원본 상영 영상은 포함하지 않습니다.'),
    place('digital','디지털 실감 영상관',[10,35.4],[10,32],0,5,'3면 스크린 공간을 재현했습니다. 실제 상영 콘텐츠를 복제한 화면은 아닙니다.'),
    place('experience','교육체험실',[4,47.5],[4,44],0,5,'공식 층별 안내에 맞춘 체험 공간입니다. 세부 방 크기와 가구는 추정입니다.'),
    place('lobby','1층 안내 로비',[-16,52],[-20,51],0,14,'전시관의 실제 지도 윤곽과 공식 층별 배치를 참고한 출발 공간입니다.'),
]
spawn=g.point(-16,52)
bridge_arrival=[bridge_path[-1][0]-directions[-1][0]*.6,bridge_path[-1][1]-directions[-1][1]*.6]
route_local=[[-16,52],[-24.2,52],[-24.2,43],[-22,28],[-21.5,25.3]]+[[r[0],r[1]] for r in stair_route]+bridge_path[1:-1]+[bridge_arrival]
world=dict(title='나주 산책',subtitle='복암리고분전시관 · 내부 사진과 발굴도 참고',source='© OpenStreetMap contributors, ODbL 1.0',source_url='https://www.openstreetmap.org/way/471352007',origin=layout['origin'],bounds=[-65,65,-65,80],spawn=dict(x=spawn[0],z=spawn[1],yaw=.1),verticalNavigation=True,solids=g.solids,signs=g.signs,places=places,lights=g.lights,buildings=[dict(osm_id='471352007',footprint=layout['building']['museumLocalXZ'][:-1],height=10.5,height_source='Photo-informed envelope heights, not measured')],burials=burials,walkRoute=[g.point(*p) for p in route_local],bridgeHeight=BRIDGE,stairs=dict(main=stair_route,cafe=cafe_stairs),limitations=[
    'Exterior footprint is OSM way471352007. Official floor icons establish relative room arrangement, not measured room walls.',
    'Official photos and post-renovation visitor photos dated 2024-08-17 inform ochre replica, pale blue-grey floor, black trusses, glass/metal/wood rails, stairs and dark pottery case.',
    '41 burial centres are manually traced from the 2001 excavation report, not a measured survey of the museum replica. Exposed sizes, elevations and museum alignment are inferred.',
    'Bridge height 3.52m includes 0.12m floor and 20 estimated 0.17m risers. Exact bridge path, exhibition partitions, room dimensions, lighting and furniture placement are estimates. Continuous corner landings, rail joints and terminal guard are model finishing details, not newly verified real-site measurements.',
    'The central replica uses an estimated stepped height surface. Ancient remains were not modelled as present-day human remains; the 2024 exhibition changed after the displayed skeleton was moved for study.',
    'Theatre has 38 seats per official description; screen content is original placeholder typography. Digital room retains three screens without redistributing the actual film.',
    'The 2F cafe is walkable. Unverified staff/service interiors, toilet interiors and 3F observatory interiors are not reproduced.',
    'This is a detailed reference model, not an exact current interior scan or as-built digital twin. Original photos, video and satellite imagery are not redistributed.',
])
world['lighting']={'exposure':1.12,'ambient':.95,'sun':.18}
world['exhibitionDetails']=detail_manifest
(ROOT/'public/bogam-museum-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(ROOT/'knowledge/sources/bogam-museum-model-provenance.json').write_text(json.dumps({k:world[k] for k in ('source','source_url','origin','buildings','burials','bridgeHeight','limitations')},ensure_ascii=False,indent=2),encoding='utf-8')

bpy.ops.object.camera_add(location=g.bp(61,64,82));camera=bpy.context.object;camera.name='Museum_cutaway_overview';camera.data.type='ORTHO';camera.data.ortho_scale=115;camera.data.clip_end=500
camera.rotation_euler=(Vector(g.bp(-4,1,14))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
scene.world=bpy.data.worlds.new('Museum_soft_ambient');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.63,.70,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.28
scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1700;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/bogam-museum.glb'),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
print(json.dumps(dict(objects=len(scene.objects),burials=len(burials),solids=len(g.solids),bridgeHeight=BRIDGE,blend=str(OUTPUT)),ensure_ascii=False))
if '--render-bridge' in sys.argv:
    camera.data.type='PERSP';camera.data.lens=26;camera.data.clip_start=.1
    scene.render.resolution_x=1400;scene.render.resolution_y=1000
    for name,eye,target in [('bogam-museum-corner-finished',(-21.5,5.24,-12),(-21.1,4.5,-19.4)),('bogam-museum-corner-detail',(-23.3,6.4,-21.8),(-20,3.7,-18)),('bogam-museum-end-finished',(20.7,5.24,11.5),(20.7,4.3,18))]:
        camera.location=g.bp(*eye);camera.rotation_euler=(Vector(g.bp(*target))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/'outputs'/f'{name}.png');bpy.ops.render.render(write_still=True)
if '--render' in sys.argv:
    for o in scene.objects:
        if o.get('hide_in_overview'):o.hide_render=True
    scene.render.filepath=str(ROOT/'outputs/bogam-museum-overview.png');bpy.ops.render.render(write_still=True)
    for o in scene.objects:
        if o.get('hide_in_overview'):o.hide_render=False
    camera.data.type='PERSP';camera.data.lens=22;camera.data.clip_start=.1
    for name,eye,target in [('bogam-museum-main',(-23.8,3.0,23),(0,2.5,-1)),('bogam-museum-bridge',(-6.7,5.24,-11),(3,2.7,7)),('bogam-museum-pottery',(21.9,2.0,12),(23,1.8,3)),('bogam-museum-cafe',(-24,5.24,47),(-8,4.6,54))]:
        camera.location=g.bp(*eye);camera.rotation_euler=(Vector(g.bp(*target))-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/'outputs'/f'{name}.png');bpy.ops.render.render(write_still=True)
