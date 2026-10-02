"""Photographed riverside frontage, with separately documented roof coordinates.

Original editable geometry only. Archive photos establish facade types; roof
traces establish plan positions. Heights and detailed dimensions are estimates.
"""
import math, random
from yeongsanpo_geometry import Geometry
from yeongsanpo_street_detail import surface


def edge_frame(g, pts, index):
    a,b=pts[index],pts[(index+1)%len(pts)]
    area=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(pts,pts[1:]+pts[:1]))
    return Geometry(g.scene,[(a[k]+b[k])/2 for k in (0,1)],
                    math.atan2(b[1]-a[1],b[0]-a[0])+(math.pi if area>0 else 0)),math.dist(a,b)


def sash(g,name,x,y,z,w,h,door=False):
    # Opaque dark interior behind the glazing prevents a solid shell from
    # washing the window white. Aluminium details sit outside the wall plane.
    g.box(name+'_recess',x,y,z,w,h,.035,'#263c40',record=False)
    g.box(name+'_pane',x,y,z+.023,w-.10,h-.10,.014,'#587b80',record=False)
    g.box(name+'_reflection',x-w*.13,y+h*.19,z+.033,w*.69,h*.09,.007,'#799397',record=False)
    for dx in (-w/2,0,w/2):g.box(name+'_metal_stile',x+dx,y,z+.052,.045,h+.07,.055,'#bcc3bf',record=False)
    for dy in (-h/2,h/2):g.box(name+'_metal_rail',x,y+dy,z+.052,w+.07,.045,.055,'#b4bbb8',record=False)
    g.box(name+'_transom',x,y+(h*.27 if door else 0),z+.052,w,.034,.052,'#a4aeaa',record=False)
    g.box(name+'_sill',x,y-h/2-.06,z+.08,w+.18,.10,.20,'#a7a797',record=False)
    if door:
        for dx in (-.12,.12):g.box(name+'_pull',x+dx,y-.20,z+.105,.025,.36,.045,'#dbded4',record=False)


def ac(g,x,y,z):
    g.box('riverfront_ac',x,y,z,.83,.61,.44,'#d3d4c7',record=False)
    for i in range(9):g.box('riverfront_ac_grille',x-.31+i*.077,y,z+.229,.023,.40,.014,'#727f7a',record=False)
    for dx in (-.30,.30):g.box('riverfront_ac_bracket',x+dx,y-.36,z-.02,.055,.10,.54,'#6d756d',record=False)
    g.tube('riverfront_ac_pipe',(x+.39,y+.1,z-.08),(x+.54,.16,z-.1),.025,'#d4cdb8',n=6)


def canopy(g,width,y,color):
    g.mesh('riverfront_shop_canopy',[(-width/2,y,.12),(width/2,y,.12),(width/2,y-.24,.96),(-width/2,y-.24,.96)],[(0,1,2,3)],color)
    g.box('riverfront_canopy_front',0,y-.26,.96,width,.13,.055,color,record=False)
    for i in range(max(2,int(width/.52))):
        x=-width/2+(i+.5)*.52
        g.tube('riverfront_canopy_seam',(x,y+.01,.12),(x,y-.23,.96),.012,'#a6aaa0',n=5)
    for x in (-width*.40,width*.40):g.tube('riverfront_canopy_brace',(x,y-.55,.12),(x,y-.25,.90),.027,'#696d65',n=6)


def sign(g,text,width,y,color='#ebe8d9',ink='#9b3342',height=.72):
    g.box('riverfront_sign_fascia',0,y,.22,width,height,.16,color,record=False)
    for yy in (y-height/2,y+height/2):g.box('riverfront_sign_trim',0,yy,.32,width+.08,.035,.045,'#959991',record=False)
    g.label(text,0,y,.322,width-.5,height*.56,color=ink)


