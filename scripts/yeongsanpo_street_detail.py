"""Located-photo street finishes and satellite roof massing, authored in Blender.

No source photograph is embedded. Facade modules and unmeasured dimensions are
estimates; roof coordinates remain the separately recorded satellite traces.
"""
import bpy, math, random
from yeongsanpo_geometry import Geometry

def surface(g,color,kind):
    mat=g.mat(color)
    if any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes):return
    rng=random.Random(604);n=256;rgb=[int(color[1+i:3+i],16)/255 for i in (0,2,4)];pixels=[]
    for j in range(n):
        for i in range(n):
            t=rng.uniform(.92,1.07)
            if kind=='pavers':
                row=int(j/16);mortar=(j%16<1 or (i+(row%2)*16)%32<1)
                t*=.69 if mortar else 1.0+((row*13+int((i+(row%2)*16)/32)*7)%11-5)*.009
            elif kind=='plaster':t=.96+(t-.96)*.35
            pixels.extend([min(1,c*t) for c in rgb]+[1])
    im=bpy.data.images.new('Street_original_'+kind+'_'+color[1:],width=n,height=n);im.pixels.foreach_set(pixels);im.pack()
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
    bs=mat.node_tree.nodes['Principled BSDF'];mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.91

def steel_guard(g,name,a,b,base=0):
    length=math.dist(a,b);n=max(1,math.ceil(length/2.0))
    for y in (.22,.48,.75,1.07):g.tube(name+'_horizontal',(a[0],base+y,a[1]),(b[0],base+y,b[1]),.026,'#a6b7b6',n=8)
    for i in range(n+1):
        p=[a[k]+(b[k]-a[k])*i/n for k in (0,1)]
        g.tube(name+'_post',(p[0],base,p[1]),(p[0],base+1.13,p[1]),.041,'#a6b7b6',n=8)

def wharf_detail(dock):
    level=-6.4
    # White triangular brackets under the circular lighthouse balcony (KTO).
    for i in range(12):
        angle=i*math.tau/12
        def p(r,y,offset=0):return (math.cos(angle+offset)*r,level+y,-2.3+math.sin(angle+offset)*r)
        dock.mesh('lighthouse_radial_bracket',[p(1.01,5.05,-.04),p(1.9,6.65,-.04),p(1.01,6.65,-.04),p(1.01,5.05,.04),p(1.9,6.65,.04),p(1.01,6.65,.04)],[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],'#d9ddd2')
    # Low polygonal timber enclosure visible at the foot; keep the visitor path.
    pts=[(3.35*math.cos(math.pi+i*math.pi/10),-2.3+3.35*math.sin(math.pi+i*math.pi/10)) for i in range(11)]
    for a,b in zip(pts,pts[1:]):
        for y in (.22,.59):dock.segment('lighthouse_timber_fence',a,b,.095,.105,'#786450',base=level+y,record=False)
    for x,z in pts:dock.box('lighthouse_fence_post',x,level+.39,z,.13,.78,.13,'#766351',True)
    dock.box('lighthouse_info_plinth',.1,level+.5,-5.98,.64,1,.19,'#929c99',True)
    dock.label('영산포 등대',.1,level+.76,-6.09,.57,.10,rotation=math.pi,color='#f0ecdc')
    # Horizontal metal rail pattern and cantilever brackets are observable in
    # the KTO front photo. Projection/spacing are photo-proportioned estimates.
    steel_guard(dock,'wharf_upper_steel_guard',(-42,0),(29,0))
    for left,right in [(-40,-8),(8,28)]:
        dock.box('wharf_overlook_edge',(left+right)/2,-.12,-.74,right-left,.24,1.50,'#8c7b65',record=False)
        for x in range(left,right,3):
            dock.tube('wharf_cantilever_brace',(x,-1.45,-.20),(x,-.22,-1.4),.065,'#485953',n=8)
    for y in (-.85,-1.15):dock.tube('retaining_service_pipe',(-41,y,-.35),(29,y,-.35),.040,'#667d7e',n=8)
    # Deck bolts and staggered end joints stop the timber reading as one slab.
    for row in range(17):
        z=-3.35-row*1.5
        for col in range(10):
            x=-41+col*8+(row%2)*3
            if x>41:continue
            dock.box('deck_plank_end_joint',x,level+.014,z,.018,.012,1.47,'#61574a',record=False)
    for x in (-39,39):
        dock.tube('dock_safety_ring_stand',(x,level,-23),(x,level+1.5,-23),.04,'#bac1b3',n=8)
        for i in range(24):
            a=i*math.tau/24;b=(i+1)*math.tau/24
            dock.tube('dock_lifebuoy',(x+.34*math.cos(a),level+1.15+.34*math.sin(a),-23),(x+.34*math.cos(b),level+1.15+.34*math.sin(b),-23),.075,'#d47b3b',n=7)

