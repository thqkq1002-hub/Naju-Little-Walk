"""OSM topology + manually observed 2022 roofs; executed by the school builder.

No source photographs are embedded. Every added building has a source record.
Roof profiles, openings and construction heights remain modelling estimates.
"""
SURVEYS = [json.loads((ROOT/'knowledge/sources'/name).read_text(encoding='utf-8')) for name in ('dasi-west-north-survey.json','dasi-east-south-survey.json')]
NG='06_Neighborhood_Mapped'
IG='07_Neighborhood_Image_Trace'
RG='08_Railway'

def open_ring(p):
    return p[:-1] if p and p[0] == p[-1] else p[:]

def inside(p, ring):
    yes=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>p[1]) != (b[1]>p[1]) and p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:yes=not yes
    return yes

def clip_ring(pts):
    pts=open_ring(pts)
    for axis,edge,minimum in ((0,bounds[0],True),(0,bounds[1],False),(1,bounds[2],True),(1,bounds[3],False)):
        result=[]
        if not pts:break
        for a,b in zip(pts,pts[1:]+pts[:1]):
            ai=a[axis]>=edge if minimum else a[axis]<=edge
            bi=b[axis]>=edge if minimum else b[axis]<=edge
            if ai:result.append(a)
            if ai!=bi:
                t=(edge-a[axis])/(b[axis]-a[axis])
                result.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])])
        pts=result
    return pts

def center(pts):return [sum(p[i] for p in pts)/len(pts) for i in (0,1)]

def overlap(a,b):
    if any(inside(p,b) for p in a) or any(inside(p,a) for p in b):return True
    def orient(p,q,r):return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    for p,q in zip(a,a[1:]+a[:1]):
        for r,s in zip(b,b[1:]+b[:1]):
            if orient(p,q,r)*orient(p,q,s)<0 and orient(r,s,p)*orient(r,s,q)<0:return True
    return False

def road_width(w):
    return {'footway':2.2,'path':1.8,'steps':2,'track':3,'service':3.8,'residential':6.5,'tertiary':8,'secondary':8.5,'primary':12,'trunk':12}.get(w['tags']['highway'],6)

def neighborhood_gate_opening(a,b):
    global neighborhood_gate
    dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz);ux,uz=dx/length,dz/length
    for c,d in zip(ways['592336461']['points'],ways['592336461']['points'][1:]):
        ex,ez=d[0]-c[0],d[1]-c[1];den=dx*ez-dz*ex
        if abs(den)<1e-7:continue
        t=((c[0]-a[0])*ez-(c[1]-a[1])*ex)/den
        u=((c[0]-a[0])*dz-(c[1]-a[1])*dx)/den
        if 0<=t<=1 and 0<=u<=1:break
    else:raise RuntimeError('Mapped school approach must intersect the campus boundary')
    x,z=a[0]+dx*t,a[1]+dz*t
    neighborhood_gate=dict(center=[x,z],tangent=[ux,uz],approach_osm_id='592336461',opening_width=15,placement_source='Intersection of OSM campus edge and mapped entrance service road; pillar spacing estimated')
    for side,aa,bb in [('west',a,[x-ux*7.5,z-uz*7.5]),('east',[x+ux*7.5,z+uz*7.5],b)]:
        segment('boundary_wall_2_'+side,aa,bb,.35,.45,'#b9b9a8',True)
        segment('boundary_rail_2_'+side,aa,bb,.09,.065,'#566c61',base=1.2)
        count=max(1,int(math.dist(aa,bb)/2.2))
        for j in range(count+1):
            p=[aa[k]+(bb[k]-aa[k])*j/count for k in (0,1)]
            cylinder('boundary_post_2_'+side,p[0],.76,p[1],.035,1.05,'#536b60',8)

