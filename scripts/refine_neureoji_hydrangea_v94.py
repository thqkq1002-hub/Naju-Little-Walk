"""New Blender revision: mapped hydrangea trails, continuous slopes and 2026 planting study.

Open the preserved v93d artist file; never regenerate or overwrite it.
All geometry, walking planes and rail guards are authored/extracted in Blender.
"""
import bpy, json, math, random, sys, gzip, struct, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
rev=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'a'
O=R/'outputs/neureoji-v94';O.mkdir(parents=True,exist_ok=True)
SOURCE=R/'outputs/neureoji-v93/neureoji-quality-v93d.blend';TARGET=O/f'neureoji-hydrangea-v94{rev}.blend'
if TARGET.exists():raise RuntimeError('Preserve existing artist file: choose a fresh revision suffix')
source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;g=Geometry(s)
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
T=json.loads((R/'work/neureoji-v94/trail.json').read_text(encoding='utf8'))
D=json.loads((R/'work/neureoji-v94/ground.json').read_text(encoding='utf8'))
B=w['spawn']['height'];A=R/'assets/neureoji-v94';rng=random.Random(9404)
for ob in list(s.objects):
    if ob.name.startswith(('Neureoji93_hydrangea','Neureoji94_','walk-floor_hydrangea')):bpy.data.objects.remove(ob,do_unlink=True)
w['solids']=[q for q in w['solids'] if not q['name'].startswith(('walk-floor_hydrangea','Neureoji94_'))]

def material(name,image=None,color=(1,1,1),leaf=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.9
    if image:
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/image),check_existing=True);tex.image.pack()
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        if leaf:m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
    return m

class Batch:
    def __init__(self,name,mat,shadow=False,smooth=False):self.name=name;self.mat=mat;self.v=[];self.f=[];self.uv=[];self.shadow=shadow;self.smooth=smooth
    def add(self,v,f,uv=None):
        n=len(self.v);self.v.extend(v);self.f.extend(tuple(n+i for i in p) for p in f);self.uv.extend(uv or [(p[0],p[2]) for p in v])
    def card(self,c,u,v):
        c,u,v=Vector(c),Vector(u),Vector(v)
        self.add([tuple(c-u-v),tuple(c+u-v),tuple(c+u+v),tuple(c-u+v)],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)])
    def tube(self,a,b,r,n=6):
        a,b=Vector(a),Vector(b);ax=(b-a).normalized();u=ax.cross(Vector((0,1,0)))
        if u.length<.001:u=ax.cross(Vector((1,0,0)))
        u.normalize();v=ax.cross(u)
        self.add([tuple(p+r*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))) for p in [a,b] for i in range(n)],
                 [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(reversed(range(n))),tuple(range(n,2*n))])
    def finish(self):
        if not self.v:return None
        ob=g.mesh(self.name,self.v,self.f,'#ffffff',smooth=self.smooth);ob.data.materials[0]=self.mat
        ob['keep_web']=True;ob['no_shadow']=not self.shadow
        for f in ob.data.polygons:
            for li in f.loop_indices:ob.data.uv_layers.active.data[li].uv=self.uv[ob.data.loops[li].vertex_index]
        return ob

# Cut coarse land exactly at the corridor boundary and keep all existing river geometry.
land=s.objects.get('ground_native_DSM_interpreted');landmat=land.data.materials[0];bpy.data.objects.remove(land,do_unlink=True)
land=g.mesh('ground_native_DSM_interpreted',D['vertices'],D['faces'],'#ffffff',smooth=True);land['keep_web']=True;land['no_shadow']=True;land.data.materials[0]=landmat
for li,loop in enumerate(land.data.loops):
    q=land.data.vertices[loop.vertex_index].co;land.data.uv_layers.active.data[li].uv=((q.x+3100)/6200,(2300+q.y)/5000)
patch=Batch('Neureoji94_graded_woodland_banks',material('Neureoji94_woodland_floor','woodland-floor-original.png'),smooth=True)
patch.add(D['patchVertices'],D['patchFaces'],[(p[0]/5,p[2]/5) for p in D['patchVertices']]);patch.finish()

