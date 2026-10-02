"""Entrance landscaping and adjacent streets; called by build_city.py.

OSM supplies the precinct, car park and road alignment. Photos inform the
materials and furniture; their dimensions and positions are estimates.
"""

def surroundings_local(p):
    f=hall_detail_frame;dx,dz=p[0]-f.origin[0],p[1]-f.origin[1]
    return [dx*f.u[0]+dz*f.u[1],dx*f.v[0]+dz*f.v[1]]


def surroundings_polygon(name,points,height,color,collision=False,base=0,group='01_Actual_Map'):
    # Direct meshes avoid repeated full-scene operator updates for the context block.
    pts=points[:-1] if points[0]==points[-1] else points;n=len(pts)
    frame=HeritageFrame([0,0],(1,0));frame.v=(0,1)
    verts=[(x,y,z) for y in (base,base+height) for x,z in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=frame.mesh(name,verts,faces,color)
    if group!=DETAIL_GROUP:
        groups[DETAIL_GROUP].objects.unlink(obj);groups[group].objects.link(obj)
    obj['source_class']=group;obj['collision']=collision
    solids.append(dict(name=name,kind='building',position=[0,base,0],size=[1,height,1],color=color,collision=collision,footprint=pts))
    return obj


def surroundings_segment(name,a,b,width,height,color,collision=False,base=0):
    length=math.dist(a,b)
    frame=HeritageFrame(a,((b[0]-a[0])/length,(b[1]-a[1])/length))
    return frame.box(name,length/2,base+height/2,0,length,height,width,color,collision)


def precinct_wall(a,b,name):
    """Continuous stone core, varied rubble faces and a pitched tiled coping."""
    parent=hall_detail_frame;length=math.dist(a,b)
    wa,wb=parent.point(*a),parent.point(*b)
    f=HeritageFrame(wa,((wb[0]-wa[0])/length,(wb[1]-wa[1])/length))
    f.box('hall-wall_boundary_'+name,length/2,.68,0,length,1.34,.52,'#b8b3a1',True)
    rng=random.Random(name);verts=[];faces=[]
    for side in (-1,1):
        for row in range(4):
            x=-rng.uniform(.1,.5)
            while x<length:
                width=rng.uniform(.38,.76);left=max(0,x+.025);right=min(length,x+width-.02)
                if right>left:
                    bottom=.04+row*.31+rng.uniform(-.025,.025);top=bottom+rng.uniform(.23,.285)
                    start=len(verts);zz=side*.268
                    verts += [(left+.04,bottom,zz),(right-.04,bottom-.018,zz),(right,top-.05,zz),(right-.08,top,zz),(left+.03,top+.015,zz),(left,top-.055,zz)]
                    faces.append(tuple(range(start,start+6)))
                x+=width
    rubble=f.mesh('precinct_rubble_face',verts,faces,'#928f7e')
    for col in ('#a09c89','#878b7f','#a8a58f','#777d73'):rubble.data.materials.append(material(col))
    for face in rubble.data.polygons:face.material_index=rng.randrange(5)
    f.mesh('precinct_pitched_tile_coping',[(x,y,z) for x in (0,length) for y,z in [(1.39,-.43),(1.66,0),(1.39,.43)]],[(0,1,4,3),(1,2,5,4)],'#4b514b')
    f.tube('precinct_wall_ridge',(0,1.69,0),(length,1.69,0),.105,'#65675b',10)
    for i in range(max(1,int(length/.24))):
        x=(i+.5)*length/max(1,int(length/.24))
        for side in (-1,1):
            f.tube('precinct_coping_tile',(x,1.66,0),(x,1.39,side*.46),.041,'#5e6359',7)


def shrub_strip(f,a,b,width=.65,height=.6):
    rng=random.Random(str(a)+str(b));length=math.dist(a,b);count=max(2,int(length/.48));verts=[];faces=[]
    for i in range(count):
        t=(i+.5)/count;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t
        # Low faceted rounded clumps: geometry is original, no photo texture.
        start=len(verts);radius=width*.64
        for level in range(5):
            phi=math.pi*level/4
            for j in range(9):
                angle=math.tau*j/9;rr=radius*rng.uniform(.88,1.12)
                verts.append((x+rr*math.sin(phi)*math.cos(angle),.16+height*.5+height*.46*math.cos(phi),z+rr*math.sin(phi)*math.sin(angle)))
        for level in range(4):
            for j in range(9):
                k=start+level*9+j;kn=start+level*9+(j+1)%9;faces.append((k,kn,kn+9,k+9))
    o=f.mesh('entrance_low_shrubs',verts,faces,'#657d3c',True)
    for color in ('#718644','#587239','#7b8b4b'):o.data.materials.append(material(color))
    for p in o.data.polygons:p.material_index=rng.randrange(4)


def parked_car(f,x,z,color,rotation=0):
    """Unbranded static context vehicles; placement does not represent live parking."""
    co,si=math.cos(rotation),math.sin(rotation)
    origin=f.point(x,z);u=(f.u[0]*co+f.v[0]*si,f.u[1]*co+f.v[1]*si)
    car=HeritageFrame(origin,u)
    car.box('parked_vehicle_body',0,.61,0,4.1,.59,1.75,color,True)
    car.box('parked_vehicle_cabin',-.15,1.03,0,2.15,.59,1.61,color)
    for side in (-1,1):
        car.box('vehicle_side_glass',-.14,1.09,side*.818,1.89,.38,.023,'#344e57')
        car.box('vehicle_window_pillar',-.12,1.08,side*.835,.08,.45,.03,color)
        for xx in (-1.28,1.25):
            car.tube('vehicle_tire',(xx,.36,side*.83),(xx,.36,side*.94),.31,'#343935',12)
            car.tube('vehicle_hub',(xx,.36,side*.943),(xx,.36,side*.95),.16,'#92958e',10)
    for side in (-1,1):
        car.box('vehicle_end_glass',side*1.245,1.06,0,.025,.35,1.45,'#354f57')
        for zz in (-.57,.57):car.box('vehicle_lamp',side*2.06,.70,zz,.025,.15,.32,'#e7d9a4' if side==1 else '#923d32')


def build_surroundings():
    f=hall_detail_frame
    boundary=next(w for w in ways if w['id']=='540205109')['points'][:-1]
    local=[surroundings_local(p) for p in boundary]
    # Mapped north, east and west boundary. The south line meets the gate sides,
    # leaving its actual middle passage open instead of sealing the frontage.
    for i in range(5):precinct_wall(local[i],local[i+1],str(i))
    for i in (6,7):precinct_wall(local[i],local[(i+1)%len(local)],str(i))
    precinct_wall(local[5],[26.95,-103.2],'front_east')
    precinct_wall([15.05,-102.8],local[6],'front_west')

    # Two lawns are shaped to the photographed frontage and the mapped east edge.
    lawn_polys=[('west',[[-5.7,-104.6],[16.4,-103.8],[17.6,-72],[-5.8,-72]]),('east',[[26.7,-102.8],[70.7,-100.7],[78.4,-71],[27.9,-71]])]
    for name,pts in lawn_polys:
        surroundings_polygon('ground_floor_entrance_lawn_'+name,[f.point(*p) for p in pts],.036,'#809957',base=.033,group=DETAIL_GROUP)
        rng=random.Random(name)
        for row in range(30):
            t=(row+.5)/30
            a=[pts[0][k]+(pts[3][k]-pts[0][k])*t for k in range(2)];b=[pts[1][k]+(pts[2][k]-pts[1][k])*t for k in range(2)]
            # Small low-contrast turf strokes avoid the old unbroken flat rectangles.
            for j in range(int(math.dist(a,b)/1.2)):
                q=rng.random();x=a[0]+(b[0]-a[0])*q;z=a[1]+(b[1]-a[1])*q
                f.box('lawn_fine_grass',x,.071,z,.22,.008,.055,rng.choice(['#7d9553','#889d5d','#7e9756']))
    for offset in (-3.7,3.7):
        a=[21.2+offset,-100];b=[22.75+offset,-71]
        wa,wb=f.point(*a),f.point(*b);surroundings_segment('walk-floor_path_brick_border',wa,wb,.40,.085,'#a57958')
        for j in range(52):
            t=j/51;f.box('path_border_paving_joint',a[0]+(b[0]-a[0])*t,.09,a[1]+(b[1]-a[1])*t,.42,.009,.018,'#715e4c')
    f.box('ground_floor_stele_bed',-3.5,.041,-80.5,3.3,.056,25.4,'#a88968')
    for x in (-5.2,-1.8):f.box('stele_bed_stone_edge',x,.11,-80.5,.13,.14,25.6,'#a79e88')

    # Paved apron outside the gateway. Its height stays a small walkable threshold.
    apron=[[-7,-110.2],[13,-109.3],[30,-108.3],[72.8,-105.3],[72.2,-103.9],[28,-101.5],[15,-101.2],[-6.5,-107]]
    surroundings_polygon('walk-floor_front_apron',[f.point(*p) for p in apron],.09,'#b8b5a7',group=DETAIL_GROUP)
    for j in range(8):
        for i in range(22):
            x=10.6+i*.93;z=-108.9+j*.84
            f.box('entry_granite_paver',x,.092,z,.88,.018,.79,['#bab8aa','#c1bdac','#b2b0a2'][(i+j*3)%3])
    # Timber roadside rail, interrupted at the public gate approach.
    for a,b in [([-6.8,-110.0],[15.8,-109.0]),([27,-107.7],[70.5,-103.8])]:
        count=max(2,int(math.dist(a,b)/2.4))
        for i in range(count+1):
            t=i/count;x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t
            f.tube('front_low_timber_post',(x,.08,z),(x,.64,z),.075,'#9b9887',10,True)
        f.tube('front_low_timber_rail',(a[0],.49,a[1]),(b[0],.49,b[1]),.054,'#9b998a',10)
        guard=f.box('hall-wall_front_timber_rail',(a[0]+b[0])/2,.49,(a[1]+b[1])/2,math.dist(a,b),.11,.11,'#9b998a',True,math.atan2(b[1]-a[1],b[0]-a[0]))
        bpy.data.objects.remove(guard,do_unlink=True)  # The visible rail is round; retain its collision proxy.
    # Low shrub borders stay beside the gate, leaving the forecourt and path clear.
    shrub_strip(f,[-5.2,-106.5],[8.7,-105.2],.72,.57)
    shrub_strip(f,[33,-103.8],[70.4,-101.2],.75,.63)
    for x,z,h,r in [(-2,-101,11.5,3.7),(37,-99,11.8,3.9),(72,-69,8.2,2.7),(-8.8,30,9.8,3.0)]:
        wx,wz=f.point(x,z);photo_tree(wx,wz,h,r)

    # A roofed visitor information board is visible left of the front gate.
    board=HeritageFrame(f.point(8,-104.7),f.u)
    for x in (-1.5,1.5):board.post('entrance_information_post',x,0,.1,2.42,.12,'#794f32')
    board.box('entrance_information_frame',0,1.48,0,3.1,1.78,.18,'#714b32',True)
    board.box('entrance_information_panel',0,1.49,-.108,2.79,1.53,.03,'#d5c8a7')
    detailed_roof(board,'entrance_information_roof',0,0,3.75,1.12,2.47,.67,False)
    board.text('entrance_information_title','나주 금성관',0,1.92,-.14,2.28,.30,'#373f32')
    board.text('entrance_information_en','GEUMSEONGGWAN',0,1.56,-.14,2.32,.13,'#52604b')
    board.text('entrance_information_direction','망화루  ·  정청  →',0,.99,-.14,2.3,.19,'#3e5140')
    # Diagram lines are original interpretive visitor information, not copied text.
    for i in range(3):board.box('information_diagram',-.57+i*.57,1.28,-.14,.34,.10,.02,'#7c8462')
    for x in (4.0,42.0,64.0):
        z=-102.6+(x-30)*.07
        f.box('front_wall_uplight',x,.19,z,.19,.25,.24,'#464f45')

    # The actual mapped western car park was previously left as featureless ground.
    parking=next(w for w in ways if w['id']=='478611741')
    surroundings_polygon('ground_floor_mapped_parking',parking['points'],.075,'#686f6d',group='01_Actual_Map')
    f.box('walk-floor_west_sidewalk',-9.4,.055,-34.5,2.45,.11,138,'#b6b7a9')
    f.box('west_sidewalk_curb',-10.65,.10,-34.5,.15,.20,138,'#c7c7b5')
    for z in range(-103,33,3):f.box('sidewalk_slab_joint',-9.4,.116,z,2.4,.008,.018,'#929b8f')
    for row,x,start,end in [('east',-13.6,-102,26),('west',-33.3,-94,27)]:
        for i,z in enumerate(range(start,end,5)):
            if row=='west' and z < -59:continue  # The mapped south end narrows around a bend.
            for dz in (-1.16,1.16):f.box('parking_bay_line',x,.080,z+dz,4.7,.012,.08,'#d8d7c3')
            f.box('parking_bay_end',x+(-2.34 if row=='west' else 2.34),.080,z,.08,.012,2.40,'#d8d7c3')
            if i%3!=1:
                parked_car(f,x,z,['#d9ddd4','#8d9a9b','#e0dfd2','#434e51','#b5c0bd'][i%5],0 if row=='east' else math.pi)
    # Preserve the actual parking aisles as an open route; no decorative cars there.
    for z in (-77,-35,10):
        f.box('parking_aisle_direction',-17.5,.081,z,.14,.014,2.5,'#d4d4bd')
        for s in (-1,1):f.box('parking_aisle_arrow',-17.5+s*.28,.081,z+1,.12,.014,.88,'#d4d4bd',rotation=s*.65)
    sign=HeritageFrame(f.point(-11.4,-106),f.u)
    sign.tube('parking_sign_post',(0,0,0),(0,2.1,0),.06,'#666f64',10,True)
    sign.box('parking_sign_panel',0,1.94,0,.63,.63,.08,'#3e695b')
    sign.text('parking_sign_text','P',0,1.94,-.05,.43,.45)

    # Road markings follow sourced centerlines, rather than an invented street grid.
    for way_id in ('130622795','330182897','800174812'):
        way=next(w for w in ways if w['id']==way_id)
        for a,b in zip(way['points'],way['points'][1:]):
            clipped=clip_segment(a,b)
            if not clipped:continue
            aa,bb=clipped;length=math.dist(aa,bb)
            if length<1:continue
            # A restrained center line; exact widths and markings are photo estimates.
            for i in range(int(length/5)):
                t=(i+.15)/max(1,int(length/5));tt=min(1,t+2.8/length)
                pa=[aa[k]+(bb[k]-aa[k])*t for k in range(2)];pb=[aa[k]+(bb[k]-aa[k])*tt for k in range(2)]
                surroundings_segment('street_yellow_centerline',pa,pb,.12,.062,'#c8b978',base=.005)
    for x,z in [(-42,-102),(-45,-18),(84,-100)]:
        f.tube('street_light_pole',(x,0,z),(x,5.6,z),.065,'#515e56',10,True)
        f.tube('street_light_arm',(x,5.5,z),(x+1,5.7,z),.05,'#515e56',10)
        f.box('street_light_head',x+1,5.68,z,.68,.14,.27,'#d5d5bc')

    # Streetside destinations are approachable; markers never send walkers into cars.
    for id,name,point,description in [('entrance-street','망화루 앞 거리',(21.2,-111),'박석 보행대와 기와담장을 따라 금성관 입구를 둘러보세요.'),('west-parking','금성관 서쪽 주차장',(-17,-104),'지도에 등록된 주차장과 담장 옆 보행길입니다.'),('gate-lawn','망화루 안 잔디마당',(22,-83),'중삼문으로 이어지는 돌길과 양쪽 잔디를 둘러보세요.')]:
        places.append(dict(id=id,name=name,position=f.point(*point),arrival=f.point(*point),radius=7,description=description))
    # The dark rectangular water body east of the wall is also mapped in OSM.
    water=next(w for w in ways if w['id']=='1268984920')
    surroundings_polygon('mapped_water_bank',water['points'],.09,'#9b9c83',group='01_Actual_Map')
    wp=water['points'][:-1];cx=sum(p[0] for p in wp)/len(wp);cz=sum(p[1] for p in wp)/len(wp)
    inset=[[cx+(p[0]-cx)*.945,cz+(p[1]-cz)*.972] for p in wp]
    surroundings_polygon('mapped_reservoir_water',inset,.015,'#405e55',True,.09,'01_Actual_Map')
    roof_observations=build_surrounding_roofs()
    return dict(precinctBoundary=boundary,parkingOutline=parking['points'][:-1],parkingOsmId=parking['id'],roofObservations=roof_observations,entranceRoute=[f.point(*p) for p in [(-17,-104),(-17,-112),(21.2,-111),(21.2,-98),(22.75,-76),(22.75,-68.2),(26,-27)]] ,sourceClass='OSM boundary, roads and parking; photo-estimated surface finishes, furniture and vehicle positions')


def context_facades(fp,height,name):
    """Generic estimated windows, recesses and eaves on observed exterior masses."""
    for index,(a,b) in enumerate(zip(fp,fp[1:]+fp[:1])):
        length=math.dist(a,b)
        if length<2:continue
        f=HeritageFrame(a,((b[0]-a[0])/length,(b[1]-a[1])/length))
        # The outline is CCW in browser X/Z; the frame's positive Z is exterior.
        count=max(1,int(length/3));spacing=length/count
        for j in range(count):
            x=(j+.5)*spacing;ww=min(1.55,spacing*.58)
            f.box(name+'_window_surround',x,height*.53,.024,ww+.12,1.24,.045,'#8b9288')
            f.box(name+'_window',x,height*.53,.054,ww,1.07,.035,'#4b6670')
            f.box(name+'_window_mullion',x,height*.53,.08,.044,1.10,.026,'#b6b8a6')
            f.box(name+'_window_sill',x,height*.53-.59,.09,ww+.2,.085,.22,'#b7b8a7')
        f.box(name+'_eave_band',length/2,height-.14,.045,length,.17,.13,'#a7a799')


def build_surrounding_roofs():
    data=json.loads((ROOT/'knowledge'/'sources'/'geumseonggwan-surrounding-roofs.json').read_text(encoding='utf-8'))
    grid=data['pixelGrid'];scale=2**grid['zoom']
    def from_pixel(p):
        lon=(grid['tileX']+p[0]/256)/scale*360-180
        lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*(grid['tileY']+p[1]/256)/scale))))
        return project(lon,lat)
    observations=[]
    for item in data['features']:
        fp=[from_pixel(p) for p in item['pixels']]
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(fp,fp[1:]+fp[:1]))
        if area<0:fp.reverse()
        height=item['height'];name='context_'+item['id']
        surroundings_polygon(name+'_wall',fp,height,'#c7c4b3',True,.025,DETAIL_GROUP)
        context_facades(fp,height,name)
        if item['roof']=='gable' and len(fp)==4:
            a,b,c,d=fp
            # A shallow corrugated roof spans the interpreted quadrilateral.
            f=HeritageFrame([0,0],(1,0));f.v=(0,1)
            r0=[(a[k]+d[k])/2 for k in range(2)];r1=[(b[k]+c[k])/2 for k in range(2)]
            points=[(p[0],height+.12,p[1]) for p in fp]+[(r0[0],height+1.1,r0[1]),(r1[0],height+1.1,r1[1])]
            f.mesh(name+'_metal_roof',points,[(0,1,5,4),(4,5,2,3),(0,4,3),(1,2,5)],item['color'])
            count=max(5,int(math.dist(a,b)/.55))
            for i in range(count+1):
                t=i/count
                for pa,pb in [(a,b),(d,c)]:
                    x=pa[0]+(pb[0]-pa[0])*t;z=pa[1]+(pb[1]-pa[1])*t
                    rx=r0[0]+(r1[0]-r0[0])*t;rz=r0[1]+(r1[1]-r0[1])*t
                    f.tube(name+'_roof_seam',(x,height+.15,z),(rx,height+1.12,rz),.021,item['color'],5)
        elif item['roof']=='gable':
            # Irregular outlines keep an estimated raised metal roof rather than a
            # silent flat-roof fallback. This small context roof is not measured.
            f=HeritageFrame([0,0],(1,0));f.v=(0,1)
            cx=sum(p[0] for p in fp)/len(fp);cz=sum(p[1] for p in fp)/len(fp);n=len(fp)
            verts=[(x,height+.12,z) for x,z in fp]+[(cx,height+1.1,cz)]
            f.mesh(name+'_metal_roof',verts,[(i,(i+1)%n,n) for i in range(n)],item['color'])
        else:
            surroundings_polygon(name+'_flat_roof',fp,.14,item['color'],False,height+.025,DETAIL_GROUP)
            for a,b in zip(fp,fp[1:]+fp[:1]):surroundings_segment(name+'_roof_parapet',a,b,.17,.33,'#a2a89b',False,height+.14)
        observations.append(dict(id=item['id'],footprint=fp,height=height,sourceClass='Imagery-interpreted roof coverage; facade, height and roof pitch estimated'))
    # The two OSM buildings outside the monument retain their source outlines.
    for building in buildings:
        if building['osm_id'] in ('610255925','832423355'):
            fp=building['footprint'][:]
            if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(fp,fp[1:]+fp[:1]))<0:fp.reverse()
            context_facades(fp,3.5,'mapped_neighbor_'+building['osm_id'])
    return observations