def roof(g,pts,h,config):
    kind=config['roofType'];col=config['roofColor'];pid=config['id']
    g.polygon('riverfront_roof_fascia_'+pid,pts,h,.15,col)
    if kind=='flat':
        for a,b in zip(pts,pts[1:]+pts[:1]):
            g.segment('riverfront_parapet_'+pid,a,b,.16,.48,config['wallColor'],base=h+.15,record=False)
            g.segment('riverfront_parapet_coping',a,b,.24,.07,'#a2a79b',base=h+.63,record=False)
        return
    p=list(pts)
    if math.dist(p[0],p[1])<math.dist(p[1],p[2]):p=p[1:]+p[:1]
    a=[(p[0][k]+p[3][k])/2 for k in (0,1)];b=[(p[1][k]+p[2][k])/2 for k in (0,1)]
    rise=config.get('rise',min(2.3,math.dist(p[0],p[3])*.23));e=h+.16
    if kind=='hip':
        a,b=([a[k]*.80+b[k]*.20 for k in (0,1)],[a[k]*.20+b[k]*.80 for k in (0,1)])
        faces=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    else:faces=[(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5)]
    g.mesh('riverfront_pitched_roof_'+pid,[(x,e,z) for x,z in p]+[(x,e+rise,z) for x,z in (a,b)],faces,col)
    g.tube('riverfront_roof_ridge_'+pid,(a[0],e+rise+.04,a[1]),(b[0],e+rise+.04,b[1]),.06,col,n=6)
    n=max(2,int(math.dist(p[0],p[1])/.50))
    for i in range(n+1):
        t=i/n;top=[a[k]+(b[k]-a[k])*t for k in (0,1)]
        for u,v in [(p[0],p[1]),(p[3],p[2])]:
            edge=[u[k]+(v[k]-u[k])*t for k in (0,1)]
            g.tube('riverfront_roof_sheet_seam',(edge[0],e+.025,edge[1]),(top[0],e+rise+.025,top[1]),.016,col,n=5)
    for u,v in [(p[0],p[1]),(p[3],p[2])]:
        g.tube('riverfront_eaves_gutter',(u[0],h+.10,u[1]),(v[0],h+.10,v[1]),.065,'#6c7d7d',n=7)