def relocate_school_gate():
    from mathutils import Matrix
    x,z=neighborhood_gate['center'];ux,uz=neighborhood_gate['tangent']
    # Old east-facing presentation gate is preserved in the original school file.
    # In this new scene align it to the mapped south approach and synchronise physics.
    phi=math.atan2(ux,-uz)
    matrix=Matrix.Translation(Vector(bp(x,0,z))) @ Matrix.Rotation(-phi,4,'Z') @ Matrix.Translation(Vector(bp(-82.5,0,-6)))
    def target(name):return name.startswith('gate_') or name=='centenary_monument' or name.startswith('label_다\n시\n초') or name=='label_개교\n100주년'
    for obj in list(scene.objects):
        if target(obj.name):obj.matrix_world=matrix @ obj.matrix_world
    def point(p):
        dx,dz=p[0]-82.5,p[2]-6
        return [x+dx*math.cos(phi)-dz*math.sin(phi),p[1],z+dx*math.sin(phi)+dz*math.cos(phi)]
    for s in solids:
        if target(s['name']):s['position']=point(s['position']);s['rotation']=s.get('rotation',0)-phi
    for sign in signs:
        if sign['text'] in ('다\n시\n초\n등\n학\n교','개교\n100주년'):
            sign['position']=point(sign['position']);sign['rotation']=sign.get('rotation',0)-phi

def build_neighborhood_ground():
    # Large mapped parcels first. Traced surfaces below roads/campus avoid seams.
    colors={'farmland':'#adb77d','residential':'#c2c4b4','commercial':'#b4b7ae','railway':'#b1aea0','forest':'#778a63'}
    for wid,w in ways.items():
        use=w['tags'].get('landuse')
        if use not in colors:continue
        pts=clip_ring(w['points'])
        if len(pts)>2:polygon('parcel_osm_'+wid,pts,.007,colors[use],group=NG)
    for survey in SURVEYS:
        for f in survey['surfaces']:
            if f['kind'] in ('road','railway-corridor','vegetated-strip'):continue
            pts=clip_ring(f['footprint'])
            if len(pts)<3:continue
            polygon('parcel_trace_'+f['id'],pts,.012,f['color'],base=.008,group=IG)
            if f['kind'] in ('farmland','cropland','covered-crop-rows'):
                # Crop rows are decorative within the observed parcel, never buildings.
                xmin,xmax=min(p[0] for p in pts),max(p[0] for p in pts)
                zmin,zmax=min(p[1] for p in pts),max(p[1] for p in pts)
                for z in range(math.ceil(zmin/3)*3,math.floor(zmax),3):
                    crossings=[]
                    for a,b in zip(pts,pts[1:]+pts[:1]):
                        if (a[1]>z)!=(b[1]>z):crossings.append(a[0]+(z-a[1])*(b[0]-a[0])/(b[1]-a[1]))
                    crossings.sort()
                    for i in range(0,len(crossings)-1,2):
                        segment('crop-row_'+f['id'],[crossings[i],z],[crossings[i+1],z],.12,.01,'#879665',base=.022,group=IG)
            if f['kind']=='woodland':
                xmin,xmax=min(p[0] for p in pts),max(p[0] for p in pts)
                zmin,zmax=min(p[1] for p in pts),max(p[1] for p in pts)
                for x in range(math.ceil(xmin),math.floor(xmax),8):
                    for z in range(math.ceil(zmin),math.floor(zmax),8):
                        if inside([x,z],pts):tree(x,z,1.4+((x+z)%5)*.09,'woodland_'+str(x)+'_'+str(z))

def roof_frame(pts):
    a,b=max(zip(pts,pts[1:]+pts[:1]),key=lambda e:math.dist(*e))
    d=math.dist(a,b); ux,uz=(b[0]-a[0])/d,(b[1]-a[1])/d
    vx,vz=-uz,ux
    us=[x*ux+z*uz for x,z in pts]; vs=[x*vx+z*vz for x,z in pts]
    cu,cv=(min(us)+max(us))/2,(min(vs)+max(vs))/2
    return (cu*ux+cv*vx,cu*uz+cv*vz,ux,uz,vx,vz,max(us)-min(us),max(vs)-min(vs))