leafmat=material('Neureoji94_leaf_cutout','hydrangea-leaf-original.png',leaf=True)
headmats=[material(f'Neureoji94_bloom_cutout_{i}',f'hydrangea-head-{i}-original.png',leaf=True) for i in range(4)]
petalmats=[g.mat(c) for c in ['#85acf0','#b296e8','#db8ab9','#eee8dc']]
stem=Batch('Neureoji94_hydrangea_stems',g.mat('#506338'))
rail=Batch('Neureoji94_trail_steel_rails',g.mat('#4c524b'),True)
trunks=Batch('Neureoji94_trail_trunks',g.mat('#655945'),True)
treeleafmat=bpy.data.materials.get('Neureoji93_near_leaves')
shrub_count=0;tree_count=0;guard_count=0;floors=[];trailroutes={};railguards=[]

def leaf(batch,c,angle,l=.28):
    # Curved leaf with a raised central vein; alpha cuts the tooth-shaped original map.
    u=Vector((math.cos(angle)*l,0,math.sin(angle)*l));v=Vector((-math.sin(angle)*l*.38,l*.60,math.cos(angle)*l*.38));c=Vector(c)
    verts=[c-u-v,c+u-v,c+u,c+u+v,c-u+v,c-u,c+Vector((0,.035,0))]
    batch.add([tuple(p) for p in verts],[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)],[(0,0),(1,0),(1,.5),(1,1),(0,1),(0,.5),(.5,.5)])

def round_head(batch,c,r):
    verts=[];uv=[];rows=5;cols=12
    for j in range(rows+1):
        t=.035+(math.pi-.07)*j/rows
        for i in range(cols+1):
            a=i*math.tau/cols;rr=r*(1+.05*math.sin(a*3+t*5))
            verts.append((c[0]+rr*math.sin(t)*math.cos(a),c[1]+rr*.80*math.cos(t),c[2]+rr*math.sin(t)*math.sin(a)));uv.append((i/cols,1-j/rows))
    fs=[]
    for j in range(rows):
        for i in range(cols):n=j*(cols+1)+i;fs.append((n,n+1,n+cols+2,n+cols+1))
    batch.add(verts,fs,uv)

def lacecap(batch,core,c,r):
    # Flat fertile central disc plus large perimeter florets, unlike the rounded mophead.
    ring=[(c[0],c[1]+.04,c[2])];uv=[(.5,.5)]
    for i in range(13):
        a=i*math.tau/12;ring.append((c[0]+math.cos(a)*r*.65,c[1],c[2]+math.sin(a)*r*.65));uv.append((.5+.48*math.cos(a),.5+.48*math.sin(a)))
    core.add(ring,[(0,i+1,i+2) for i in range(12)],uv)
    for i in range(11):
        a=i*2.3999632297;xx=c[0]+math.cos(a)*r;zz=c[2]+math.sin(a)*r;yy=c[1]+rng.uniform(0,.035)
        for k in range(4):
            aa=k*math.pi/2+a;u=Vector((math.cos(aa),.10,math.sin(aa)));v=Vector((-math.sin(aa),.04,math.cos(aa)))
            center=Vector((xx,yy,zz))+u*.018
            batch.card(center,u*.026,v*.018)

def sample_at(route,d):
    pts=route['samples'];i=next((i for i,p in enumerate(pts[1:],1) if p['distance']>=d),len(pts)-1);a,b=pts[i-1],pts[i];t=(d-a['distance'])/max(.001,b['distance']-a['distance'])
    return {k:a[k]+(b[k]-a[k])*t for k in ['x','y','z','nx','nz','distance']}

