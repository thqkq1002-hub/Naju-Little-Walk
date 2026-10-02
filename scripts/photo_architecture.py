"""Photo-guided architecture helpers executed by build_city.py.
References: National Heritage Service and Academy of Korean Studies photographs.
Dimensions other than the OSM footprint remain estimates; interior is illustrative.
"""
import random

def round_post(name,x,z,height,base=0,radius=.19,color='#714534'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=height,location=blender_point(x,base+height/2,z))
    return finish(bpy.context.object,dict(name=name,kind='cylinder',position=[x,base+height/2,z],size=[radius*2,height,radius*2],color=color,collision=True),'02_Estimated_Architecture')

def curved_roof(name,front_start,front_end,depth,eave,rise):
    ux,uz=front_end[0]-front_start[0],front_end[1]-front_start[1]
    width=math.hypot(ux,uz); ux/=width; uz/=width
    vx,vz=uz,-ux; cx=(front_start[0]+front_end[0])/2+vx*depth/2; cz=(front_start[1]+front_end[1])/2+vz*depth/2
    width+=3.4; depth+=3.5
    nx=max(24,int(width/.18)); nz=28
    verts=[]
    for j in range(nz+1):
        t=j/nz*2-1; inset=depth*.15*(1-abs(t))
        for i in range(nx+1):
            s=i/nx*2-1; x=s*(width/2-inset); z=t*depth/2
            y=eave+rise*(1-abs(t))**1.7+.19*abs(t)**10+.22*abs(s)**8+.045*math.cos(i*math.pi)
            verts.append(blender_point(cx+ux*x+vx*z,y,cz+uz*x+vz*z))
    faces=[]
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i; faces.append((a,a+1,a+nx+2,a+nx+1))
    # Close the two hipped ends.
    for side in (0,nx):
        anchor=len(verts); sign=-1 if side==0 else 1
        verts.append(blender_point(cx+ux*sign*width/2,eave,cz+uz*sign*width/2))
        for j in range(nz):
            a=j*(nx+1)+side; b=(j+1)*(nx+1)+side
            faces.append((anchor,b,a) if side==0 else (anchor,a,b))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); scene.collection.objects.link(o)
    finish(o,dict(name=name,kind='roof',position=[cx,eave,cz],size=[width,rise,depth],color='#505753'),'02_Estimated_Architecture')
    for color in ('#48504d','#5c615a','#64695f'):mesh.materials.append(material(color))
    for i,p in enumerate(mesh.polygons):p.material_index=(i%nx//2*17)%4
    angle=math.atan2(-uz,ux)
    box(name+'_ridge',cx,eave+rise+.12,cz,width-depth*.3,.24,.27,'#424b47',False,angle)
    for t in (-1,1):
        a=[cx-ux*width/2+vx*t*depth/2,cz-uz*width/2+vz*t*depth/2]
        b=[cx+ux*width/2+vx*t*depth/2,cz+uz*width/2+vz*t*depth/2]
        segment(name+'_eave',a,b,.19,.2,'#39594b',False,eave-.15)

def photo_tree(x,z,height=13,radius=5,pine=False):
    round_post('photo-tree_trunk',x,z,height*.6,radius=.36,color='#625444')
    rng=random.Random(round(x*117+z*91))
    for i in range(7):
        a=i*2.4; r=radius*(.45 if i else 0)
        px=x+math.cos(a)*r; pz=z+math.sin(a)*r
        py=height*(.65+.045*i)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=radius*.67,location=blender_point(px,py,pz))
        o=bpy.context.object; o.scale=(1,1,.7 if pine else .9)
        finish(o,dict(name='photo-tree_foliage',kind='sphere',position=[px,py,pz],size=[radius*1.34]*3,color=rng.choice(['#365346','#426245','#526c45'] if pine else ['#637e4a','#728956','#4e7348','#829157'])),'02_Estimated_Architecture')