def make_roof(name,pts,h,color,style,group):
    cx,cz,ux,uz,vx,vz,w,d=roof_frame(pts)
    if style=='flat' or len(pts)>6:
        polygon(name,pts,.18,color,base=h,group=group)
        for a,b in zip(pts,pts[1:]+pts[:1]):segment(name+'_parapet',a,b,.16,.38,'#d1cdc0',base=h,group=group)
        return
    w+=.8; d+=.8
    rise=2.5 if name=='neighborhood_roof_605798599' else min(3.5,max(1,d*.22))
    hip=min(w*.22,d*.55) if style in ('hipped','hip') else 0
    local=[(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),(-w/2+hip,0,rise),(w/2-hip,0,rise)]
    verts=[bp(cx+ux*u+vx*v,h+y,cz+uz*u+vz*v) for u,v,y in local]
    mesh_object(name,verts,[(4,5,1,0),(5,4,3,2),(4,0,3),(5,2,1)],color,group)
    for side in (-1,1):segment(name+'_eave',[cx-ux*w/2+vx*d/2*side,cz-uz*w/2+vz*d/2*side],[cx+ux*w/2+vx*d/2*side,cz+uz*w/2+vz*d/2*side],.18,.16,'#e3e0d6',base=h-.08,group=group)
    segment(name+'_ridge',[cx+ux*(-w/2+hip),cz+uz*(-w/2+hip)],[cx+ux*(w/2-hip),cz+uz*(w/2-hip)],.18,.12,color,base=h+rise,group=group)

def neighborhood_windows(name,pts,height,floors,group):
    # Regular fenestration is explicitly estimated, not inferred from roof pixels.
    signed=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))
    for ei,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
        length=math.dist(a,b)
        if length<3:continue
        ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length
        nx,nz=(uz,-ux) if signed>0 else (-uz,ux)
        angle=math.atan2(-uz,ux); bays=max(1,int(length/(4.0 if floors>2 else 5.8)))
        for floor in range(floors):
            yy=height/floors*(floor+.51)
            for j in range(bays):
                t=(j+.5)/bays; x,z=a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])
                width=min(2.1,length/bays-1.1); wh=min(1.6,height/floors*.51)
                box(name+f'_frame_{ei}_{floor}_{j}',x+nx*.035,yy,z+nz*.035,width+.14,wh+.14,.10,'#e7e4d9',rotation=angle,group=group)
                box(name+f'_glass_{ei}_{floor}_{j}',x+nx*.10,yy,z+nz*.10,width,wh,.025,'#516a72',rotation=angle,group=group)
                box(name+'_mullion',x+nx*.125,yy,z+nz*.125,.055,wh,.025,'#d8ded8',rotation=angle,group=group)

