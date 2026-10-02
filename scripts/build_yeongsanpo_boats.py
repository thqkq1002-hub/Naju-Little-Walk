"""Original editable photo-reference boat assets; metres, +X boarding, -Z bow.
Research photos/video are never bundled. Outputs use separate detail .blend files.
"""
import bpy, math, sys, json, gzip, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'outputs'
sys.path.insert(0,str(ROOT/'scripts'))
from yeongsanpo_geometry import Geometry

WOOD='#986443'; DARK='#563822'; TRIM='#734a30'; DECK='#ad794d'; CREAM='#e9dac1'; METAL='#788486'; BLACK='#242728'
DECK_Y=1.1

def grain(g):
    """Original packed grain, shared UV-continuous subtle varnished timber."""
    n=256;values=[]
    for j in range(n):
        for i in range(n):
            u=i/n;v=j/n
            warp=math.sin(v*math.tau)*.055+math.sin(v*math.tau*3)*.012
            fine=math.sin((u+warp)*math.tau*23)*.11+math.sin((u+warp)*math.tau*63)*.035
            knot=math.sin(math.sqrt(((u-.52)*2)**2+((v-.6)*.23)**2)*math.tau*20)*math.exp(-((u-.52)*10)**2)*.065
            val=.77+fine+knot;values.append(.48+.52*val)
    for col in [WOOD,DARK,TRIM,DECK,'#83512f','#bc8a59','#a5673d']:
        m=g.mat(col);nt=m.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.58
        # Bake the colour multiplication into a direct image. glTF cannot carry
        # the Blender MixRGB graph; exporting that graph loses the timber colour.
        rgb=tuple(bs.inputs['Base Color'].default_value)[:3]
        im=bpy.data.images.new('Original_timber_'+col[1:],width=n,height=n)
        pixels=[c for val in values for c in (rgb[0]*val,rgb[1]*val,rgb[2]*val,1)]
        im.pixels.foreach_set(pixels);im.pack()
        t=nt.nodes.new('ShaderNodeTexImage');t.image=im;t.extension='REPEAT'
        nt.links.new(t.outputs['Color'],bs.inputs['Base Color'])

def box(g,name,x,y,z,w,h,d,col=WOOD,collision=False,bevel=0):
    o=g.box(name,x,y,z,w,h,d,col,collision=collision,record=collision)
    if bevel:
        mod=o.modifiers.new('Soft timber edges','BEVEL');mod.width=bevel;mod.segments=2
    return o

def torus(g,name,x,y,z,r,t,col,axis='x',start=0,end=math.tau):
    n=max(8,round(40*(end-start)/math.tau));m=8;v=[]
    for i in range(n+1):
        a=start+(end-start)*i/n
        for j in range(m):
            b=j*math.tau/m;u=(r+t*math.cos(b))*math.cos(a);w=(r+t*math.cos(b))*math.sin(a);dep=t*math.sin(b)
            v.append((x+dep,y+u,z+w) if axis=='x' else (x+u,y+w,z+dep) if axis=='z' else (x+u,y+dep,z+w))
    return g.mesh(name,v,[(i*m+j,i*m+(j+1)%m,(i+1)*m+(j+1)%m,(i+1)*m+j) for i in range(n) for j in range(m)],col,smooth=True)

def buoy(g,x,z):
    torus(g,'safety_lifering',x,1.66,z,.29,.067,'#d77634')
    for a in [0,math.pi/2,math.pi,3*math.pi/2]:torus(g,'lifering_white_band',x-.002,1.66,z,.29,.07,'#e8e2cf',start=a-.14,end=a+.14)
    g.tube('lifering_hanger',(x,2.05,z),(x,1.88,z),.016,CREAM,n=6)