def frontage(g,pts,c):
    pid=c['id'];h=c['height'];kind=c.get('facade','shop')
    g.polygon('photo-building_riverfront_'+pid,pts,0,h,c['wallColor'],True)
    roof(g,pts,h,c)
    front,w=edge_frame(g,pts,0)
    levels=c.get('storeys',1)
    front.box('riverfront_'+pid+'_plinth',0,.21,.065,w,.42,.12,'#929486',record=False)
    for x in (-w/2+.13,w/2-.13):
        front.tube('riverfront_downpipe',(x,.08,.13),(x,h-.02,.13),.045,'#78817a',n=6)
    if kind=='warehouse':
        # Archive aerial: repeated blue gables, cream render and high vents.
        for index in (0,2):
            f,span=edge_frame(g,pts,index)
            doorw=min(3.8,span*.5)
            f.box('riverfront_warehouse_door',0,1.7,.06,doorw,3.4,.06,'#717d79',record=False)
            for i in range(int(doorw/.20)):
                f.box('riverfront_warehouse_door_flute',-doorw/2+.1+i*.20,1.7,.10,.025,3.25,.028,'#a3aaa0',record=False)
            sash(f,'riverfront_warehouse_high_vent',0,h-.67,.08,.84,.64)
            f.box('riverfront_warehouse_lintel',0,3.54,.12,doorw+.5,.18,.21,'#99998b',record=False)
        for index in (1,3):
            f,span=edge_frame(g,pts,index)
            for i in range(max(2,int(span/6))):
                x=-span/2+(i+.5)*span/max(2,int(span/6))
                sash(f,'riverfront_warehouse_side_vent',x,h-.82,.09,.9,.7)
                f.box('riverfront_warehouse_buttress',x-1.3,h/2,.09,.24,h,.22,'#c5c0ae',record=False)
        return dict(id=pid,footprint=pts,height=h,front=front.point(0,0),normal=front.point(0,1),roofType=c['roofType'],source=c.get('source','archive aerial'),facade=kind)
    # Shop bays vary with the actual facade type; no single repeating blank box.
    if kind=='house':
        sash(front,'riverfront_house_lower',w*.21,1.45,.10,w*.35,1.85,True)
        for x in (-w*.25,w*.23):sash(front,'riverfront_house_upper',x,h-1.25,.10,w*.30,1.65)
        front.box('riverfront_house_floor_band',0,3.0,.08,w,.21,.19,'#aead9a',record=False)
        # Visible exterior stair is facade detail, not an invented entrance.
        for i in range(17):
            top=.18+i*.18
            front.box('exhibit-case_riverfront_external_stair',-w*.35+(i/16)*w*.65,top/2,.55,w*.65/16,top,1.05,'#c6c5b6',True)
        front.tube('riverfront_stair_rail',(-w*.35,1,.98),(w*.30,4.0,.98),.035,'#858c83',n=6)
    elif kind=='large_hall':
        # Broad white three-storey facade in M288: closed ground shutters and
        # small high windows, rather than a repeated row of full-height shops.
        for i in range(3):
            x=-w/2+(i+.5)*w/3;ww=w/3-.30
            front.box('riverfront_hall_shutter',x,1.5,.07,ww,2.8,.055,'#b5b9ae',record=False)
            for j in range(19):front.box('riverfront_shutter_course',x,.17+j*.145,.109,ww,.018,.02,'#979f96',record=False)
        for floor in (1,2):
            for i in range(4):sash(front,'riverfront_hall_small_sash',-w/2+(i+.5)*w/4,3.1*floor+1.20,.10,1.16,1.18)
            front.box('riverfront_hall_floor_joint',0,3.1*floor+.16,.08,w,.04,.03,'#afb1a5',record=False)
        sign(front,'영산포',w*.40,h-.34,'#d7d7cc','#6b4952',.56)
    elif kind=='residence':
        sash(front,'riverfront_residential_entry',-w*.25,1.17,.1,1.15,2.22,True)
        for x in (0,w*.30):sash(front,'riverfront_residential_sash',x,1.75,.1,1.5,1.1)
        canopy(front,w-.1,2.65,'#9daba4')
    else:
        bays=3 if c.get('highSign') else max(1,int(w/3.4));bayw=w/bays
        for i in range(bays):
            x=-w/2+(i+.5)*bayw
            isdoor=not c.get('highSign') or i==1
            sash(front,'riverfront_'+pid+'_shop',x,1.32 if isdoor else 1.54,.10,bayw-.25 if isdoor else bayw-.43,2.34 if isdoor else 1.85,isdoor)
            if i<bays-1:front.box('riverfront_shop_pier',x+bayw/2,1.42,.12,.13,2.85,.20,c['wallColor'],record=False)
        canopy(front,w-.12,2.79,c.get('canopyColor','#768584'))
        if not c.get('highSign'):sign(front,c.get('label','홍어 · 삼합'),w-.16,3.22,c.get('signColor','#e8e3cf'),c.get('ink','#8f3e52'))
        if c.get('highSign'):
            front.box('riverfront_high_sign_wall',0,h+.40,.06,w,1.12,.18,c['wallColor'],record=False)
            front.box('riverfront_hongeosesang_red_fascia',0,h+.40,.23,w-.15,1.04,.16,'#ac3045',record=False)
            front.label('홍어',-1.30,h+.40,.324,2.70,.97,color='#fff4de')
            front.label('세상',1.30,h+.40,.324,2.70,.97,color='#edcf62')
        for floor in range(1,levels):
            yy=3.1*floor+1.30
            for i in range(bays):sash(front,'riverfront_'+pid+'_upper',-w/2+(i+.5)*bayw,yy,.11,bayw-.48,1.68)
            front.box('riverfront_storey_band',0,3.1*floor+.14,.11,w,.15,.13,'#9d9789',record=False)
        if levels>1:
            front.box('riverfront_sign_bracket',w/2-.18,4.1,.42,.06,1.75,.76,'#59635c',record=False)
            front.box('riverfront_projecting_sign',w/2-.18,4.1,.68,.22,1.55,.65,c.get('signColor','#945657'),record=False)
        if pid=='street_west_05':
            # Split orange/wood front and glazed upper bay in the 2018 photo.
            front.box('riverfront_geumseong_timber_front',-w*.25,4.40,.09,w*.48,2.72,.11,'#52453d',record=False)
            for i in range(15):front.box('riverfront_geumseong_cladding_joint',-w*.25,3.14+i*.18,.157,w*.48,.016,.015,'#81705a',record=False)
            sash(front,'riverfront_geumseong_upper_glass',-w*.25,4.65,.20,w*.40,1.8)
            front.box('riverfront_geumseong_upper_balcony',-w*.25,3.66,.52,w*.47,.10,.78,'#5a574a',record=False)
            for i in range(10):front.box('riverfront_geumseong_baluster',-w*.49+i*w*.046,4.08,.86,.025,.78,.028,'#454d46',record=False)
            front.box('riverfront_geumseong_balcony_top',-w*.25,4.49,.86,w*.48,.045,.055,'#59665a',record=False)
        ac(front,w/2-.75,.49,.46)
        # Pots are recorded obstacles; they remain beside each facade, not in lanes.
        pot_positions=(-w/2+.40,-w/2+1.05,-w/2+1.70,w/2-1.05,w/2-.40) if c.get('highSign') else (-w/2+.55,-w/2+1.18)
        for x in pot_positions:
            front.vessel('riverfront_flower_pot',x,0,1.13,.36,'#805c49')
            front.box('riverfront_planter_collision',x,.22,1.13,.44,.44,.44,'#805c49',True).hide_render=True
            front.rock('riverfront_pot_foliage',x,.57,1.13,.58,.45,.52,'#637f4a',random.Random(int(abs(x)*91)))
    # All alley returns receive small windows, joints and services, including
    # faces that are >22m away from the mapped riverside promenade axis.
    for side in (1,2,3):
        f,span=edge_frame(g,pts,side)
        f.box('riverfront_return_base',0,.18,.06,span,.36,.11,'#939589',record=False)
        for i in range(max(1,int(span/5))):
            x=-span/2+(i+.5)*span/max(1,int(span/5))
            sash(f,'riverfront_'+pid+'_return_window',x,min(h-1.0,2.25),.08,1.1,.9)
        if side==2:
            f.box('riverfront_rear_service_door',0,1.05,.08,.85,2.1,.07,'#798477',record=False)
            f.tube('riverfront_rear_conduit',(span*.34,.10,.1),(span*.34,h-.15,.1),.023,'#8a9085',n=5)
    g.solids+=front.solids;g.signs+=front.signs
    return dict(id=pid,footprint=pts,height=h,front=front.point(0,0),normal=front.point(0,1),roofType=c['roofType'],source=c.get('source','archive photograph and satellite'),facade=kind)