def photo_hall(w):
    pts=w['points'][:-1]
    a,b=pts[1],pts[2]
    length=math.dist(a,b); ux,uz=(b[0]-a[0])/length,(b[1]-a[1])/length; vx,vz=uz,-ux
    angle=math.atan2(-uz,ux)
    def at(t,d=0):return [a[0]+ux*t+vx*d,a[1]+uz*t+vz*d]
    def projection(p):return (p[0]-a[0])*ux+(p[1]-a[1])*uz
    left,right=sorted([projection(pts[7]),projection(pts[4])])
    center=(left+right)/2
    depth=math.dist(pts[0],pts[1]); rear_depth=depth+math.dist(pts[4],pts[5])
    entry=at(center)
    polygon('ground_floor_hall',pts,.58,'#b6afa0')
    central=[at(left),at(right),at(right,rear_depth),at(left,rear_depth)]
    polygon('ground_floor_central',central,.94,'#c3bca9')
    # Three distinct roof volumes, with the central Jeongcheong highest.
    curved_roof('roof_832423358',at(left),at(right),rear_depth,6.7,3.4)
    curved_roof('roof_west_wing',at(0),at(left),depth,4.5,2.4)
    curved_roof('roof_east_wing',at(right),at(length),depth,4.9,2.6)
    # Closed center, five bays. The middle opening is an explicit exploration adaptation.
    walltop=6.25
    for side_start,side_end in ((left,center-2.05),(center+2.05,right)):
        segment('hall-wall_front',at(side_start),at(side_end),.34,walltop-.94,'#d7c6a2',True,.94)
    segment('hall-wall_back',at(left,rear_depth),at(right,rear_depth),.36,walltop-.94,'#d7c6a2',True,.94)
    for t in (left,right):segment('hall-wall_side',at(t),at(t,rear_depth),.36,walltop-.94,'#d7c6a2',True,.94)
    segment('hall-wall_lintel',at(center-2.05),at(center+2.05),.4,2.1,'#526954',False,4.15)
    for i in range(6):
        t=left+(right-left)*i/5
        for d in (-.35,rear_depth-.2):
            p=at(t,d); round_post('hall-column',*p,5.42,.9,.22,'#743d30')
    # A dense green timber lattice, following the photographed color and bay rhythm.
    for i in (0,1,3,4):
        t=left+(right-left)*(i+.5)/5; p=at(t,-.25); bw=(right-left)/5-.65
        box('hall-window_paper',p[0],3.25,p[1],bw,3.35,.09,'#aaa997',False,angle)
        for q in range(12):
            pt=at(t-bw/2+bw*q/11,-.33)
            box('hall-window_lattice',pt[0],3.25,pt[1],.042,3.35,.05,'#496852',False,angle)
        for q in range(10):
            box('hall-window_lattice',p[0],1.62+q*.36,p[1]+.015,bw,.042,.1,'#496852',False,angle)
        box('hall-window_frame',p[0],1.52,p[1],bw,.17,.15,'#345944',False,angle)
        box('hall-window_frame',p[0],5.0,p[1],bw,.17,.15,'#345944',False,angle)
    for d in (-.45,rear_depth):
        segment('dancheong_green',at(left,d),at(right,d),.55,.32,'#3c7661',False,5.85)
        segment('dancheong_ochre',at(left,d),at(right,d),.58,.10,'#bd9749',False,6.18)
        segment('dancheong_red',at(left,d),at(right,d),.56,.10,'#8d4935',False,6.3)
    for i in range(21):
        p=at(left+(right-left)*i/20,-.55)
        box('dancheong_bracket',p[0],6.38,p[1],.35,.3,1.1,'#446d57',False,angle)
    # The wings have open front verandas and partial rear rooms.
    for lo,hi,h in ((0,left,4.5),(right,length,4.9)):
        for j in range(max(2,round((hi-lo)/3.2))+1):
            t=lo+(hi-lo)*j/max(2,round((hi-lo)/3.2))
            for d in (.25,depth-.25):
                p=at(t,d); round_post('wing-column',*p,h-.58,.58,.18,'#76503a')
        segment('wing-beam',at(lo),at(hi),.4,.32,'#81543a',False,h-.25)
        segment('hall-wall_wing-back',at(lo,depth),at(hi,depth),.3,h-.58,'#d9d1b6',True,.58)
        rlo=lo+(hi-lo)*.27; rhi=lo+(hi-lo)*.72
        segment('hall-wall_wing-room',at(rlo,depth*.55),at(rhi,depth*.55),.26,h-.58,'#d3c8ac',True,.58)
        for j in range(3):
            p=at(rlo+(rhi-rlo)*(j+.5)/3,depth*.55-.18)
            box('wing-window',p[0],2.35,p[1],(rhi-rlo)/3-.25,2.3,.08,'#68806a',False,angle)
    # Broad raised stone terrace and shallow stairs, as seen in the official photo.
    terrace_center=at(center,-1.1)
    box('walk-floor_terrace',terrace_center[0],.36,terrace_center[1],(right-left)*.65,.72,2.5,'#bdb6a5',False,angle)
    for n in range(5):
        p=at(center,-3.15+n*.53)
        box('walk-floor_step',p[0],(.15+n*.158)/2,p[1],5.0,.15+n*.158,.58,'#c3bcac',False,angle)
    p=at(center,-.62)
    box('hall_nameboard',p[0],5.6,p[1],4.1,.95,.19,'#34453a',False,angle)
    q=at(center,-.75); label('館 城 錦',q[0],5.6,q[1],3.6,angle)
    # Fictional interior display is clearly labelled in the app and the model.
    interior=at(center,4.7)
    panel=at(center,7.0)
    box('interior_panel',panel[0],2.4,panel[1],5,2.5,.25,'#38554b',True,angle,'03_Illustrative_Interior')
    textp=at(center,6.81)
    label('나주, 시간을 걷다',textp[0],2.7,textp[1],4.4,angle)
    label('실내 탐험용 가상 전시',textp[0],1.9,textp[1],4.0,angle,'#c5d0b4')
    for offset in (-4,4):
        p=at(center+offset,4.5)
        box('interior_plinth',p[0],1.3,p[1],1.2,.72,1.2,'#b8ac8e',True,angle,'03_Illustrative_Interior')
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.4,location=blender_point(p[0],1.95,p[1]))
        finish(bpy.context.object,dict(name='interior_art',kind='sphere',position=[p[0],1.95,p[1]],size=[.8,.8,.8],color='#628b77'),'03_Illustrative_Interior')
    # Photo-guided trees: approximate placement, not surveyed coordinates.
    for t,d,h,r in ((-5,3,17,6),(left-4,rear_depth+6,15,5.5),(center,rear_depth+10,17,6.5),(right+5,rear_depth+7,16,5.6),(length+5,depth+2,12,4.5)):
        p=at(t,d); photo_tree(*p,h,r,t<0)
    # Natural stone walkway shown in the heritage photograph, modeled as one mesh.
    rng=random.Random(32); vertices=[]; faces=[]
    for row in range(70):
        for col in range(8):
            t=center-2.8+(col+.5)*.7+rng.uniform(-.11,.11); d=-4.0-row*.75
            p=at(t,d); base=len(vertices)
            for k in range(6):
                a2=k*math.pi/3; sx=math.cos(a2)*rng.uniform(.29,.4); sz=math.sin(a2)*rng.uniform(.3,.43)
                vertices.append(blender_point(p[0]+ux*sx+vx*sz,.055+rng.uniform(0,.025),p[1]+uz*sx+vz*sz))
            faces.append(tuple(range(base,base+6)))
    mesh=bpy.data.meshes.new('photo_stone_walkway'); mesh.from_pydata(vertices,[],faces); mesh.update()
    o=bpy.data.objects.new('photo_stone_walkway',mesh); groups['02_Estimated_Architecture'].objects.link(o)
    for c in ('#b7ae96','#c6b797','#a5a28e','#cebf9f'):mesh.materials.append(material(c))
    for p in mesh.polygons:p.material_index=rng.randrange(4)
    for side in (-3.1,3.1):segment('path-edging',at(center+side,-4),at(center+side,-56),.16,.16,'#b7b098',False)
    places.insert(0,dict(id='interior',name='금성관 실내 체험',position=interior,radius=5,description='공식 사진을 참고한 외관과 탐험용 가상 실내입니다.'))
    places.insert(1,dict(id='hall',name='금성관 앞마당',position=at(center,-12),radius=24,description='박석길을 따라 계단을 올라, 가운데 출입구로 들어가 보세요.'))
    return entry