def tube(name,a,b,radius,color,group=RG):
    av,bv=Vector(bp(*a)),Vector(bp(*b)); direction=bv-av
    # Local geometry, unlike the main cylinder helper, supports arbitrary direction.
    n=8; verts=[(radius*math.cos(i*2*math.pi/n),radius*math.sin(i*2*math.pi/n),z) for z in (-direction.length/2,direction.length/2) for i in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    o=mesh_object(name,verts,faces,color,group);o.location=(av+bv)/2;o.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    return o

def station_details(pts):
    # Front edge faces north, towards Dasi-ro. Address 218 and facade from 2014 photo.
    a,b=pts[0],pts[3]; length=math.dist(a,b);ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length;nx,nz=uz,-ux
    cx,cz=(a[0]+b[0])/2,(a[1]+b[1])/2;theta=math.atan2(-uz,ux)
    def pt(u,offset):return [cx+ux*u+nx*offset,cz+uz*u+nz*offset]
    def front_box(name,u,y,off,w,h,d,color):
        # On the north facade, photo-right is west in world coordinates.
        x,z=pt(-u,off);return box(name,x,y,z,w,h,d,color,rotation=theta,group=NG)
    # Deliberately patterned after the photo, not generic repeated school windows.
    front_box('station_white_eave',0,3.72,.50,length+1,.22,.95,'#e8e5d9')
    for u,w in [(-13,3.1),(4.6,7.7),(13,3.1)]:
        front_box('station_window_frame',u,2.0,.08,w+.16,1.85,.10,'#e3ddd0')
        front_box('station_window',u,2.0,.16,w,1.69,.05,'#516a70')
        for div in range(1,max(2,int(w/.8))):front_box('station_window_divider',u-w/2+div*w/max(2,int(w/.8)),2,.20,.04,1.7,.03,'#d2d8d5')
    front_box('station_entry_surround',-4.2,1.55,.17,7.8,2.85,.23,'#d9d7cc')
    front_box('station_entry_glass',-4.2,1.52,.31,7.5,2.64,.05,'#4b6064')
    for u in (-6.7,-4.2,-1.7):front_box('station_entry_mullion',u,1.52,.35,.065,2.64,.05,'#e0dfd3')
    front_box('station_entry_transom',-4.2,2.5,.37,7.5,.08,.05,'#e0dfd3')
    front_box('station_entrance_sign',-4.2,2.73,.4,3,.43,.06,'#164781')
    sx,sz=pt(4.2,.45);label('입구',sx,2.75,sz,2.2,theta+math.pi,'#ffffff',.27)
    for u in (-9,9):front_box('station_brick_pier',u,1.8,.15,.75,3.6,.4,'#884e3b')
    front_box('station_glass_block_frame',4.6,.63,.15,7.8,.9,.1,'#d1d6cf')
    for col in range(18):
        for row in range(3):front_box('station_glass_block',4.6-3.65+col*.43,.32+row*.29,.22,.39,.255,.055,('#708b8d','#869d9d','#637f84')[(col+row)%3])
    # Central projecting gable above the entrance.
    verts=[]
    for off in (.8,-2):
        for u,y in [(-8,3.8),(8,3.8),(0,6.8)]:
            x,z=pt(u,off);verts.append(bp(x,y,z))
    mesh_object('station_central_gable',verts,[(2,1,0),(4,5,3),(3,5,2,0),(5,4,1,2)],'#4c433d',NG)
    tri=[bp(*[pt(u,.82)[0],y,pt(u,.82)[1]]) for u,y in [(-7.4,3.9),(7.4,3.9),(0,6.5)]]
    mesh_object('station_gable_brick_face',tri,[(2,1,0)],'#884e3b',NG)
    for side in (-1,1):
        ribbon=[]
        for u,y in [(side*8,3.8),(0,6.8),(0,6.4),(side*7.0,3.8)]:
            xx,zz=pt(u,.9);ribbon.append(bp(xx,y,zz))
        mesh_object('station_gable_cream_trim',ribbon,[(3,2,1,0)] if side<0 else [(0,1,2,3)],'#eee5cb',NG)
    for u in (-2.2,2.2):front_box('station_sign_post',u,7.4,-.6,.12,2.6,.12,'#d9ded7')
    front_box('station_blue_nameboard',0,8.8,-.55,6.8,3.1,.16,'#184e9a')
    front_box('station_nameboard_white_strip',0,10.1,-.44,6.6,.4,.025,'#eceee9')
    sx,sz=pt(0,-.43)
    label('다시역',sx,8.95,sz,5.8,theta+math.pi,'#ffffff',1.02)
    label('Dasi Station',sx,7.85,sz,5.2,theta+math.pi,'#e9f3ff',.38)
    sx,sz=pt(0,-.40);label('KORAIL',sx,10.1,sz,2.5,theta+math.pi,'#184e9a',.27)
    front_box('station_address_plate',.15,2.3,.22,.40,.45,.04,'#174da1')
    sx,sz=pt(-.15,.26);label('218',sx,2.3,sz,.32,theta+math.pi,'#f4f0df',.17)
    for u in (-length/2+.2,length/2-.2):
        x,z=pt(u,.15);cylinder('station_downpipe',x,1.85,z,.07,3.7,'#3b4141',group=NG)
    # The station remains an exterior building; first-floor school is walkable.
    front_box('station_front_paving',0,.045,5,length+8,.06,8,'#babbae')

def build_railway():
    railways=[]
    for wid,w in ways.items():
        if w['tags'].get('railway')!='rail':continue
        for si,(a,b) in enumerate(zip(w['points'],w['points'][1:])):
            clipped=clip(a,b)
            if not clipped:continue
            a,b=clipped;ln=math.dist(a,b)
            if ln<.5:continue
            ux,uz=(b[0]-a[0])/ln,(b[1]-a[1])/ln;nx,nz=-uz,ux
            segment(f'rail-ballast_{wid}_{si}',a,b,3.6,.16,'#8b8579',base=.02,group=RG)
            for side in (-1,1):
                aa=[a[0]+nx*.7175*side,a[1]+nz*.7175*side];bb=[b[0]+nx*.7175*side,b[1]+nz*.7175*side]
                segment(f'rail_{wid}_{si}_{side}',aa,bb,.075,.11,'#69716d',base=.25,group=RG)
                segment('railhead',aa,bb,.06,.025,'#bfc4c1',base=.36,group=RG)
            for j in range(int(ln/.75)+1):
                t=j/max(1,int(ln/.75));x,z=a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t
                segment('rail_sleeper',[x-nx*1.15,z-nz*1.15],[x+nx*1.15,z+nz*1.15],.20,.13,'#b0ada1',base=.16,group=RG)
            tube('rail_contact_wire',(a[0],5.6,a[1]),(b[0],5.6,b[1]),.017,'#515a56')
            railways.append(dict(osm_id=wid,points=[a,b],gauge=1.435))
    for wid in ('1147618305','1147618306'):
        pts=clip_ring(ways[wid]['points'])
        polygon('walk-floor_platform_'+wid,pts,.43,'#bdbbad',base=.035,group=RG)
        for ei,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
            if math.dist(a,b)>20:
                segment('platform_yellow_safety_'+wid,a,b,.30,.02,'#d5b950',base=.47,group=RG)
        a,b=max(zip(pts,pts[1:]+pts[:1]),key=lambda e:math.dist(*e));ux,uz=(b[0]-a[0])/math.dist(a,b),(b[1]-a[1])/math.dist(a,b)
        for j in range(1,8):
            x,z=a[0]+(b[0]-a[0])*j/8,a[1]+(b[1]-a[1])*j/8
            cylinder('platform_light',x,2.8,z,.07,4.7,'#d7d4bd',group=RG)
            box('platform_lamp',x,5.1,z,1,.10,.32,'#e6e1bd',group=RG)
    # Positions along the mapped centreline; mast spacing is estimated from photo.
    a,b=ways['561612864']['points'][0],ways['561612864']['points'][-1];ln=math.dist(a,b);ux,uz=(b[0]-a[0])/ln,(b[1]-a[1])/ln;nx,nz=-uz,ux
    for j in range(11):
        x=a[0]+ux*(j*42-170);z=a[1]+uz*(j*42-170)
        if not(bounds[0]+5<x<bounds[1]-5):continue
        for side in (-1,1):
            px,pz=x+nx*8*side,z+nz*8*side
            tube('catenary_mast',(px,.2,pz),(px,8,pz),.12,'#737b76')
        tube('catenary_crossbeam',(x-nx*8,7.8,z-nz*8),(x+nx*8,7.8,z+nz*8),.10,'#737b76')
        tube('catenary_crossbeam_top',(x-nx*8,8.3,z-nz*8),(x+nx*8,8.3,z+nz*8),.07,'#737b76')
        for k in range(8):
            off=-8+k*2;tube('catenary_lattice',(x+nx*off,7.8,z+nz*off),(x+nx*(off+2),8.3,z+nz*(off+2)),.035,'#737b76')
    return railways

def build_neighborhood():
    relocate_school_gate()
    mapped={wid:w for wid,w in ways.items() if w['tags'].get('building') and wid not in ('963585634','963585635') and len(clip_ring(w['points']))>2}
    observations=[f for survey in SURVEYS for f in survey['features'] if f['kind']=='building']
    matches={}; omitted=[]; added=[]
    for f in observations:
        candidates=[wid for wid,w in mapped.items() if overlap(f['footprint'],open_ring(w['points']))]
        if candidates:
            wid=min(candidates,key=lambda wid:math.dist(center(f['footprint']),center(open_ring(mapped[wid]['points']))))
            # Tiny corner overlaps may be offset roof silhouettes, not identity matches.
            related=inside(center(f['footprint']),open_ring(mapped[wid]['points'])) or inside(center(open_ring(mapped[wid]['points'])),f['footprint'])
            if related:matches.setdefault(wid,[]).append(f)
            omitted.append(dict(trace=f['id'],reason='Mapped footprint takes precedence' if related else 'Ambiguous partial overlap; silhouette excluded',osm_id=wid))
        elif overlap(f['footprint'],open_ring(campus)):
            omitted.append(dict(trace=f['id'],reason='School envelope excluded'))
        elif any(overlap(f['footprint'],g['footprint']) for g in added):
            omitted.append(dict(trace=f['id'],reason='Overlapping aerial silhouette omitted'))
        else:added.append(f)
    # Floor counts are independently address-matched. Metre heights still assumed.
    floors_known={'963585625':(10,'https://kbland.kr/se/c/426959'),'963585637':(5,'https://kbland.kr/se/c/554475'),'963585641':(4,'https://zippoom.com/부동산/전남-나주시-다시면-남도아파트/p1mcqu')}
    for wid,w in mapped.items():
        pts=open_ring(w['points']);tags=w['tags'];f=matches.get(wid,[{}])[0]
        station=wid=='605798599';apart='아파트' in tags.get('name','')
        floors=floors_known.get(wid,(4 if apart else 1,None))[0]
        height=3.8 if station else floors*2.9+.4
        if not station and not apart:height=max(3.4,f.get('height',3.8))
        wall='#884e3b' if station else '#d5d0bc' if apart else '#c9c7b8'
        roof='#4c433d' if station else f.get('roofColor','#9b9c91')
        style='hipped' if station else 'flat' if apart else f.get('roofType','flat')
        polygon('osm-building_'+wid,pts,height,wall,True,group=NG)
        make_roof('neighborhood_roof_'+wid,pts,height,roof,style,NG)
        if station:station_details(pts)
        else:neighborhood_windows('neighborhood_window_'+wid,pts,height,floors,NG)
        buildings.append(dict(osm_id=wid,name=tags.get('name','다시역' if station else '지도 건물 '+wid),footprint=pts,height=height,height_source='Estimated metres; no surveyed height',floors=floors,floors_source=floors_known.get(wid,(None,'Unverified model estimate'))[1],roof_color_source=f.get('id','2014 station photo' if station else 'Unverified neutral material'),source='OpenStreetMap',trace_matches=[item['id'] for item in matches.get(wid,[])]))
    for f in added:
        pts=clip_ring(f['footprint'])
        if len(pts)<3:continue
        h=f['height'];name='photo-building_trace_'+f['id']
        polygon(name,pts,h,'#d1cfbf',True,group=IG)
        make_roof('trace_roof_'+f['id'],pts,h,f['roofColor'],f['roofType'],IG)
        neighborhood_windows('trace_window_'+f['id'],pts,h,1,IG)
        buildings.append(dict(trace_id=f['id'],name=f.get('observation',f.get('notes','영상 관찰 건물')),footprint=pts,height=h,height_source=f['heightSource'],source='2022-10-14 Esri/Vantor imagery: manually observed roof silhouette',source_tile=f['sourceTile']))
    for survey in SURVEYS:
        for f in survey['features']:
            if f['kind']=='building':continue
            pts=clip_ring(f['footprint'])
            if len(pts)>2:polygon('crop-cover_'+f['id'],pts,.025,f.get('roofColor','#babeb9'),base=.025,group=IG)
    rails=build_railway()
    # Paint follows OSM centreline; widths and exact mark placement are estimates.
    for wid in ('591007053','233475079','1216271144'):
        w=ways[wid]
        for a,b in zip(w['points'],w['points'][1:]):
            clipped=clip(a,b)
            if not clipped:continue
            a,b=clipped;ln=math.dist(a,b)
            if ln<1:continue
            segment('road_center_yellow',a,b,.12,.007,'#dbba58',base=.048,group=NG)
    # Utilities follow the actual roadside; pole spacing and wire sag are illustrative.
    road=ways['591007053']['points'];previous=None
    for a,b in zip(road,road[1:]):
        ln=math.dist(a,b);nx,nz=-(b[1]-a[1])/ln,(b[0]-a[0])/ln
        for j in range(max(1,int(ln/35))):
            t=j/max(1,int(ln/35));x,z=a[0]+(b[0]-a[0])*t+nx*5,a[1]+(b[1]-a[1])*t+nz*5
            if not(bounds[0]<x<bounds[1] and bounds[2]<z<bounds[3]):continue
            cylinder('road_utility_pole',x,4,z,.14,8,'#a6a698',group=NG)
            if previous:
                for offset in (-.35,.35):
                    last=(previous[0]+offset,7.6,previous[1])
                    for k in range(1,9):
                        t=k/8;nextp=(previous[0]+(x-previous[0])*t+offset,7.6-math.sin(t*math.pi)*.65,previous[1]+(z-previous[1])*t)
                        tube('road_overhead_wire',last,nextp,.024,'#555c54',NG);last=nextp
            previous=(x,z)
    return dict(extent_metres=[570,440],imagery_date='2022-10-14',source_accuracy_metres=5,mapped_buildings=len(mapped),added_roof_traces=len(added),omitted_traces=omitted,railways=rails,school_gate=neighborhood_gate,places=[
        dict(id='dasi-station',name='다시역 앞',position=[100,78],radius=13,description='사진에 보이는 벽돌 역사와 파란 역명판을 찾아보세요. 외관은 2014년 사진을 참고했습니다.'),
        dict(id='dasi-road',name='다시로',position=[-34,50],radius=17,description='학교 앞에서 다시역 방향으로 이어지는 실제 도로입니다.'),
        dict(id='daeyong-road',name='대용길',position=[-164,-18],radius=18,description='학교 서쪽 주택가와 아파트 사이로 이어지는 길입니다.'),
        dict(id='east-fields',name='학교 동쪽 들판',position=[164,-70],radius=42,description='위성영상에서 확인한 논과 재배시설을 표현했습니다.'),
        dict(id='station-platform',name='다시역 승강장',position=[153,119],radius=70,footprint=open_ring(ways['1147618306']['points']),description='지도 좌표에 따라 놓은 승강장과 호남선 철로입니다.')
    ],limitations=[
        'Neighborhood covers 570 x 440 m. Mapped building footprints take precedence over manually traced roof silhouettes; duplicate traces are recorded.',
        'The satellite image date is 2022-10-14 with approximately 5 m source accuracy; hidden and low-contrast structures may be omitted. This is not a complete current survey or photogrammetric reconstruction.',
        'Top Class apartment 10 floors, Jungang/Taeheung 5 floors and Namdo 4 floors are address-matched public listings. Their metre heights and all other neighborhood heights/window layouts are estimates.',
        'Dasi station facade uses a photograph dated 2014-06-16; present-day condition is unverified. Railway alignments/platform outlines use OSM, gauge 1.435 m; rail elevation, catenary mast positions and utility poles are estimates.',
        'Terrain remains flat; no measured elevation data. Road widths, parcel textures and individual vegetation are approximate. Agricultural covers are surfaces without building collisions.'
        ,'School gate is aligned with the intersection of mapped entrance service road 592336461 and campus boundary; the photo-derived pier geometry and opening width are estimates.'
    ])