def courtyard(g,pts):
    """Low cream front wall and timber gate visible beside Hong-eo Sesang."""
    f,w=edge_frame(g,pts,0);depth=5.5
    f.box('walk-floor_riverfront_house_yard',0,.035,depth/2,w,.06,depth,'#b7b19b')
    for a,b in [(-w/2,-w*.10),(w*.12,w/2)]:
        f.box('hall-wall_riverfront_house_front',(a+b)/2,.72,depth,b-a,1.44,.22,'#d2cbb0',True)
        f.box('riverfront_wall_coping',(a+b)/2,1.46,depth,b-a+.05,.08,.29,'#b2af9d',record=False)
    for x in (-w/2,w/2):f.box('hall-wall_riverfront_house_return',x,.72,depth/2,.20,1.44,depth,'#d2cbb0',True)
    # Closed domestic gate: observation-only frontage, not a museum portal.
    gatew=w*.22
    f.box('hall-wall_riverfront_house_gate',w*.01,.90,depth,gatew,1.80,.10,'#534f3d',True)
    for i in range(12):f.box('riverfront_house_gate_slats',w*.01-gatew/2+(i+.5)*gatew/12,.9,depth+.065,.028,1.73,.055,'#9c865b',record=False)
    f.roof('riverfront_house_gate_tile_cap',w*.01,2.0,depth,gatew+.52,1.25,.35,'#685450',tiles=False)
    rng=random.Random(813)
    for i in range(11):
        x=-w/2+.55+i*(w*.45)/11;z=depth-1.1+rng.uniform(-.25,.25);height=rng.uniform(3.7,5.4)
        f.tube('riverfront_bamboo_stem',(x,0,z),(x,height,z),.031,'#748454',n=5)
        for y in (height*.65,height*.82,height):f.rock('riverfront_bamboo_crown',x,y,z,1.02,1.15,.82,'#547843',rng)
    g.solids+=f.solids


def finishes(g):
    for col in ('#d0cab9','#ddd7c8','#c4bea9','#d7d7cc'):
        surface(g,col,'plaster')