def roof_form(g,roof,pts,prefix='round2'):
    h=roof['height'];cx=sum(p[0] for p in pts)/len(pts);cz=sum(p[1] for p in pts)/len(pts)
    # Offset each edge inward: scaling about the centroid can push an L-shaped
    # roof's re-entrant corner outside its eaves and obstruct a narrow lane.
    winding=1 if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1]))>0 else -1
    walls=[]
    for i,p in enumerate(pts):
        a=pts[i-1];b=pts[(i+1)%len(pts)]
        normals=[]
        for u,v in [(a,p),(p,b)]:
            length=math.dist(u,v);normals.append([-(v[1]-u[1])/length*winding,(v[0]-u[0])/length*winding])
        m=[normals[0][k]+normals[1][k] for k in (0,1)];den=sum(m[k]*normals[0][k] for k in (0,1))
        walls.append([p[k]+.16*m[k]/max(.2,den) for k in (0,1)])
    g.polygon('photo-building_'+prefix+'_'+roof['id'],walls,0,h,roof['wallColor'],True)
    g.polygon(prefix+'_roof_fascia_'+roof['id'],pts,h,.16,roof['roofColor'])
    # Preserve the traced eaves instead of replacing the outline by a rectangle.
    if len(pts)==4:
        if math.dist(pts[0],pts[1])<math.dist(pts[1],pts[2]):pts=pts[1:]+pts[:1]
        a=[(pts[0][k]+pts[3][k])/2 for k in (0,1)];b=[(pts[1][k]+pts[2][k])/2 for k in (0,1)]
        rise=min(1.4,math.dist(pts[0],pts[3])*.14)
        verts=[(x,h+.16,z) for x,z in pts]+[(x,h+.16+rise,z) for x,z in (a,b)]
        g.mesh(prefix+'_pitched_roof_'+roof['id'],verts,[(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5)],roof['roofColor'])
        g.tube(prefix+'_roof_ridge',(a[0],h+.21+rise,a[1]),(b[0],h+.21+rise,b[1]),.055,roof['roofColor'],n=6)
        n=max(2,int(math.dist(a,b)/.65))
        for i in range(n+1):
            t=i/n;top=[a[k]+(b[k]-a[k])*t for k in (0,1)]
            for p,q in [(pts[0],pts[1]),(pts[3],pts[2])]:
                edge=[p[k]+(q[k]-p[k])*t for k in (0,1)]
                g.tube(prefix+'_roof_sheet_rib',(edge[0],h+.19,edge[1]),(top[0],h+.19+rise,top[1]),.021,roof['roofColor'],n=5)
    return walls

def facade_detail(g,pts,height,roads,seed):
    """Orient the estimated street facade toward the nearest mapped road."""
    def dist(p,a,b):
        d=[b[k]-a[k] for k in (0,1)];t=max(0,min(1,sum((p[k]-a[k])*d[k] for k in (0,1))/(sum(v*v for v in d) or 1)))
        return math.dist(p,[a[k]+d[k]*t for k in (0,1)])
    def road_distance(p):return min(dist(p,a,b) for r in roads for a,b in zip(r['points'],r['points'][1:]))
    edges=list(zip(pts,pts[1:]+pts[:1]));a,b=min(edges,key=lambda e:road_distance([(e[0][k]+e[1][k])/2 for k in (0,1)]))
    center=[(a[k]+b[k])/2 for k in (0,1)];length=math.dist(a,b)
    if length<3 or road_distance(center)>22:return
    area=sum(p[0]*q[1]-q[0]*p[1] for p,q in edges)
    face=Geometry(g.scene,center,math.atan2(b[1]-a[1],b[0]-a[0])+(math.pi if area>0 else 0))
    face.box('street_facade_plinth',0,.20,.06,length,.40,.11,'#8d8c80',record=False)
    for x in (-length/2+.20,length/2-.20):face.tube('street_downpipe',(x,.06,.12),(x,height-.1,.12),.046,'#7b8986',n=7)
    face.box('street_roof_gutter',0,height-.12,.14,length,.13,.19,'#707e79',record=False)
    modules=max(1,int(length/3.3))
    for i in range(modules):
        x=-length/2+(i+.5)*length/modules;w=min(2.7,length/modules-.35)
        face.box('street_store_dark_recess',x,1.28,.075,w,2.32,.05,'#344b4a',record=False)
        face.window('street_aluminium_front',x,1.29,.12,w,2.35)
        face.box('street_shop_sill',x,.10,.15,w,.12,.28,'#a9aca1',record=False)
        if height>4.7:face.window('street_upper_sash',x,height-1.15,.12,min(w,1.8),1.30)
    # Original generic sign copy: the source does not establish each business.
    if road_distance(center)<15:
        face.box('street_fascia_sign',0,2.93,.17,length-.15,.62,.18,['#37656a','#e0ded2','#857046','#446d56'][seed%4],record=False)
        face.label(['영산포 홍어','홍어 · 삼합','남도 음식','영산포 상회'][seed%4],0,2.93,.28,length-.6,.36,color='#f7eed8' if seed%4!=1 else '#364a48')
        z=.20;projection=.70
        face.mesh('street_corrugated_canopy',[(-length/2,2.60,z),(length/2,2.60,z),(length/2,2.40,z+projection),(-length/2,2.40,z+projection)],[(0,1,2,3)],['#6d827b','#8d7865','#607785'][seed%3])
        for i in range(max(2,int(length/.28))):
            x=-length/2+(i+.5)*.28
            face.tube('street_canopy_rib',(x,2.61,z),(x,2.41,z+projection),.017,'#99a296',n=5)
        face.box('street_ac_compressor',length/2-.7,2.02,.38,.82,.50,.43,'#bdc5bb',record=False)
        for i in range(6):face.box('street_ac_grille',length/2-.99+i*.11,2.02,.605,.025,.34,.018,'#7b8980',record=False)
    g.signs+=face.signs