def flag(g,x,z,color,top=4.8,dragon=False):
    g.tube('ceremonial_flagpole',(x,DECK_Y,z),(x,top,z),.028,METAL,n=8)
    cols=14;rows=8;width=1.05;height=.72;v=[]
    for j in range(rows+1):
        for i in range(cols+1):
            u=i/cols;vv=j/rows
            v.append((x+u*width,top-.08-vv*height,z+math.sin(u*math.pi*2)*.09*u))
    g.mesh('ceremonial_flag',v,[(j*(cols+1)+i,j*(cols+1)+i+1,(j+1)*(cols+1)+i+1,(j+1)*(cols+1)+i) for j in range(rows) for i in range(cols)],color)
    # Original abstract traditional medallion, not copied from a photograph.
    points=[]
    for i in range(28):
        a=i/27*math.pi*3;u=.54+math.cos(a)*(.22-i/27*.12);vv=.43+math.sin(a)*.28
        points.append((x+u*width,top-.08-vv*height,z+math.sin(u*math.pi*2)*.09*u-.012))
    for a,b in zip(points,points[1:]):g.tube('flag_gold_emblem',a,b,.014,'#d8b854',n=5)

def outline(L,B):
    # Broad transom, rounded shoulders and rising bow from official photographs.
    return [(-B*.32,-L*.5),(B*.32,-L*.5),(B*.42,-L*.43),(B*.49,-L*.29),(B*.5,-L*.13),(B*.5,L*.2),(B*.45,L*.39),(B*.36,L*.5),(-B*.36,L*.5),(-B*.45,L*.39),(-B*.5,L*.2),(-B*.5,-L*.13),(-B*.49,-L*.29),(-B*.42,-L*.43)]

def hull(g,L,B,boat):
    pts=outline(L,B);n=len(pts);verts=[]
    layers=[(-1.3,.62,.86),(-.85,.76,.94),(-.25,.89,.99),(.45,.98,1),(1.08,1,1)]
    for y,sx,sz in layers:
        for x,z in pts:verts.append((x*sx,y+max(0,abs(z)/L-.36)*1.7,z*sz))
    faces=[tuple(range(n-1,-1,-1))]+[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(layers)-1) for i in range(n)]
    g.mesh('timber_hull_'+boat,verts,faces,'#83512f',smooth=True)
    g.polygon('ground_floor_boat_deck',pts,.93,.17,DECK)
    # Long timber strakes, caulking and outside gunwale follow hull profile.
    for j,(y,sx,sz) in enumerate(layers[1:]):
        for i in range(n):
            a=pts[i];b=pts[(i+1)%n]
            g.tube('hull_plank_seam',(a[0]*sx,y+max(0,abs(a[1])/L-.36)*1.7,a[1]*sz),(b[0]*sx,y+max(0,abs(b[1])/L-.36)*1.7,b[1]*sz),.028,DARK,n=6)
    for side in [-1,1]:
        # plank seams clipped to taper at each end
        for z in [(-L*.37)+i*.26 for i in range(int(L*.74/.26))]:
            box(g,'deck_caulk',0,1.106,z,B*.84,.009,.013,TRIM)
        break
    # Join the perimeter rail except the +X central boarding gate, 2.2 metres clear.
    railpts=[(x*.975,z*.99) for x,z in pts]
    for i,a in enumerate(railpts):
        b=railpts[(i+1)%n]
        if a[0]>B*.4 and b[0]>B*.4 and min(a[1],b[1])<0<max(a[1],b[1]):
            t0=(-1.1-a[1])/(b[1]-a[1]);t1=(1.1-a[1])/(b[1]-a[1])
            aa=(a[0]+(b[0]-a[0])*t0,-1.1);bb=(a[0]+(b[0]-a[0])*t1,1.1)
            railing(g,a,aa);railing(g,bb,b)
        else:railing(g,a,b)
    for side in [-1,1]:
        for z in [-L*.30,L*.27]:
            x=side*B*.5
            if boat=='najuho':
                for j in range(5):g.tube('yellow_rope_fender',(x,.18+j*.15,z),(x,.28+j*.15,z),.105,'#c9ac41',n=10)
                g.tube('fender_lashing',(x,2.1,z),(x,.82,z),.017,CREAM,n=6)
            else:torus(g,'rubber_fender',x,.30,z,.35,.10,'#282a28')
        buoy(g,side*(B*.5-.18),-L*.1);buoy(g,side*(B*.5-.18),L*.24)
    for side in [-1,1]:
        x=side*B*.30
        for z in [-L*.43,L*.43]:
            box(g,'mooring_bollard_base',x,1.14,z,.35,.08,.36,DARK)
            g.tube('mooring_bollard',(x,1.14,z),(x,1.57,z),.06,TRIM,n=10)
            g.tube('mooring_crossbar',(x-.18,1.47,z),(x+.18,1.47,z),.045,TRIM,n=8)
            torus(g,'coiled_mooring_rope',x+.32,1.15,z,.20,.023,CREAM,'y')
            torus(g,'coiled_mooring_rope',x+.32,1.15,z,.26,.023,CREAM,'y')
    for side in [-1,1]:
        x=side*(B*.5+.04)
        box(g,'vessel_nameplate',x,.52,0,.035,.32,4.6,DARK)
        g.label('영산강 황포돛배  '+('나주호' if boat=='najuho' else '왕건호'),x+side*.025,.54,0,4.35,.23,rotation=-side*math.pi/2,color=CREAM)
    return pts