def paving(g,source,roads):
    """Photo-derived apron underlays the retained OSM road and pavement strips."""
    def inside(p,poly):
        result=False
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:result=not result
        return result
    def distance(p,a,b):
        d=[b[k]-a[k] for k in (0,1)];t=max(0,min(1,sum((p[k]-a[k])*d[k] for k in (0,1))/(sum(v*v for v in d) or 1)))
        return math.dist(p,[a[k]+d[k]*t for k in (0,1)])
    s=source['surfaces'][0];poly=s['worldFootprint'];axis=s['accessAxis']['worldCoordinates']
    surface(g,'#969b97','asphalt')
    # Top 0.044 is below existing road (0.056) and pavers (0.112), so their
    # geometry stays visible without coplanar overlaps or hidden curb strips.
    g.polygon('walk-floor_riverfront_parking_apron',poly,.008,.036,'#969b97')
    front=s['southBoundaryWorld']
    for a,b in zip(front,front[1:]):g.segment('riverfront_apron_edge',a,b,.15,.014,'#c2c3b7',base=.045,record=False)
    road=next(r for r in roads if r['id']=='way/729505193')
    slots=[];cars=[]
    for a,b in zip(road['points'],road['points'][1:]):
        length=math.dist(a,b);u=[(b[k]-a[k])/length for k in (0,1)];v=[-u[1],u[0]];theta=math.atan2(u[1],u[0])
        for i in range(int(length/2.65)):
            q=[a[k]+u[k]*(i+.5)*2.65 for k in (0,1)]
            if not(-160<q[0]<-72):continue
            center=[q[k]+v[k]*8.1 for k in (0,1)]
            f=Geometry(g.scene,center,theta)
            corners=[f.point(x,z) for x,z in [(-1.22,-2.15),(1.22,-2.15),(1.22,2.15),(-1.22,2.15)]]
            if not all(inside(p,poly) for p in corners):continue
            if min(distance(center,c,d) for c,d in zip(axis,axis[1:]))<4.4:continue
            for x in (-1.22,1.22):f.box('riverfront_parking_bay_line',x,.052,0,.075,.012,4.35,'#e5e5d8',record=False)
            f.box('riverfront_parking_end_line',0,.052,-2.15,2.45,.012,.075,'#e5e5d8',record=False)
            slots.append(center)
            if len(slots)%4==1:
                color=['#e5e5da','#6d858b','#aeb6b1','#4f5d68'][(len(slots)//4)%4]
                body=f.box('riverfront_parked_car_body',0,.59,0,1.78,.65,4.0,color,True)
                bevel=body.modifiers.new('Rounded_body_edges','BEVEL');bevel.width=.12;bevel.segments=2
                f.mesh('riverfront_car_upper',[(-.77,.88,-1.18),(.77,.88,-1.18),(.77,.88,1.13),(-.77,.88,1.13),(-.68,1.43,-.72),(.68,1.43,-.72),(.68,1.43,.62),(-.68,1.43,.62)],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],color)
                f.mesh('riverfront_car_windscreen',[(-.71,.98,1.05),(.71,.98,1.05),(.63,1.39,.66),(-.63,1.39,.66)],[(0,1,2,3)],'#3f5860')
                f.mesh('riverfront_car_rear_window',[(-.71,.98,-1.12),(-.63,1.39,-.76),(.63,1.39,-.76),(.71,.98,-1.12)],[(0,1,2,3)],'#3f5860')
                for x in (-.79,.79):
                    side=-1 if x<0 else 1
                    f.mesh('riverfront_car_side_glass',[(side*.766,.97,-1.02),(side*.694,1.38,-.68),(side*.694,1.38,.59),(side*.766,.97,.98)],[(0,1,2,3)],'#3f5860')
                    for z in (-1.25,1.26):f.tube('riverfront_car_tyre',(x-.12,.29,z),(x+.12,.29,z),.29,'#343c39',n=12)
                for x in (-.58,.58):
                    f.box('riverfront_car_headlight',x,.64,2.02,.42,.17,.026,'#e0dfbd',record=False)
                    f.box('riverfront_car_taillight',x,.63,-2.02,.38,.17,.024,'#aa554a',record=False)
                for z in (-2.02,2.02):f.box('riverfront_car_bumper',0,.37,z,1.72,.13,.08,'#69726b',record=False)
                cars.append(center)
            g.solids+=f.solids
    # Thin streetlights on the retained separator; exact interval is inferred.
    for x in (-171,-119,-77):
        a,b=road['points'][-3],road['points'][-2]
        t=(x-a[0])/(b[0]-a[0]);z=a[1]+(b[1]-a[1])*t+4.25
        g.tube('riverfront_blue_light_pole',(x,.06,z),(x,5.8,z),.054,'#708f97',n=7)
        g.box('riverfront_lamp_base',x,.26,z,.16,.42,.16,'#b1b5a7',True)
        g.tube('riverfront_light_arm',(x,5.78,z),(x+.72,5.95,z),.04,'#788e92',n=7)
        g.box('riverfront_streetlight_head',x+.75,5.93,z,.53,.16,.22,'#c2c5b6',record=False)
    return dict(surface=poly,accessRoute=axis,parkingSpaces=slots,parkedCars=cars,source=source['source'],captureDate='unknown',dimensions='photo-estimated')