def streets(g,roads):
    surface(g,'#7e8582','asphalt');surface(g,'#b09079','pavers');surface(g,'#b8b4a4','pavers')
    detailed=[]
    # Repeated narrow modules leave road intersections and driveways clear.
    # The red/brown pavers and yellow curbside marks are visible in KTO street
    # photos. Exact widths/intervals are estimates within mapped road shoulders.
    for road in roads:
        if road['name'] not in ('등대길','선창길','영산3길'):continue
        for a,b in zip(road['points'],road['points'][1:]):
            length=math.dist(a,b);u=[(b[k]-a[k])/length for k in (0,1)];v=[-u[1],u[0]]
            for j in range(int(length/3)):
                t=(j+.5)*3;center=[a[k]+u[k]*t for k in (0,1)]
                if not(-396<center[0]<385 and -290<center[1]<285):continue
                if t<5 or length-t<5:continue
                for side in (-1,1):
                    offset=road['width']/2+.68;p=[center[k]+v[k]*side*offset for k in (0,1)]
                    # Don't span another mapped road at a T junction.
                    def near_other():
                        for other in roads:
                            if other['id']==road['id']:continue
                            for c,d in zip(other['points'],other['points'][1:]):
                                delta=[d[k]-c[k] for k in (0,1)];dot=sum(delta[k]*(p[k]-c[k]) for k in (0,1));ratio=max(0,min(1,dot/(sum(x*x for x in delta) or 1)))
                                if math.dist(p,[c[k]+ratio*delta[k] for k in (0,1)])<other['width']/2+2:return True
                        return False
                    if near_other():continue
                    theta=math.atan2(u[1],u[0])
                    g.box('walk-floor_street_pavers',p[0],.067,p[1],3,.09,1.30,'#b09079',rotation=theta)
                    q=[center[k]+v[k]*side*(road['width']/2+.06) for k in (0,1)]
                    g.box('street_granite_kerb',q[0],.079,q[1],2.94,.12,.17,'#b8b4a4',rotation=theta,record=False)
                    if j%3==0:
                        q=[center[k]+v[k]*side*(road['width']/2-.23) for k in (0,1)]
                        g.box('street_yellow_edge_dash',q[0],.065,q[1],1.3,.008,.10,'#d7b855',rotation=theta,record=False)
                    if j%11==0:
                        q=[center[k]+v[k]*side*(road['width']/2-.32) for k in (0,1)]
                        g.box('street_drain_grate',q[0],.068,q[1],.64,.013,.40,'#435851',rotation=theta,record=False)
                detailed.append(center)
    return dict(sidewalkModules=len(detailed)*2,source='KTO 3346412–3346418; OSM road axes',dimensions='estimated')