def railing(g,a,b):
    if math.dist(a,b)<.05:return
    g.segment('deck_railing_collision',a,b,.15,1.13,DARK,base=1.1,collision=True).hide_render=True
    count=max(1,math.ceil(math.dist(a,b)/1.45))
    for y,h,w in [(2.16,.14,.19),(1.79,.10,.08),(1.43,.10,.08)]:
        g.segment('continuous_timber_handrail' if y>2 else 'horizontal_rail',a,b,w,h,TRIM,base=y-h/2,record=False)
    for i in range(count+1):
        t=i/count;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t
        box(g,'squared_rail_post',x,1.65,z,.16,1.13,.16,WOOD,bevel=.014)

def pane(g,name,x,z,w,h,side=False):
    rot=math.pi/2 if side else 0
    g.window(name,x,2.60,z,w,h,rotation=rot)
    # There is no glass in a door opening; glass only spans the surrounding fixed windows.

def cabin(g,name,w,z0,z1,side_door=False,end_doors=True):
    """Lower boarded walls plus real glass openings, all floor on continuous deck."""
    walltop=3.43
    for side in [-1,1]:
        x=side*w/2
        runs=[(z0,z1)]
        if side_door:runs=[(z0,-.82),(.82,z1)]
        for a,b in runs:
            if b<=a:continue
            box(g,name+'_side_boarded_wall',x,1.58,(a+b)/2,.14,.96,b-a,WOOD,True)
            # Window panes/frames are closed and collision is the full wall except door.
            box(g,name+'_window_collision',x,2.65,(a+b)/2,.12,1.7,b-a,WOOD,True).hide_render=True
            count=max(1,round((b-a)/1.16))
            for j in range(count):pane(g,name+'_side_window',x,(a+(j+.5)*(b-a)/count),(b-a)/count-.09,1.27,True)
        box(g,name+'_wall_plate',x,3.34,(z0+z1)/2,.17,.17,z1-z0,TRIM)
    for zz in [z0,z1]:
        box(g,name+'_continuous_end_header',0,3.35,zz,w+.08,.25,.18,TRIM)
        door=end_doors
        if door:
            for s in [-1,1]:
                a=s*(w/2+.72)/2;ww=w/2-.72
                box(g,name+'_end_wall',a,1.57,zz,ww,.94,.14,WOOD,True)
                box(g,name+'_end_window_collision',a,2.68,zz,ww,1.52,.13,WOOD,True).hide_render=True
                pane(g,name+'_end_window',a,zz,ww-.06,1.27)
            box(g,name+'_door_header',0,3.35,zz,1.52,.17,.17,TRIM)
            for x in [-.75,.75]:box(g,name+'_door_jamb',x,2.21,zz,.11,2.22,.19,DARK)
        else:
            box(g,name+'_end_wall',0,1.57,zz,w,.94,.14,WOOD,True)
            box(g,name+'_end_window_collision',0,2.68,zz,w,1.52,.14,WOOD,True).hide_render=True
            for x in [-w/3,0,w/3]:pane(g,name+'_end_window',x,zz,w/3-.075,1.27)
    if side_door:
        for side in [-1,1]:
            for z in [-.82,.82]:box(g,name+'_side_door_jamb',side*w/2,2.21,z,.21,2.22,.11,DARK)
            # Open leaf lies against the rear panel, never across entry.
            box(g,name+'_open_door_leaf',side*(w/2+.11),2.17,1.62,.09,2.08,1.48,WOOD)
            box(g,name+'_open_door_glass',side*(w/2+.17),2.54,1.62,.018,.94,1.13,'#70827d')
    return walltop

