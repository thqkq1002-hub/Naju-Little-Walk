"""Photo/video-informed details for Geumseonggwan, executed by build_city.py.

Map roof outlines are retained. Unmeasured joinery, material patterns and open-door
positions are interpretive modeling, not survey data or copied image textures.
"""
import bmesh
import random

DETAIL_GROUP='02_Estimated_Architecture'

class HeritageFrame:
    def __init__(self,origin,u):
        self.origin=origin;self.u=u;self.v=(u[1],-u[0])
    def point(self,x,z):
        return [self.origin[0]+self.u[0]*x+self.v[0]*z,self.origin[1]+self.u[1]*x+self.v[1]*z]
    def xyz(self,p):
        x,z=self.point(p[0],p[2]);return blender_point(x,p[1],z)
    def mesh(self,name,verts,faces,color,smooth=False):
        m=bpy.data.meshes.new(name);m.from_pydata([self.xyz(p) for p in verts],[],faces);m.update()
        bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
        o=bpy.data.objects.new(name,m);groups[DETAIL_GROUP].objects.link(o);m.materials.append(material(color))
        for p in m.polygons:p.use_smooth=smooth
        o['source_class']='Photo/video-informed detail; unmeasured dimensions'
        return o
    def box(self,name,x,y,z,w,h,d,color,collision=False,rotation=0):
        c,s=math.cos(rotation),math.sin(rotation)
        pts=[(x+dx*c-dz*s,z+dx*s+dz*c) for dx,dz in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
        o=self.mesh(name,[(px,yy,pz) for yy in (y-h/2,y+h/2) for px,pz in pts],[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],color)
        if collision or name.startswith(('ground_floor','walk-floor')):
            solids.append(dict(name=name,kind='building',position=[0,y-h/2,0],size=[w,h,d],footprint=[self.point(*p) for p in pts],color=color,collision=collision))
        return o
    def tube(self,name,a,b,r,color,n=12,collision=False):
        p,q=Vector(a),Vector(b);axis=(q-p).normalized();u=axis.cross(Vector((0,1,0)))
        if u.length<.001:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u).normalized()
        verts=[tuple(c+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for c in (p,q) for i in range(n)]
        o=self.mesh(name,verts,[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],color,True)
        if collision:
            wx,wz=self.point(a[0],a[2]);solids.append(dict(name=name,kind='cylinder',position=[wx,(a[1]+b[1])/2,wz],size=[r*2,abs(b[1]-a[1]),r*2],color=color,collision=True))
        return o
    def post(self,name,x,z,base,h,r=.23,color='#754235'):
        self.box(name+'_stone',x,base-.10,z,r*2.7,.20,r*2.7,'#aaa69a')
        return self.tube(name,(x,base,z),(x,base+h,z),r,color,16,True)
    def text(self,name,text,x,y,z,width,height=.6,color='#efe5c9',rotation=0):
        curve=bpy.data.curves.new(name,'FONT');curve.body=text;curve.align_x='CENTER';curve.align_y='CENTER';curve.size=1;curve.extrude=.0015
        if font:curve.font=font
        o=bpy.data.objects.new(name,curve);groups[DETAIL_GROUP].objects.link(o);o.location=self.xyz((x,y,z))
        angle=math.atan2(-self.u[1],self.u[0])+rotation;o.rotation_euler=(math.pi/2,0,angle);curve.materials.append(material(color));bpy.context.view_layer.update()
        ww=max(v[0] for v in o.bound_box)-min(v[0] for v in o.bound_box);hh=max(v[1] for v in o.bound_box)-min(v[1] for v in o.bound_box);scale=min(width/max(ww,.01),height/max(hh,.01));o.scale=(scale,scale,scale)
        wx,wz=self.point(x,z);signs.append(dict(text=text,position=[wx,y,wz],width=width,height=height,rotation=angle,color=color))
        return o

def detailed_roof(f,name,cx,cz,width,depth,eave,rise,paljak=True):
    """Two curved tiled slopes plus hip skirts and visible upper gables."""
    rng=random.Random(name);half=depth/2;hip=depth*.13 if paljak else 0
    colors=['#4a4e4d','#505451','#585a55','#606159','#454b48']
    def shape(t,x):
        return eave+rise*t**1.35+.16*(1-t)**10+.28*abs(x/(width/2))**10
    for side in (-1,1):
        nx=max(24,int(width/.16));nz=28;verts=[];faces=[]
        for j in range(nz+1):
            t=j/nz;span=width/2-hip*min(t/.58,1)
            for i in range(nx+1):
                x=-span+2*span*i/nx;z=side*half*(1-t)
                y=shape(t,x)+.034*math.cos(i*math.pi)
                verts.append((cx+x,y,cz+z))
        for j in range(nz):
            for i in range(nx):
                a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
        o=f.mesh(name if side==-1 else name+'_back',verts,faces,colors[0],True)
        for c in colors[1:]:o.data.materials.append(material(c))
        for j,p in enumerate(o.data.polygons):p.material_index=rng.randrange(len(colors)) if j%nx%2==0 else 0
        # Curved eave fascia, two rows of exposed rafters and round tile ends.
        for i in range(nx//2+1):
            x=-width/2+width*i/(nx//2);y=shape(0,x)
            f.tube(name+'_tile_end',(cx+x,y-.01,cz+side*half),(cx+x,y-.01,cz+side*(half+.075)),.075,'#626052',10)
            f.tube(name+'_lower_rafter',(cx+x,eave-.44,cz+side*(half-.9)),(cx+x,y-.25,cz+side*(half+.05)),.073,'#45715b',10)
            f.tube(name+'_upper_rafter',(cx+x,eave-.19,cz+side*(half-.7)),(cx+x,y-.07,cz+side*(half+.02)),.055,'#486c56',10)
        for k in range(32):
            xa=-width/2+width*k/32;xb=-width/2+width*(k+1)/32
            f.tube(name+'_eave_fascia',(cx+xa,shape(0,xa)-.19,cz+side*half),(cx+xb,shape(0,xb)-.19,cz+side*half),.11,'#466653')
        # Horizontal overlaps indicate courses without redistributing photo textures.
        for j in range(1,17):
            t=j/17;span=width/2-hip*min(t/.58,1)
            vv=[]
            for k in range(41):
                x=-span+2*span*k/40
                for dz in (0,.024):vv.append((cx+x,shape(t,x)+.015,cz+side*half*(1-t)+dz))
            f.mesh(name+'_tile_course',vv,[(k*2,k*2+1,k*2+3,k*2+2) for k in range(40)],'#676963')
    if paljak:
        for side in (-1,1):
            verts=[];faces=[];nz=20;nt=12
            for j in range(nt+1):
                t=j/nt;span=half*(1-.58*t);x=side*(width/2-hip*t)
                for k in range(nz+1):
                    z=-span+2*span*k/nz;y=shape(.58*t,x)+.028*math.cos(k*math.pi)
                    verts.append((cx+x,y,cz+z))
            for j in range(nt):
                for k in range(nz):
                    a=j*(nz+1)+k;faces.append((a,a+1,a+nz+2,a+nz+1))
            f.mesh(name+'_hip',verts,faces,'#53554d',True)
            x=cx+side*(width/2-hip);base=shape(.58,side*(width/2-hip))
            f.mesh(name+'_upper_gable',[(x,base,cz-half*.42),(x,eave+rise,cz),(x,base,cz+half*.42)],[(0,1,2)],'#9a5d3b')
            for k in range(23):
                z=-half*.4+half*.8*k/22;top=eave+rise-(eave+rise-base)*abs(z)/(half*.42)
                if top>base:f.tube(name+'_gable_board',(x+side*.02,base,cz+z),(x+side*.02,top,cz+z),.035,'#563d2c',8)
    else:
        for side in (-1,1):
            x=cx+side*width/2
            f.mesh(name+'_gable',[(x,eave,cz-half),(x,eave+rise,cz),(x,eave,cz+half)],[(0,1,2)],'#a77549')
    ridge=width-2*hip
    for k in range(40):
        xa=-ridge/2+ridge*k/40;xb=-ridge/2+ridge*(k+1)/40
        yy=lambda x:eave+rise+.17+.27*abs(x/(ridge/2))**10
        f.tube(name+'_ridge',(cx+xa,yy(xa),cz),(cx+xb,yy(xb),cz),.15,'#4a4c43',12)
    for side in (-1,1):
        f.tube(name+'_ridge_finial',(cx+side*ridge/2,eave+rise+.35,cz),(cx+side*(ridge/2+.10),eave+rise+.75,cz),.10,'#686355',12)

def bracket(f,name,x,z,y,axis=0):
    # Three layered timber arms; ornament colors follow photos, exact carving inferred.
    for k in range(3):
        f.box(name+'_arm',x,y+k*.16,z,.32+k*.18,.13,1.15+k*.24,['#326b59','#548a71','#8c4b39'][k],rotation=axis)
    f.box(name+'_capital',x,y-.12,z,.54,.25,.56,'#84513b')
    for dx in (-.20,.20):f.box(name+'_ochre',x+dx,y+.25,z-.72,.06,.18,.035,'#c39a55')

def lattice_door(f,name,x,z,width,bottom,top,opened=0,paper='#bbb9a2'):
    """An individually framed leaf with solid lower panel and diamond lattice."""
    # Leaves are local X/Y planes. Rotate all their points around a vertical hinge.
    ca,sa=math.cos(opened),math.sin(opened)
    def b(label,xx,y,zz,w,h,d,color):
        px=x+(xx-x)*ca-(zz-z)*sa;pz=z+(xx-x)*sa+(zz-z)*ca
        return f.box(name+label,px,y,pz,w,h,d,color,rotation=opened)
    h=top-bottom;panelh=h*.20
    b('_paper',x,bottom+panelh+(h-panelh)/2,z,width-.09,h-panelh-.12,.045,paper)
    b('_bottom_panel',x,bottom+panelh/2,z,width,.97*panelh,.11,'#487564')
    for xx in (x-width/2,x+width/2):b('_stile',xx,(bottom+top)/2,z-.06,.065,h,.10,'#724c37')
    for y in (bottom,bottom+panelh,top):b('_rail',x,y,z-.07,width,.065,.12,'#684b37')
    # A clipped diamond lattice across the light upper paper panel.
    xmin,xmax=x-width/2+.06,x+width/2-.06;ymin=bottom+panelh+.06;ymax=top-.06
    for sign in (-1,1):
        intercept=ymin-(xmax-xmin) if sign==1 else ymin
        while intercept<ymax+(xmax-xmin):
            ends=[]
            for xx in (xmin,xmax):
                yy=intercept+sign*(xx-xmin)
                if ymin<=yy<=ymax:ends.append((xx,yy))
            for yy in (ymin,ymax):
                xx=xmin+(yy-intercept)/sign
                if xmin<xx<xmax:ends.append((xx,yy))
            if len(ends)>=2:
                a,c=ends[:2]
                def p(v):return (x+(v[0]-x)*ca+.075*sa,v[1],z+(v[0]-x)*sa-.075*ca)
                f.tube(name+'_diamond',p(a),p(c),.011,'#42624f',5)
            intercept+=.22

def ceiling_flower(f,x,y,z,size):
    verts=[];faces=[]
    for j in range(8):
        a=j*math.tau/8;base=len(verts)
        for k in range(16):
            t=k*math.tau/16;u=.23+.18*math.cos(t);v=.10*math.sin(t)
            verts.append((x+size*(u*math.cos(a)-v*math.sin(a)),y,z+size*(u*math.sin(a)+v*math.cos(a))))
        faces.append(tuple(range(base,base+16)))
    o=f.mesh('ceiling_original_lotus',verts,faces,'#bd8d61')
    for col in ('#b66951','#87977d','#c1b18a'):o.data.materials.append(material(col))
    for j,p in enumerate(o.data.polygons):p.material_index=j%4
    f.tube('ceiling_lotus_center',(x,y-.018,z),(x,y-.002,z),size*.09,'#b49754',16)

def photo_tree(x,z,height=13,radius=5,pine=False):
    f=HeritageFrame([x,z],(1,0));rng=random.Random(round(x*117+z*91))
    f.post('photo-tree_trunk',0,0,0,height*.56,.38,'#655a45')
    verts=[];faces=[]
    for j in range(10):
        a=j*2.40;r=radius*(.45 if j else .12)
        cx,cz=math.cos(a)*r,math.sin(a)*r;cy=height*(.62+j*.035)
        f.tube('tree_spreading_branch',(0,height*.36,0),(cx,cy,cz),.12,'#71604a',10)
        start=len(verts);n=24;levels=16
        for iy in range(levels+1):
            phi=math.pi*iy/levels
            for ix in range(n):
                theta=math.tau*ix/n;rr=radius*.55*rng.uniform(.95,1.05)
                verts.append((cx+rr*math.sin(phi)*math.cos(theta),cy+rr*.70*math.cos(phi),cz+rr*math.sin(phi)*math.sin(theta)))
        for iy in range(levels):
            for ix in range(n):
                a0=start+iy*n+ix;b0=start+iy*n+(ix+1)%n;faces.append((a0,b0,b0+n,a0+n))
    o=f.mesh('photo-tree_fine_foliage',verts,faces,'#526d38',True)
    for col in ('#58743b','#5e783e','#4e6837','#637d43'):o.data.materials.append(material(col))
    for p in o.data.polygons:p.material_index=rng.randrange(5)

def photo_hall(w):
    global hall_detail_frame,hall_detail_info
    pts=w['points'][:-1];a,b=pts[1],pts[2];length=math.dist(a,b)
    f=HeritageFrame(a,((b[0]-a[0])/length,(b[1]-a[1])/length));hall_detail_frame=f
    projection=lambda p:(p[0]-a[0])*f.u[0]+(p[1]-a[1])*f.u[1]
    roof_left,roof_right=sorted([projection(pts[7]),projection(pts[4])]);center=(roof_left+roof_right)/2
    # The mapped outline is interpreted as roof coverage. Column-grid dimensions
    # are estimated from photos and the public low-resolution plan, not measured.
    # Published area figures differ and are not used as an exact floor-area proof.
    width,depth=19.5,16.45;lo,hi=center-width/2,center+width/2;front=2.5;back=front+depth;bay=width/5
    columns=[lo+width*t for t in (0,.155,.385,.615,.845,1)]
    hall_detail_info=dict(center=center,front=front,back=back,lo=lo,hi=hi,columnGrid=[width,depth],roofOutline=[roof_right-roof_left,21.48],columns=columns)
    polygon('ground_floor_hall',pts,.58,'#b9b2a0')
    f.box('ground_floor_central',center,.47,(front+back)/2,width+1.6,.94,depth+1.5,'#bfb7a4')
    f.box('walk-floor_hall_maroo',center,.965,(front+back)/2,width-.22,.05,depth-.20,'#796343')
    detailed_roof(f,'roof_832423358',center,10.74,roof_right-roof_left,21.48,6.55,3.60,True)
    # The 2015 roof plan shows three separate hipped-and-gabled roof volumes.
    detailed_roof(f,'roof_west_wing',roof_left/2,7.4,roof_left,14.8,4.15,2.28,True)
    detailed_roof(f,'roof_east_wing',(roof_right+length)/2,7.35,length-roof_right,14.7,4.55,2.48,True)
    # Grid beams and planks form the photographed empty wooden floor.
    for i in range(6):f.box('maroo_cross_beam',lo+bay*i,.997,(front+back)/2,.11,.018,depth-.20,'#564730')
    for j in range(36):
        z=front+.10+(depth-.2)*j/35
        f.box('maroo_board_seam',center,.998,z,width-.24,.015,.014,'#534732')
    for x in columns:
        for z in (front,back):f.post('hall-column',x,z,.94,5.30,.25)
    for side in (lo,hi):
        for j in range(1,4):f.post('hall-side-column',side,front+depth*j/4,.94,5.30,.24)
    # Each bay has separate lower leaves, rails, and upper transom lights.
    for side,z in [('front',front),('back',back)]:
        for i in range(5):
            baywidth=columns[i+1]-columns[i];x=(columns[i]+columns[i+1])/2;bw=baywidth-.48;leaves=2 if i in (0,4) else 4
            opened=side=='front' and i==2
            if not opened:
                proxy=f.box('hall-wall_'+side,x,2.67,z,bw+.12,3.46,.15,'#bdbba7',True)
                bpy.data.objects.remove(proxy,do_unlink=True)
            for j in range(leaves):
                xx=x-bw/2+(j+.5)*bw/leaves;zz=z-.12 if side=='front' else z+.12
                angle=0
                if opened:
                    xx=x+(-1 if j<2 else 1)*(bw/2-.06);zz=z+.30+(j%2)*bw/leaves;angle=math.pi/2
                lattice_door(f,'hall_door_'+side+f'_{i}_{j}',xx,zz,bw/leaves-.045,1.22,4.15,angle)
                if not opened:
                    lattice_door(f,'hall_door_inside_'+side+f'_{i}_{j}',xx,z+(.15 if side=='front' else -.15),bw/leaves-.045,1.22,4.15,math.pi if side=='front' else 0)
            f.box('hall_front_sill',x,1.08,z,bw,.19,.22,'#7c6040')
            f.box('hall_transom_frame',x,4.42,z,bw,.16,.20,'#865538')
            for j in range(2):
                tx=x+(-.25 if j==0 else .25)*bw
                lattice_door(f,'hall_transom',tx,z-.10,bw/2-.07,4.52,5.36)
            for y,c,h in [(5.50,'#85633c',.16),(5.72,'#3c7764',.26),(5.92,'#b49554',.09),(6.09,'#814c37',.22)]:
                f.box('hall_painted_beam',x,y,z,baywidth,h,.34,c)
    # Side walls use the four-bay rhythm visible in the measured-plan thumbnail.
    for x in (lo,hi):
        proxy=f.box('hall-wall_side',x,3.05,(front+back)/2,.18,4.22,depth,'#d2c9ae',True)
        bpy.data.objects.remove(proxy,do_unlink=True)
        for j in range(4):
            z=front+depth*(j+.5)/4
            leaves=2 if j in (0,3) else 4;bw=depth/4-.45
            for k in range(leaves):
                zz=z-bw/2+(k+.5)*bw/leaves
                lattice_door(f,'hall_side_leaf',x+(-.13 if x==lo else .13),zz,bw/leaves-.055,1.22,4.34,math.pi/2)
                lattice_door(f,'hall_side_leaf_inside',x+(.13 if x==lo else -.13),zz,bw/leaves-.055,1.22,4.34,math.pi/2 if x==lo else -math.pi/2)
            for y in (1.22,4.34,5.34):f.box('hall_side_rail',x,y,z,.24,.13,depth/4,'#815039')
    for x in columns:
        for z in (front-.16,back+.16):bracket(f,'hall_ikgong',x,z,6.16)
    # A lower central bay is kept open for exploration; the original leaves remain.
    f.box('hall_nameboard',center,5.43,front-.63,4.5,1.12,.19,'#322b21')
    f.box('hall_nameboard_border',center,5.43,front-.75,4.3,.99,.03,'#504632')
    f.text('hall_name_readable','館 城 錦',center,5.43,front-.79,4.0,.76)
    # Two lines of inner tall columns and the coffered center ceiling are visible
    # in official 2017–2019 catalogue interior photographs, unlike the old display.
    inner_z=[front+depth*.25,front+depth*.75]
    core_width=columns[4]-columns[1];core_depth=inner_z[1]-inner_z[0]
    for x in columns[1:5]:
        for z in inner_z:f.post('hall_inner_tall_column',x,z,.99,6.65,.27)
        f.box('hall_ceiling_long_beam',x,7.10,(inner_z[0]+inner_z[1])/2,.30,.52,core_depth+.25,'#427762')
    for z in inner_z:
        for y,w,h,col in [(6.38,width,.44,'#467b68'),(6.69,width,.12,'#bf9459'),(6.88,width,.16,'#934b37')]:
            f.box('hall_ceiling_cross_beam',center,y,z,w,h,.32,col)
        for k in range(23):
            x=lo+.3+(width-.6)*k/22
            f.box('beam_original_ornament',x,6.40,z-.18,.42,.27,.014,'#b59255')
            f.box('beam_original_ornament_inset',x,6.40,z-.19,.25,.14,.012,'#548873')
    for i in range(12):
        for j in range(8):
            x=columns[1]+(i+.5)*core_width/12;z=inner_z[0]+(j+.5)*core_depth/8;y=7.74
            f.box('hall_coffer_panel',x,y,z,core_width/12-.02,.10,core_depth/8-.02,'#3b7161')
            f.box('hall_coffer_frame',x,y-.07,z,core_width/12,.035,.06,'#b29355')
            f.box('hall_coffer_frame',x,y-.07,z,.06,.035,core_depth/8,'#b29355')
            ceiling_flower(f,x,y-.071,z,min(core_width/12,core_depth/8)*.83)
    for side in (-1,1):
        for j in range(70):
            z=front+depth*j/69
            roof_t=max(0,1-abs(z-10.74)/10.74);inner_h=min(7.30,6.55+3.6*roof_t**1.35-.36)
            f.tube('hall_exposed_ceiling_rafter',(center+side*core_width/2,inner_h,z),(center+side*(width/2-.10),6.0,z),.060,'#528473',8)
        for j in range(88):
            x=lo+width*j/87;z_outer=front if side==-1 else back;z_inner=inner_z[0] if side==-1 else inner_z[1]
            f.tube('hall_front_back_ceiling_rafter',(x,6.0,z_outer),(x,7.30,z_inner),.055,'#528473',8)
    # Stone-faced raised terrace with the five existing center approach steps.
    f.box('walk-floor_terrace',center,.36,front-1.8,width+1.5,.72,3.3,'#bbb5a7')
    for n in range(5):
        z=front-5.1+n*.53;h=.15+n*.158
        f.box('walk-floor_step',center,h/2,z,5,h,.58,'#c3bcac')
    # Low upper threshold connects terrace to the hall's wooden floor.
    f.box('walk-floor_upper_step',center,.43,front-.60,5,.86,.65,'#c1b9a7')
    for side in (-1,1):
        for n in range(4):
            h=.18*(n+1);f.box('walk-floor_side_step',center+side*(7.8-n*.45),h/2,front-2.9, .5,h,1.35,'#bdb7a7')
    for i in range(17):
        for yy in (.22,.52):f.box('terrace_stone_joint',center-width/2+i*width/16,yy,front-3.47,.016,.25,.008,'#8f8b80')
    # Open timber wings: five western bays and six eastern bays, inferred from photos.
    for wing,l,r,eave,bays in [('west',.9,roof_left-.65,4.15,5),('east',roof_right+.65,length-.9,4.55,6)]:
        ww=r-l;fd=1.4;bd=13.2;bayw=ww/bays
        f.box('walk-floor_'+wing+'_maroo',(l+r)/2,.615,(fd+bd)/2,ww,.07,bd-fd,'#957044')
        for j in range(bays+1):
            for z in (fd,bd):f.post(wing+'_wing_column',l+ww*j/bays,z,.58,eave-.8,.18,'#864536')
        # The inner end of each wing contains two rooms, outer bays stay open.
        room_left=r-2*bayw if wing=='west' else l;room_right=room_left+2*bayw
        f.box('hall-wall_'+wing+'_rear',(room_left+room_right)/2,2.1,bd,2*bayw,3.04,.17,'#dacbb0',True)
        f.box('hall-wall_'+wing+'_rooms',(room_left+room_right)/2,2.0,8.2,2*bayw,2.84,.16,'#dbcfb5',True)
        for xx in (room_left,room_left+bayw,room_right):f.box('hall-wall_'+wing+'_room_partition',xx,2.0,(8.2+bd)/2,.15,2.84,bd-8.2,'#dbcfb5',True)
        for j in range(4):lattice_door(f,wing+'_wing_room_door',room_left+(j+.5)*bayw/2,8.09,bayw/2-.09,.8,3.4,paper='#d7d1b7')
        for z in (fd,bd):f.box(wing+'_wing_beam',(l+r)/2,eave-.40,z,ww,.32,.32,'#49735d')
        for j in range(36):f.box(wing+'_floor_joint',(l+r)/2,.658,fd+(bd-fd)*j/35,ww,.01,.015,'#6a5234')
    # Clear internal space is based on photographs, with no invented display objects.
    interior=f.point(center,front+4.7)
    places.insert(0,dict(id='interior',name='금성관 정청',position=interior,arrival=interior,radius=5,indoor=True,description='공식 내부 사진을 참고한 우물마루와 단청 천장입니다. 중앙 문짝은 탐험을 위해 열어 두었습니다.'))
    places.insert(1,dict(id='hall',name='금성관 앞마당',position=f.point(center,front-12),radius=24,description='높은 정청과 낮은 동서익헌, 월대와 박석길을 둘러보세요.'))
    return f.point(center,front)

def photo_gate(w):
    pts=w['points'][:-1];a,b=pts[1],pts[2];width=math.dist(a,b)
    f=HeritageFrame(a,((b[0]-a[0])/width,(b[1]-a[1])/width));depth=math.dist(pts[0],pts[1]);outer=w['id']=='832423356';name='manghwaru' if outer else 'middle_gate'
    # The historic entrance pavilion has an open upper story and three lower bays.
    inset=1.15 if outer else .55;lo,hi=inset,width-inset;front=.9;back=depth-.9;bay=(hi-lo)/3
    polygon('ground_floor_'+w['id'],pts,.065,'#bfb092')
    for x in [lo,lo+bay,lo+bay*2,hi]:
        for z in (front,back):f.post(name+'_column',x,z,.08,6.6 if outer else 3.05,.22,'#864b33')
    for i in range(3):
        x=lo+bay*(i+.5)
        if i!=1:
            f.box('hall-wall_'+name+'_closed_bay',x,1.57,front,bay-.3,3,.14,'#92512f',True)
            for k in range(9):f.box(name+'_door_plank',x-bay/2+.25+k*(bay-.5)/8,1.57,front-.10,.022,2.96,.035,'#633c29')
            for yy in (.7,1.6,2.45):
                f.box(name+'_door_iron_band',x,yy,front-.14,bay-.35,.06,.035,'#383b37')
                for k in range(6):f.tube(name+'_door_stud',(x-bay/2+.3+k*(bay-.6)/5,yy,front-.15),(x-bay/2+.3+k*(bay-.6)/5,yy,front-.18),.04,'#494c43',8)
        for z in (front,back):f.box(name+'_lower_beam',x,3.2 if outer else 2.9,z,bay,.35,.36,'#846039')
    for x in (lo,hi):f.box('hall-wall_'+name+'_side',x,1.55,(front+back)/2,.20,2.95,back-front,'#dccdaa',True)
    if outer:
        f.box('manghwaru_upper_floor',width/2,3.48,depth/2,hi-lo+.3,.22,back-front+.3,'#95723d')
        for z in (front-.15,back+.15):
            for yy,col,h in [(3.72,'#846132',.12),(4.32,'#925735',.13)]:f.box('manghwaru_balcony_rail',width/2,yy,z,hi-lo,h,.12,col)
            for j in range(29):
                x=lo+(hi-lo)*j/28;f.box('manghwaru_balcony_baluster',x,4.0,z,.065,.6,.10,'#925735',rotation=(-1 if j%2 else 1)*.16)
            f.box('manghwaru_upper_beam',width/2,6.40,z,hi-lo,.38,.36,'#3f7860')
            for j in range(4):bracket(f,'manghwaru_ikgong',lo+bay*j,z,6.54)
        for x in (lo,hi):f.box('manghwaru_side_rail',x,4.25,depth/2,.14,.13,back-front,'#925735')
        f.box('manghwaru_nameboard',width/2,5.72,front-.33,3.0,.82,.13,'#373527')
        f.text('manghwaru_name','樓 華 望',width/2,5.72,front-.42,2.72,.58)
    detailed_roof(f,'roof_'+w['id'],width/2,depth/2,width+1.2,depth+1.15,6.88 if outer else 3.38,2.60 if outer else 1.62,outer)
    center=f.point(width/2,depth/2)
    places.append(dict(id=w['id'],name='망화루' if outer else '중삼문',position=center,radius=9,arrival=center,description='공식 사진을 참고한 문루입니다. 가운데 통로로 마당에 들어갈 수 있습니다.'))

def detailed_grounds():
    f=hall_detail_frame;info=hall_detail_info;c=info['center'];front=info['front']
    # Entrance lawns and the mapped perimeter are authored in the surroundings pass.
    # Stone platform and bases mark the photographed vanished inner gate; placement
    # follows aerial proportions, not a surveyed archaeological site plan.
    f.box('ground_floor_inner_gate_site',c,.08,-17.8,31,.09,13.4,'#9b9c72')
    for i in range(8):
        for z in (-13.8,-22.0):f.box('inner_gate_stone_base',c-13+i*26/7,.27,z,.58,.44,.58,'#777b6b')
    for x in (c-15.5,c+15.5):
        for j in range(22):f.box('inner_site_fence_pick',x,.42,-24.5+j*13.4/21,.055,.70,.065,'#745335')
        f.box('inner_site_fence_rail',x,.59,-17.8,.06,.07,13.4,'#745335',True)
    for z in (-24.5,-11.1):
        for start,end in [(c-15.5,c-2.2),(c+2.2,c+15.5)]:
            for j in range(22):f.box('inner_site_fence_pick',start+(end-start)*j/21,.42,z,.06,.70,.06,'#745335')
            f.box('inner_site_fence_rail',(start+end)/2,.59,z,end-start,.07,.06,'#745335',True)
    # Three-part stone approach, subtly irregular original geometry.
    approach=[(-106,21.2),(-98.5,21.2),(-68.2,22.75),(-24.5,c),(-2.9,c)]
    def path_x(z):
        for (za,xa),(zb,xb) in zip(approach,approach[1:]):
            if za<=z<=zb:return xa+(xb-xa)*(z-za)/(zb-za)
        return approach[0][1] if z<approach[0][0] else c
    rng=random.Random(614);verts=[];faces=[]
    # Irregular shared-edge slabs replace the old repeated hexagonal stone pattern.
    rows,cols=149,9
    seeds={(row,col):(-3.2+(col+.5+rng.uniform(-.31,.31))*6.4/cols,-2.9-(row+.5+rng.uniform(-.32,.32))*103.1/rows) for row in range(rows) for col in range(cols)}
    def clip(poly,nx,nz,limit):
        out=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da=a[0]*nx+a[1]*nz-limit;db=b[0]*nx+b[1]*nz-limit
            if da<=0:out.append(a)
            if (da<=0)!=(db<=0):
                t=da/(da-db);out.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
        return out
    for (row,col),(sx,sz) in seeds.items():
        poly=[(-3.2,-106),(3.2,-106),(3.2,-2.9),(-3.2,-2.9)]
        for dr in range(-2,3):
            for dc in range(-2,3):
                key=(row+dr,col+dc)
                if key==(row,col) or key not in seeds:continue
                tx,tz=seeds[key];poly=clip(poly,tx-sx,tz-sz,(tx*tx+tz*tz-sx*sx-sz*sz)/2)
        if len(poly)<3:continue
        base=len(verts)
        for x,z in poly:
            x=sx+(x-sx)*.966;z=sz+(z-sz)*.966
            y=.145 if -24.6<z<-11.0 else .105
            verts.append((path_x(z)+x,y,z))
        faces.append(tuple(range(base,base+len(poly))))
    o=f.mesh('photo_stone_walkway',verts,faces,'#aaa68a')
    for col in ('#b5ad8a','#958f72','#bcb598'):o.data.materials.append(material(col))
    for p in o.data.polygons:p.material_index=rng.randrange(4)
    for offset in (-3.35,-1.08,1.08,3.35):
        for (za,xa),(zb,xb) in zip(approach,approach[1:]):f.tube('stone_walkway_division',(xa+offset,.09,za),(xb+offset,.09,zb),.045,'#b7b19b',6)
    # The photographed stele row lies along the west boundary in the front precinct.
    for j in range(11):
        x=-3.5;z=-91+j*2.10;h=1.1+(j%4)*.18
        f.box('memorial_stele_plinth',x,.19,z,1.0,.30,.75,'#b1ac97',True)
        f.box('memorial_stele_body',x,.32+h/2,z,.68,h,.24,'#8e927f',True)
        f.box('memorial_stele_cap',x,.34+h,z,.86,.18,.46,'#686d60')
    # Low circular rubble well with a square timber surround, seen in 2012 photos.
    wx,wz=5,-5.5
    for row in range(3):
        for j in range(18):
            a=math.tau*(j+(row%2)*.5)/18
            f.box('old_well_rubble',wx+.84*math.cos(a),.17+row*.23,wz+.84*math.sin(a),.38,.23,.32,['#989886','#a5a28c','#858d7b'][j%3],True,rotation=a)
    f.box('old_well_dark_center',wx,.08,wz,1.25,.10,1.25,'#384237')
    for side in (-1,1):
        f.box('old_well_timber_rim',wx+side*.94,.78,wz,.14,.15,2.0,'#8c7250')
        f.box('old_well_timber_rim',wx,.78,wz+side*.94,2.0,.15,.14,'#8c7250')
    # Mature trunks and asymmetric foliage preserve the photographed rear tree belt.
    for x,z,h,r in [(-4,6,14,4),(4,23,16,5),(26,28,18,6),(47,24,16,5),(69,10,13,4)]:
        wx,wz=f.point(x,z);photo_tree(wx,wz,h,r,x<0)