def samhwa(g,pts):
    """OSM way/1000416564 + building no.204 in KTO 3346413/3346416.

    White shopfront faces the western street; the red brick return is beside
    the northern alley. Dimensions and faded plaque lettering are estimated.
    """
    a,b=pts[0],pts[1];w=math.dist(a,b);angle=math.atan2(b[1]-a[1],b[0]-a[0])+math.pi
    f=Geometry(g.scene,[(a[k]+b[k])/2 for k in (0,1)],angle)
    f.box('samhwa_white_front',0,3.65,.045,w,7.3,.09,'#d8d9d0',record=False)
    f.box('walk-floor_samhwa_entry_paving',0,.067,.73,w,.09,1.40,'#b09079')
    for y in (.35,3.7,6.25,7.2):f.box('samhwa_render_joint',0,y,.10,w,.025,.013,'#9fa99e',record=False)
    for x in (-w*.28,0,w*.28):f.box('samhwa_render_vertical_joint',x,3.6,.10,.019,7.15,.013,'#a8b0a7',record=False)
    for i in range(4):
        x=-w/2+(i+.5)*w/4
        f.box('samhwa_upper_dark_recess',x,5.0,.10,w/4-.35,1.95,.10,'#57666a',record=False)
        f.window('samhwa_upper_metal_sash',x,5.0,.18,w/4-.32,1.98)
        for dx in (-.48,.48):f.box('samhwa_window_slide',x+dx,5.0,.205,.04,1.94,.04,'#aab4b1',record=False)
    f.label('대  창  상  회',0,6.80,.14,w-.7,.45,color='#73776f')
    f.box('samhwa_sign_fascia',0,3.39,.20,w-.12,.83,.22,'#d1d1cc',record=False)
    f.label('삼 화 홍 어',0,3.39,.34,w-2,.51,color='#943775')
    f.box('samhwa_ground_recess',0,1.48,.11,w-.3,2.55,.08,'#344342',record=False)
    for i in range(4):
        x=-w/2+(i+.5)*w/4;f.window('samhwa_shop_sliding_glass',x,1.46,.22,w/4-.21,2.58)
    f.mesh('samhwa_weathered_canopy',[(-w/2,2.98,.22),(w/2,2.98,.22),(w/2,2.77,1.07),(-w/2,2.77,1.07)],[(0,1,2,3)],'#66746d')
    for i in range(int(w/.23)):
        x=-w/2+i*.23;f.tube('samhwa_canopy_flute',(x,2.99,.22),(x,2.78,1.07),.018,'#91978a',n=5)
    # Separate miniature lighthouse attached to the street/alley corner.
    x=-w/2+.26;z=.35
    f.vessel('samhwa_corner_lighthouse',x,0,z,1,'#d1d5cb',profile=[(0,.28),(4.9,.30),(5.42,.83),(5.52,.83),(5.55,.40),(6.44,.40),(6.55,.46),(6.69,.16),(6.73,.01)])
    for y in (5.97,):f.box('samhwa_lantern_pane',x,y,z+.41,.39,.49,.018,'#667977',record=False)
    for i in range(20):f.box('samhwa_water_gauge_mark',x+.09,1.2+i*.18,z+.31,.29 if i%5==0 else .19,.021,.035,'#646c63',record=False)
    f.box('samhwa_address_blue',x+.33,1.5,.18,.39,.25,.025,'#315c91',record=False)
    f.label('204',x+.33,1.5,.21,.32,.12,color='#eef2e1')
    f.box('samhwa_ac',w*.25,.40,.52,.83,.69,.5,'#bbc4b9',record=False)
    for i in range(7):f.box('samhwa_ac_slit',w*.25-.32+i*.105,.4,.78,.024,.48,.02,'#66756c',record=False)
    # Brick return: mortar is original geometry and does not copy photo pixels.
    a,b=pts[1],pts[2];length=math.dist(a,b)
    side=Geometry(g.scene,[(a[k]+b[k])/2 for k in (0,1)],math.atan2(b[1]-a[1],b[0]-a[0])+math.pi)
    side.box('samhwa_red_brick_return',0,3.5,.065,length,7,.1,'#955e49',record=False)
    mortar_verts=[];mortar_faces=[]
    for row in range(40):
        side.box('samhwa_horizontal_mortar',0,.09+row*.17,.125,length,.014,.015,'#c9b19b',record=False)
        for i in range(int(length/.42)):
            x=-length/2+i*.42+(row%2)*.21;y=.09+row*.17
            index=len(mortar_verts);mortar_verts.extend([(x,y,.136),(x+.014,y,.136),(x+.014,y+.17,.136),(x,y+.17,.136)]);mortar_faces.append(tuple(range(index,index+4)))
    side.mesh('samhwa_staggered_brick_joints',mortar_verts,mortar_faces,'#c9b19b')
    for x in (-length*.34,0,length*.34):
        side.box('samhwa_white_pilaster',x,3.5,.15,.28,7,.13,'#d7d9cf',record=False)
        side.window('samhwa_alley_window',x+1.1,5.0,.16,1.2,1.95)
    # Color letter marker is a short place name observed over this specific lane.
    f.tube('jukjeon_sign_arm',(-w/2-2.8,5.45,.52),(-w/2+.2,5.45,.52),.045,'#a9a691',n=8)
    for i,(txt,col) in enumerate([('죽','#b6362f'),('전','#286baf'),('골목','#3c8257')]):
        f.label(txt,-w/2-2.45+i*.72,4.95,.52,.79,.54,color=col)
    g.solids+=f.solids;g.signs+=f.signs+side.signs
    return f.point(0,2.2)