def seat(g,name,x,z,length,side=True):
    w=.53 if side else length;d=length if side else .53
    box(g,name+'_seat',x,1.59,z,w,.13,d,DECK,True,bevel=.025)
    for a in [-1,1]:
        xx=x if side else x+a*length*.38;zz=z+a*length*.38 if side else z
        box(g,name+'_leg',xx,1.31,zz,.12,.43,.13,DARK)
    if side:box(g,name+'_back',x+(.22 if x>0 else -.22),1.97,z,.085,.47,length,TRIM,bevel=.02)

def helm(g,z,w=1.7):
    # Controls are a functional recreation; photo reveals wheel/instrument desk, not exact gauges.
    box(g,'helm_console',0,1.59,z-.69,w,.98,.58,TRIM,True,bevel=.04)
    box(g,'helm_black_dashboard',0,2.07,z-.71,w+.08,.12,.65,BLACK)
    box(g,'navigation_display',.38,2.15,z-.68,.42,.24,.045,'#203a42')
    box(g,'navigation_screen',.38,2.16,z-.649,.35,.17,.008,'#41666f')
    for x in [-.57,-.35,-.13]:
        torus(g,'round_engine_gauge',x,2.20,z-.68,.065,.009,'#a7aaa1','z')
        g.tube('gauge_needle',(x,2.2,z-.665),(x+.027,2.23,z-.665),.005,CREAM,n=5)
    torus(g,'helm_wheel',0,1.95,z-.25,.265,.024,'#a2aaa6','z')
    for i in range(6):
        a=i*math.tau/6;g.tube('helm_wheel_spoke',(0,1.95,z-.25),(.26*math.cos(a),1.95+.26*math.sin(a),z-.25),.012,'#a2aaa6',n=6)
    g.tube('helm_shaft',(0,1.95,z-.26),(0,1.95,z-.59),.045,BLACK,n=12)
    box(g,'throttle_base',.67,2.16,z-.57,.16,.07,.23,METAL)
    for x in [.62,.72]:g.tube('engine_throttle',(x,2.18,z-.59),(x,2.38,z-.49),.018,BLACK,n=8)
    box(g,'vhf_radio',-.60,2.19,z-.64,.25,.13,.14,BLACK)
    g.label('조타실',0,3.15,z-1.06,1.35,.20,color=CREAM)