for route in T['routes']:
    forest=route['id']=='woodland-hydrangea';pts=route['samples'];width=route['width']
    floor=Batch('walk-floor_hydrangea_'+route['id'],material('Neureoji94_path_'+route['id'],'path-concrete-original.png'))
    leaves=Batch('Neureoji94_hydrangea_leaves_'+route['id'],leafmat,smooth=True)
    heads=[Batch(f'Neureoji94_flower_heads_{route["id"]}_{i}',m,smooth=True) for i,m in enumerate(headmats)]
    lace=[Batch(f'Neureoji94_lacecap_{route["id"]}_{i}',m) for i,m in enumerate(petalmats[:3])]
    canopy=Batch('Neureoji94_trail_leaf_clusters_'+route['id'],treeleafmat,True)
    underleaf=Batch('Neureoji94_shrub_leaf_clusters_'+route['id'],treeleafmat)
    for k,(a,b) in enumerate(zip(pts,pts[1:])):
        aa=[(a['x']+side*a['nx']*width/2,a['y'],a['z']+side*a['nz']*width/2) for side in [-1,1]]
        bb=[(b['x']+side*b['nx']*width/2,b['y'],b['z']+side*b['nz']*width/2) for side in [-1,1]]
        top=[aa[0],aa[1],bb[1],bb[0]];vs=top+[(x,y-.14,z) for x,y,z in top]
        # Explicit triangles permit a floor plane to be extracted from the visible surface.
        floor.add(vs,[(0,1,2),(0,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(7,6,5,4)],[(p[0]*.8,p[2]*.8) for p in vs])
        if forest and a['z']<-190:
            # Photo-referenced transition to timber cliff-side walkway; no expansion into the river.
            for side in [-1,1]:
                xx=a['x']+side*a['nx']*(width/2+.03);zz=a['z']+side*a['nz']*(width/2+.03)
                trunks.tube((xx,a['y']-.1,zz),(xx,a['y']-.7,zz),.035)
    # Extend the final slab beyond its route marker so that the marker is inside the floor.
    a=pts[-1];prev=pts[-2];length=math.hypot(a['x']-prev['x'],a['z']-prev['z'])
    tx,tz=(a['x']-prev['x'])/length,(a['z']-prev['z'])/length;grade=(a['y']-prev['y'])/length
    b={**a,'x':a['x']+tx*.6,'z':a['z']+tz*.6,'y':a['y']+grade*.6}
    aa=[(a['x']+side*a['nx']*width/2,a['y'],a['z']+side*a['nz']*width/2) for side in [-1,1]]
    bb=[(b['x']+side*b['nx']*width/2,b['y'],b['z']+side*b['nz']*width/2) for side in [-1,1]]
    floor.add([aa[0],aa[1],bb[1],bb[0]],[(0,1,2),(0,2,3)])
    ob=floor.finish()
    # Join the lighting across the small authored slope segments without moving any vertex.
    # Hard side normals remain intact; only the walking surface receives continuous normals.
    centers=np.array([[p['x'],p['z']] for p in pts]);smooth_normals=[]
    for i,p in enumerate(pts):
        a,b=pts[max(0,i-1)],pts[min(len(pts)-1,i+1)];grade=(b['y']-a['y'])/max(.001,b['distance']-a['distance'])
        smooth_normals.append(Vector((-grade*p['nz'],-grade*p['nx'],1)).normalized())
    normals=[(0,0,1)]*len(ob.data.loops)
    for face in ob.data.polygons:
        for li in face.loop_indices:
            p=ob.data.vertices[ob.data.loops[li].vertex_index].co
            k=int(np.argmin(np.sum((centers-[p.x,-p.y])**2,axis=1)))
            normals[li]=tuple(smooth_normals[k] if face.normal.z>.5 else face.normal)
        if face.normal.z>.5:face.use_smooth=True
    ob.data.normals_split_custom_set(normals)
    if forest:
        ob.data.materials.append(material('Neureoji94_boardwalk','path-wood-original.png'))
        for face in ob.data.polygons:
            if -sum(ob.data.vertices[i].co.y for i in face.vertices)/len(face.vertices)<-190:face.material_index=1
    # Extract the actual Blender top faces into the same world-space walking planes.
    for k,f in enumerate(ob.data.polygons):
        if f.normal.z<.5:continue
        vs=[ob.matrix_world@ob.data.vertices[i].co for i in f.vertices]
        p=[Vector((q.x,q.z,-q.y)) for q in vs];normal=(p[1]-p[0]).cross(p[2]-p[0]);normal.normalize()
        plane=[-normal.x/normal.y,-normal.z/normal.y,normal.dot(p[0])/normal.y]
        h=sum(q.y for q in p)/len(p)
        floors.append(dict(name=ob.name+f'_{k}',kind='building',position=[0,h-.14,0],size=[1,.14,1],footprint=[[q.x,q.z] for q in p],floorPlane=plane,color='#d3bd94',collision=False))
    trailroutes[route['id']]=[[p['x'],p['z'],p['y']] for p in pts]
    distance=3.0
    while distance<route['lengthMetres']-2:
        q=sample_at(route,distance)
        if forest and q['z']<-195:break
        for side in [-1,1]:
            offset=width/2+rng.uniform(.52,.85);x=q['x']+side*q['nx']*offset;z=q['z']+side*q['nz']*offset;y=q['y']-.08
            col=rng.choices(range(4),[.46,.29,.20,.05])[0];height=rng.uniform(.90,1.48);shrub_count+=1
            for j in range(8):
                a=j*2.3999632297;c=(x+math.cos(a)*.31,y+height*.48+rng.uniform(-.17,.17),z+math.sin(a)*.31)
                underleaf.card(c,(math.cos(a)*.42,0,math.sin(a)*.42),(0,.32,0))
            for branch in range(4):
                a=branch*math.tau/4+rng.uniform(-.4,.4);cx=x+math.cos(a)*.40;cz=z+math.sin(a)*.40
                stem.tube((x,y+.08,z),(cx,y+height*.85,cz),.010,5)
                for j in range(4):
                    t=.35+j*.14;angle=a+(math.pi if j%2 else 0)
                    leaf(leaves,(x+(cx-x)*t,y+height*t,z+(cz-z)*t),angle,rng.uniform(.24,.36))
            for j in range(6):
                a=j*2.3999632297;rr=.22+.12*(j%2);c=(x+math.cos(a)*rr,y+height-rng.uniform(0,.27),z+math.sin(a)*rr)
                if forest and rng.random()<.66:lacecap(lace[col%3],heads[col],c,rng.uniform(.17,.23))
                else:round_head(heads[col],c,rng.uniform(.17,.24))
        distance+=rng.uniform(1.02,1.35)
    for batch in [leaves,underleaf,*heads,*lace]:batch.finish()
    # Close trunks and many small foliage clusters create a shaded corridor, not a flat flower field.
    for distance in range(7,int(route['lengthMetres']),5):
        q=sample_at(route,distance)
        for side in [-1,1]:
            offset=rng.uniform(5.0,10.5);x=q['x']+side*q['nx']*offset;z=q['z']+side*q['nz']*offset;y=q['y']+.30
            h=rng.uniform(8.2,12.0);tree_count+=1;trunks.tube((x,y-.4,z),(x+.10,y+h*.86,z),.13,7)
            for branch in range(7):
                a=branch*math.tau/7+rng.uniform(-.2,.2);rr=rng.uniform(1.8,3.0);cx=x+math.cos(a)*rr;cz=z+math.sin(a)*rr;cy=y+h*.72+rng.uniform(-.8,.8)
                trunks.tube((x,y+h*.42,z),(cx,cy,cz),.040)
                for j in range(12):
                    a=rng.random()*math.tau;u=rng.uniform(-1,1);rr=math.sqrt(1-u*u)*rng.uniform(.3,1.6);angle=rng.random()*math.tau
                    canopy.card((cx+math.cos(a)*rr,cy+u*1.5,cz+math.sin(a)*rr),(math.cos(angle)*1.12,0,math.sin(angle)*1.12),(0,.95,0))
    canopy.finish()
    # The narrow northern hillside rail and end guards correspond to the photo trail.
    if forest:
        for distance in range(61,int(route['lengthMetres'])-1,2):
            a=sample_at(route,distance);b=sample_at(route,min(distance+2,route['lengthMetres']))
            for side in ([-1,1] if a['z']<-190 else [1]):
                ax=a['x']+side*a['nx']*(width/2+.12);az=a['z']+side*a['nz']*(width/2+.12)
                bx=b['x']+side*b['nx']*(width/2+.12);bz=b['z']+side*b['nz']*(width/2+.12)
                rail.tube((ax,a['y'],az),(ax,a['y']+1.05,az),.040)
                for yy in [.30,.65,1.02]:rail.tube((ax,a['y']+yy,az),(bx,b['y']+yy,bz),.027)
                length=math.hypot(bx-ax,bz-az);ux,uz=-(bz-az)/length*.05,(bx-ax)/length*.05
                lo=min(a['y'],b['y']);hi=max(a['y'],b['y'])+1.07
                railguards.append(dict(name=f'Neureoji94_hillside_guard_{guard_count}',kind='building',position=[0,lo,0],size=[1,hi-lo,1],footprint=[[ax+ux,az+uz],[bx+ux,bz+uz],[bx-ux,bz-uz],[ax-ux,az-uz]],color='#4c524b',collision=True));guard_count+=1
stem.finish();trunks.finish();rail.finish()

# The old panoramic crown cards are too large beside a close walking corridor.
# Retain their distant forest coverage, clear the trail and shrink the nearby understorey.
samples=np.array([[p['x'],p['z']] for r in T['routes'] for p in r['samples']])
for old in list(s.objects):
    if not old.name.startswith('Neureoji93_woodland_crowns_'):continue
    batch=Batch(old.name,old.data.materials[0]);uv=old.data.uv_layers.active
    for face in old.data.polygons:
        vs=[old.matrix_world@old.data.vertices[i].co for i in face.vertices]
        center=sum(vs,Vector())/len(vs);x,z=center.x,-center.y;distance=1000
        if -100<x<100 and -290<z<195:distance=math.sqrt(float(np.min(np.sum((samples-[x,z])**2,axis=1))))
        if distance<22:continue
        factor=.60 if distance<45 else 1
        points=[]
        for v in vs:
            q=center+(v-center)*factor;points.append((q.x,q.z,-q.y))
        batch.add(points,[tuple(range(len(vs)))],[tuple(uv.data[i].uv) for i in face.loop_indices])
    bpy.data.objects.remove(old,do_unlink=True);batch.finish()

# Solar lights and entrance interpretation: dimensions/positions are photo approximations.
for route in T['routes']:
    for distance in range(25,int(route['lengthMetres'])-12,48):
        q=sample_at(route,distance);x=q['x']+q['nx']*(route['width']/2+1.15);z=q['z']+q['nz']*(route['width']/2+1.15);y=q['y']
        g.tube('Neureoji94_solar_light_pole',(x,y,z),(x,y+3.8,z),.038,'#8d938c')
        g.box('Neureoji94_solar_panel',x,y+3.75,z,.68,.055,.42,'#355f81',record=False)
        g.box('Neureoji94_solar_panel_frame',x,y+3.71,z,.73,.04,.47,'#d0d3c7',record=False)
        g.box('Neureoji94_light_head',x-.3,y+3.15,z,.5,.045,.16,'#d9dcd2',record=False)

# Photo-observed red booth at a flower-road stopping place; its exact location is not surveyed.
q=sample_at(T['routes'][0],105);x=q['x']-q['nx']*3.4;z=q['z']-q['nz']*3.4;y=q['y']
g.box('Neureoji94_booth_back',x,y+1.12,z+.42,.92,2.24,.08,'#913e36',record=False)
for dx in [-.42,.42]:
    for dz in [-.39,.39]:g.box('Neureoji94_booth_frame',x+dx,y+1.14,z+dz,.06,2.28,.06,'#b44336',record=False)
g.box('Neureoji94_booth_top',x,y+2.30,z,1.01,.10,.96,'#ad3a32',record=False)
g.box('Neureoji94_booth_bottom',x,y+.04,z,1.01,.08,.96,'#a04938',record=False)
g.box('Neureoji94_booth_phone',x,y+1.15,z+.32,.34,.46,.08,'#747e80',record=False)
for dx in [-.43,.43]:g.box('Neureoji94_booth_pane',x+dx,y+1.31,z,.018,1.25,.65,'#657e78',record=False)
g.label('수국길',x,y+2.10,z-.445,.70,.20,color='#f0e8db')
g.collider('Neureoji94_booth_collision',[[x-.48,z-.45],[x+.48,z-.45],[x+.48,z+.45],[x-.48,z+.45]],y,2.34)

# Current tower label colours from the 2026 exterior; retain its actual stairs and roof.
g.box('Neureoji94_tower_nameplate',-.65,w['topDeckHeightMetres']-.34,.455,2.15,1.10,.04,'#a4bfca',record=False)
for ob in s.objects:
    if ob.type=='FONT' and ob.data.body in ('느러지','전망대'):
        ob.data.materials.clear();ob.data.materials.append(g.mat('#3c67bd'));ob.location.y=-.487

w['solids'].extend(floors+railguards+g.solids)
w.update(revision=f'neureoji-hydrangea-v94{rev}',navigationFromBlend=TARGET.relative_to(R).as_posix(),bounds=[-49,55,-234,142],
         subtitle='느러지 전망대와 수국길',hydrangeaRoutes=trailroutes,hydrangeaTrailLengthMetres=sum(r['lengthMetres'] for r in T['routes']),
         hydrangeaConnector=[[3.2,21,B],[3.2,14,B],[4.6,12,B],[4.6,-5.1,B],[5,-5.1,B]])
def arrival(route,d,reverse=False):
    p=sample_at(route,d);q=sample_at(route,d+(.7 if not reverse else -.7));yaw=math.atan2(p['x']-q['x'],p['z']-q['z'])
    return dict(x=p['x'],z=p['z'],height=p['y'],yaw=yaw,pitch=-.015)
w['arrivals']['hydrangea']=arrival(T['routes'][0],106,True)
w['arrivals']['forest']=arrival(T['routes'][1],80)
w['arrivals']['boardwalk']=arrival(T['routes'][1],214)
for id,name,key in [('flower-road','수국 언덕길','hydrangea'),('woodland-hydrangea','그늘 수국길','forest'),('cliff-deck','숲길 끝 데크','boardwalk')]:
    a=w['arrivals'][key];w['places']=[p for p in w['places'] if p['id']!=id]
    w['places'].append(dict(id=id,name=name,description='여름 수국이 핀 숲길',position=[a['x'],a['z']],arrival=[a['x'],a['z']],arrivalHeight=a['height'],arrivalYaw=a['yaw'],arrivalPitch=a['pitch'],radius=2))
w['architectureViews']=[v for v in w['architectureViews'] if v['id'] not in ['hydrangea','forest']]
for id,label,key in [('hydrangea','수국 언덕길','hydrangea'),('forest','그늘 꽃길','forest')]:
    a=w['arrivals'][key];w['architectureViews'].append(dict(id=id,label=label,center=[a['x'],a['height']+1.72,a['z']],radius=.01,elevation=.015,angle=a['yaw'],fov=60))
map_labels={'tower-entry': '전망대 계단 앞', 'tower-third': '중간층 쉼터', 'peninsula-view': '정상 데크', 'flower-road': '여름 수국 꽃길', 'woodland-hydrangea': '숲 그늘 산책길', 'cliff-deck': '목재 데크'}
for place in w['places']:place['mapLabel']=map_labels[place['id']]
w['limitations']=[x for x in w['limitations'] if not x.startswith('수국길:')]+['수국길: 2026-06-27 현장 사진·OSM 중심선 참고. 폭·연결부·개별 식재·전화부스 위치 추정. 근처 366m 구간만 구현; 30m DSM 지면 추정과 여름 개화 표현.']
for font in bpy.data.fonts:
    if font.filepath and Path(font.filepath).is_file() and not font.packed_file:font.pack()
s['hydrangea_reference']='2026-06-27 visitor photographs, OSM ways 699922279/947992194, 30m DSM with explicit canopy allowance.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));stats=export('neureoji',O)
# Preserve v93's cutout semantics and prepainted distant canopy lighting through the new export.
p=R/'public/models/neureoji.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc['materials']:
    if m['name'].startswith(('Neureoji93_crown_','Neureoji93_near_leaves','Neureoji94_leaf_cutout','Neureoji94_bloom_cutout')):
        m.update(alphaMode='MASK',alphaCutoff=.38,doubleSided=True)
        bm=bpy.data.materials.get(m['name']);m['pbrMetallicRoughness']['baseColorFactor']=[min(1,c) for c in bm.diffuse_color]
    if m['name'].startswith('Neureoji93_crown_'):
        m.setdefault('extensions',{})['KHR_materials_unlit']={};m.pop('emissiveFactor',None);m.pop('emissiveTexture',None)
doc['extensionsUsed']=list(dict.fromkeys(doc.get('extensionsUsed',[])+['KHR_materials_unlit']))
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
raw,normal_stats=compact_normals(raw)
packed=gzip.compress(raw,9,mtime=0)
for suffix,data in [('.glb',raw),('.glb.gz',packed)]:
    dest=R/'public/models'/('neureoji'+suffix);temp=dest.with_suffix(dest.suffix+'.v94.tmp');temp.write_bytes(data);temp.replace(dest)
stats.update(bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest())
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha
record=dict(revision=w['revision'],blend=w['navigationFromBlend'],preservedSource=SOURCE.relative_to(R).as_posix(),preservedSourceSha256=source_sha,
            export=stats,hydrangeaBushes=shrub_count,trailTrees=tree_count,trailLengthMetres=w['hydrangeaTrailLengthMetres'],slopedFloorTriangles=len(floors),railGuards=guard_count,
            reference=T['sourceURLs'],limitations=T['limitations'],artistRevision=rev,normalStorage=normal_stats)
(R/'knowledge/sources/neureoji-v94/model.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NEUREOJI_HYDRANGEA_COMPLETE',json.dumps(record,ensure_ascii=False),flush=True)