def roof_hanok(g,w,L,zc):
    # Ridge follows the ship. Closed soffit and full pitched shell keep sky out of the cabin.
    eave=3.46;rise=.91;half=w/2;hz=L/2;ridge=hz-1.35
    box(g,'continuous_cabin_ceiling',0,3.47,zc,w-.16,.10,L-.42,'#705137')
    verts=[(-half,eave,zc-hz),(half,eave,zc-hz),(half,eave,zc+hz),(-half,eave,zc+hz),(0,eave+rise,zc-ridge),(0,eave+rise,zc+ridge)]
    g.mesh('hanok_hip_roof',verts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)],'#69695e')
    g.tube('hanok_ridge',(0,eave+rise+.11,zc-ridge-.06),(0,eave+rise+.11,zc+ridge+.06),.105,'#7b7a6d',n=12)
    # Each cylindrical tile is an editable mesh, segmented to follow eave curl.
    count=int(L/.22)
    for side in [-1,1]:
        for i in range(count+1):
            z=zc-hz+i*L/count;rz=max(zc-ridge,min(zc+ridge,z))
            p=[(side*half,eave+.12,z),(side*half*.78,eave+rise*.17,z+(rz-z)*.22),(side*half*.38,eave+rise*.64,z+(rz-z)*.64),(0,eave+rise+.03,rz)]
            for a,b in zip(p,p[1:]):g.tube('ceramic_roof_tile',a,b,.052,'#818174',n=8)
    for end in [-1,1]:
        for i in range(1,18):
            x=-half+i*w/18
            g.tube('hip_end_tile',(x,eave+.1,zc+end*hz),(0,eave+rise+.02,zc+end*ridge),.045,'#818174',n=8)
    for x,z in [(0,zc-ridge),(0,zc+ridge),(-half,zc-hz),(half,zc-hz),(-half,zc+hz),(half,zc+hz)]:
        g.vessel('turquoise_roof_end_cap',x,eave+rise+.08 if x==0 else eave+.13,z,.42,'#36a2b1',profile=[(0,.18),(.18,.24),(.52,.17),(.68,0)])
    for side in [-1,1]:
        for i in range(count+1):
            z=zc-hz+i*L/count
            g.tube('exposed_eave_rafter',(side*(half-.6),3.47,z),(side*(half-.10),3.47,z),.05,TRIM,n=8)

def sail(g,z,top,width,bottom):
    g.tube('main_mast',(0,1.1,z),(0,top,z),.16,TRIM,n=16)
    # Only the mast base obstructs the deck; rigging stays overhead until rail anchorage.
    box(g,'mast_collision',0,2.1,z,.32,2,.32,TRIM,True).hide_render=True
    cols=18;rows=18;v=[]
    for j in range(rows+1):
        vv=j/rows;ww=width*(1-.16*vv)
        for i in range(cols+1):
            u=i/cols;v.append(((u-.5)*ww,bottom+(top-bottom-.55)*vv,z+.08+.54*math.sin(u*math.pi)+.08*math.sin(vv*math.tau*3)))
    o=g.mesh('battened_ochre_sail',v,[(j*(cols+1)+i,j*(cols+1)+i+1,(j+1)*(cols+1)+i+1,(j+1)*(cols+1)+i) for j in range(rows) for i in range(cols)],'#d6bd8b')
    o.modifiers.new('Sail cloth thickness','SOLIDIFY').thickness=.012
    for j in range(11):
        vv=j/10;ww=width*(1-.16*vv);yy=bottom+(top-bottom-.55)*vv
        for i in range(12):
            u=i/12;v1=(i+1)/12
            g.tube('sail_horizontal_batten',((u-.5)*ww,yy,z+.09+.54*math.sin(u*math.pi)+.08*math.sin(vv*math.tau*3)),((v1-.5)*ww,yy,z+.09+.54*math.sin(v1*math.pi)+.08*math.sin(vv*math.tau*3)),.017,'#836944',n=6)
    for side in [-1,1]:
        g.tube('mast_stay',(0,top-.3,z),(side*3.9,2.1,z+2.7),.014,'#b4a385',n=5)
        g.tube('halyard',(0,top-.15,z),(side*.21,1.35,z+.3),.012,'#cabb99',n=5)

def create(which):
    scene=bpy.context.scene;g=Geometry(scene);grain(g)
    L,B=(21.0,5.6) if which=='najuho' else (29.9,9.9)
    pts=hull(g,L,B,which)
    if which=='najuho':
        cabin(g,'hanok_passenger_cabin',3.2,-5.6,4.6,True,False)
        roof_hanok(g,4.46,11.2,-.5)
        # Partition with 1.44m open central passage into the wheelhouse.
        for side in [-1,1]:
            box(g,'helm_partition',side*1.17,1.61,-3.25,.86,1.02,.11,WOOD,True)
            pane(g,'helm_partition_glass',side*1.17,-3.25,.76,.98)
        helm(g,-4.3)
        for side in [-1,1]:
            seat(g,'interior_passenger_bench',side*1.15,2.70,2.80)
            seat(g,'interior_passenger_bench',side*1.15,-1.92,1.58)
            seat(g,'rear_outside_bench',side*2.06,7.4,2.60)
        seat(g,'rear_transom_bench',0,9.20,3.2,False)
        for x in [-1.02,1.02]:
            box(g,'ventilated_deck_chest',x,1.43,7.33,.87,.66,.90,WOOD,True)
            for j in range(6):box(g,'chest_vent_louver',x,1.21+j*.08,7.79,.72,.035,.025,DARK)
        for side in [-1,1]:
            flag(g,side*1.65,9.7,'#344c9a' if side<0 else '#b64028',4.75)
            flag(g,side*1.55,-9.65,'#e3e4d8' if side<0 else '#344c9a',4.50)
        route=[[B/2-.6,0],[0,0],[0,-2.45],[0,-3.65],[0,-4.3]]
        # Extra route describes the stern seating deck without crossing cabin walls.
        exploration=[[2.20,0],[2.20,5.4],[1.23,5.6],[0,6.3],[0,8.40]]
        note='나주호는 2010년 건조·49인승 한옥형 선박. 길이21.0m·폭5.6m는 공식 사진 속 사람·난간·객실의 비례로 추정했으며 공개 실측 제원 미확인. 갑판·선실·조타기 치수도 추정.'
        helmp=[0,-4.3]
    else:
        cabin(g,'forward_wheelhouse',4,-8.5,-4.5,False,True)
        cabin(g,'aft_passenger_cabin',5,1.4,8.4,False,True)
        for z,w,l in [(-6.5,4.75,4.65),(4.9,5.75,7.65)]:
            box(g,'closed_flat_cabin_ceiling',0,3.52,z,w,.18,l,'#bc8a59')
            for j in range(int(l/.20)):box(g,'roof_board_joint',0,3.62,z-l/2+j*.20,w,.013,.014,TRIM)
            for side in [-1,1]:box(g,'flat_roof_fascia',side*w/2,3.44,z,.13,.22,l,TRIM)
        # Close the wheelhouse bow with glass, keeping only the aft entry open.
        box(g,'wheelhouse_forward_lower_wall',0,1.58,-8.5,1.48,.96,.14,WOOD,True)
        pane(g,'wheelhouse_forward_center_glass',0,-8.5,1.41,1.27)
        box(g,'wheelhouse_front_glass_collision',0,2.75,-8.5,1.46,1.36,.12,WOOD,True).hide_render=True
        for x in [-.73,.73]:g.tube('front_window_wiper',(x,3.20,-8.57),(x-.17,2.39,-8.57),.019,BLACK,n=6)
        helm(g,-7.2,2.0)
        for side in [-1,1]:
            seat(g,'cabin_wall_bench',side*1.92,4.93,5.63)
            seat(g,'outer_rear_bench',side*3.6,10.1,3.75)
            flag(g,side*3.1,-12.55,'#344c9a' if side<0 else '#b64028',5.3)
            flag(g,side*3.15,12.85,'#e6e1d0' if side<0 else '#344c9a',5.3)
            box(g,'deck_storage_locker',side*3.25,-.01+1.5,-10.4,1.1,.80,1.05,WOOD,True)
        sail(g,-2.65,16.9,6.3,7.65)
        sail(g,10.0,13.7,5.5,6.6)
        route=[[B/2-.6,0],[1.2,0],[1.2,-3.7],[0,-4.5],[0,-6.2],[0,-7.2]]
        exploration=[[1.2,0],[0,0],[0,2.1],[0,7.7],[0,9.2],[1.2,9.2],[1.2,11.0]]
        note='왕건호 길이29.9m·폭9.9m는 2011년 준공 보도 제원. 선체높이3.16m·돛대 포함18.2m가 함께 보도됐으나 정확 수선·갑판 기준은 미확인. 갑판1.1m·내부 배치·조타기·삭구 치수는 사진 비례 추정.'
        helmp=[0,-7.2]
    # Roofs must remain visible while walking and during the public wide shot.
    for o in scene.objects:
        if 'hide_in_overview' in o:del o['hide_in_overview']
    meta=dict(id=which,name='나주호' if which=='najuho' else '왕건호',length=L,beam=B,dimensionsNote=note,deckHeight=DECK_Y,boarding=[B/2-.6,0],helm=helmp,hull=pts,solids=g.solids,walkRoute=route,exploreRoute=exploration,signs=g.signs)
    return g,meta

def run(which):
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;g,meta=create(which)
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    world=bpy.data.worlds.new('Reference daylight');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.62,.72,.77,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55
    ld=bpy.data.lights.new('Sun','SUN');ld.energy=2.3;ld.angle=.15;lo=bpy.data.objects.new('Sun',ld);scene.collection.objects.link(lo);lo.rotation_euler=(.3,-.45,-.5)
    # Warm photographic cabin fill is only for render; app uses its outdoor illumination.
    for z in [-4,3]:
        ld=bpy.data.lights.new('Cabin fill','AREA');ld.energy=65;ld.size=3;lo=bpy.data.objects.new('Cabin fill',ld);scene.collection.objects.link(lo);lo.location=g.bp(0,3.33,z)
    cd=bpy.data.cameras.new('Reference camera');cam=bpy.data.objects.new('Reference camera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.clip_start=.06;cd.clip_end=150;cd.lens=25
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1300;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    scene.render.film_transparent=False
    for o in list(scene.objects):
        if o.hide_render and o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
    camera_views=[('exterior',(24,18,-28),(0,4,0)),('deck',(meta['beam']/2-.64,2.82,1.6),(0,2.6,-5)),('helm',(0,2.82,-2.3 if which=='najuho' else -4.7),(0,2.65,meta['helm'][1]-.6))]
    eye,target=camera_views[0][1:];cam.location=g.bp(*eye);cam.rotation_euler=(Vector(g.bp(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    for o in scene.objects:
        if o.type=='MESH':o['boat_id']=which
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(which+'-detail.blend')))
    glb=ROOT/'public/models'/(which+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True,export_animations=False)
    (ROOT/'public/models'/(which+'.glb.gz')).write_bytes(gzip.compress(glb.read_bytes(),compresslevel=9,mtime=0))
    (ROOT/'knowledge/sources'/(which+'-navigation.json')).write_text(json.dumps(meta,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    print(json.dumps({'boat':which,'objects':len(scene.objects),'solids':len(g.solids),'glb':glb.stat().st_size}),flush=True)
    if '--render' in sys.argv:
        for label,eye,target in camera_views:
            cd.lens=43 if label=='exterior' and which=='najuho' else 32 if label=='exterior' else 25
            cam.location=g.bp(*eye);cam.rotation_euler=(Vector(g.bp(*target))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(HERE/(which+'-'+label+'.png'));bpy.ops.render.render(write_still=True)

if __name__=='__main__':
    HERE.mkdir(exist_ok=True)
    for key in ['najuho','wanggeonho']:
        if '--only' in sys.argv and key!=sys.argv[sys.argv.index('--only')+1]:continue
        run(key)

