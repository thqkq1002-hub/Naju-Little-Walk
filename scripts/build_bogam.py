"""Photo/video-referenced Bogam-ri exterior. Blender 4.5 LTS.

blender --background --python scripts/build_bogam.py -- --render
Never opens another delivered .blend. Existing output requires --replace.
"""
import bpy
import bmesh
import json
import math
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs/bogam-tumuli.blend'
if OUTPUT.exists() and '--replace' not in sys.argv:
    raise RuntimeError('Output exists. Preserve your Blender edits before explicitly using --replace.')
OUTPUT.parent.mkdir(exist_ok=True)
(ROOT / 'public/models').mkdir(exist_ok=True)
reference = json.loads((ROOT / 'knowledge/sources/bogam-layout-reference.json').read_text(encoding='utf-8'))
LAT, LON = reference['origin']['lat'], reference['origin']['lon']
bounds = [-180, 180, -170, 170]
rng = random.Random(404)
scene = bpy.data.scenes.new('Naju_Bogamri_Four_Tumuli')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
groups = {}
for name in ('01_OSM_Landscape', '02_Reference_Mounds', '03_Estimated_Surface_Details', '04_Presentation'):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    groups[name] = col
solids, signs, places, materials = [], [], [], {}

def bp(x, y, z): return (x, -z, y)

def project(lon, lat):
    return [(float(lon)-LON)*111320*math.cos(math.radians(LAT)), -(float(lat)-LAT)*111320]

def mat(color):
    if color not in materials:
        rgb = [int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        m = bpy.data.materials.new('Color_'+color.lstrip('#'))
        m.diffuse_color = (*rgb, 1)
        m.use_nodes = True
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1)
        m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .92
        materials[color] = m
    return materials[color]

def mesh_object(name, verts, faces, color, group='03_Estimated_Surface_Details', smooth=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    uv = mesh.uv_layers.new(name='Original_surface_UV')
    for face in mesh.polygons:
        face.use_smooth = smooth
        for li in face.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (v.x/72, v.y/72)
    obj = bpy.data.objects.new(name, mesh)
    groups[group].objects.link(obj)
    mesh.materials.append(mat(color))
    obj['provenance'] = group
    return obj

def box(name, x, y, z, w, h, d, color, collision=False, rotation=0, group='03_Estimated_Surface_Details'):
    verts = [(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),(-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]
    o = mesh_object(name, verts, [(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)], color, group)
    o.location = bp(x,y,z); o.rotation_euler.z = rotation
    o['collision'] = collision
    solids.append(dict(name=name,kind='box',position=[x,y,z],size=[w,h,d],color=color,collision=collision,rotation=rotation))
    return o

def polygon(name, pts, height, color, base=0, collision=False, group='01_OSM_Landscape'):
    pts = pts[:-1] if pts[0] == pts[-1] else pts
    n = len(pts)
    verts = [bp(x,base,z) for x,z in pts] + [bp(x,base+height,z) for x,z in pts]
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))] + [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj = mesh_object(name, verts, faces, color, group)
    solids.append(dict(name=name,kind='building',position=[0,base,0],size=[1,height,1],footprint=pts,color=color,collision=collision))
    return obj

def segment(name, a, b, width, height, color, base=0, collision=False, group='03_Estimated_Surface_Details'):
    dx,dz = b[0]-a[0],b[1]-a[1]
    return box(name,(a[0]+b[0])/2,base+height/2,(a[1]+b[1])/2,math.hypot(dx,dz),height,width,color,collision,math.atan2(-dz,dx),group)

def clip_segment(a,b):
    dx,dz=b[0]-a[0],b[1]-a[1]; lo,hi=0.,1.
    for p,q in [(-dx,a[0]-bounds[0]),(dx,bounds[1]-a[0]),(-dz,a[1]-bounds[2]),(dz,bounds[3]-a[1])]:
        if abs(p)<1e-9:
            if q<0:return None
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
    return None if lo>hi else ([a[0]+lo*dx,a[1]+lo*dz],[a[0]+hi*dx,a[1]+hi*dz])

def clip_polygon(pts):
    pts = pts[:-1] if pts[0] == pts[-1] else pts
    for axis,edge,greater in [(0,bounds[0],True),(0,bounds[1],False),(1,bounds[2],True),(1,bounds[3],False)]:
        result=[]
        for a,b in zip(pts,pts[1:]+pts[:1]):
            ia=(a[axis]>=edge) if greater else (a[axis]<=edge)
            ib=(b[axis]>=edge) if greater else (b[axis]<=edge)
            if ia:result.append(a)
            if ia!=ib:
                t=(edge-a[axis])/(b[axis]-a[axis])
                result.append([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t])
        pts=result
        if not pts:break
    return pts

def inside(x,z,pts):
    hit=False
    for a,b in zip(pts,pts[1:]+pts[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:hit=not hit
    return hit

# This original texture is generated here; no reference photograph is embedded.
grass = mat('#82905b')
tex = bpy.data.images.new('Original_mown_grass_color', width=1024, height=1024)
noise_grids=[(n,weight,[[rng.uniform(-1,1) for _ in range(n)] for _ in range(n)]) for n,weight in [(8,.032),(24,.025),(64,.02),(192,.02)]]
pixels=[]
for j in range(1024):
    for i in range(1024):
        patch=0
        for n,weight,grid in noise_grids:
            u=i/1024*n;v=j/1024*n;a=int(u);b=int(v);tx=u-a;tz=v-b
            tx=tx*tx*(3-2*tx);tz=tz*tz*(3-2*tz)
            row0=grid[b%n][a%n]*(1-tx)+grid[b%n][(a+1)%n]*tx
            row1=grid[(b+1)%n][a%n]*(1-tx)+grid[(b+1)%n][(a+1)%n]*tx
            patch+=(row0*(1-tz)+row1*tz)*weight
        grain=rng.uniform(-.025,.025)
        pixels.extend((.45+grain+patch,.53+grain+patch,.275+grain*.68+patch*.8,1))
tex.pixels=pixels; tex.pack()
node=grass.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex
grass.node_tree.links.new(node.outputs['Color'],grass.node_tree.nodes['Principled BSDF'].inputs['Base Color'])

xml=ET.parse(ROOT / 'knowledge/sources/bogam-area.osm').getroot()
nodes={n.attrib['id']:project(n.attrib['lon'],n.attrib['lat']) for n in xml.findall('node')}
ways={w.attrib['id']:dict(tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')},points=[nodes[n.attrib['ref']] for n in w.findall('nd') if n.attrib['ref'] in nodes]) for w in xml.findall('way')}
site=ways['471352010']['points'][:-1]
box('ground_base_context',0,-.8,0,1600,1.6,1600,'#b5b67b',group='04_Presentation')
farmland=[]
for wid,w in ways.items():
    if w['tags'].get('landuse')!='farmland':continue
    pts=clip_polygon(w['points'])
    if len(pts)<3:continue
    farmland.append(pts)
    polygon('mapped_farmland_'+wid,pts,.018,('#a8ad67','#b9b974','#9eac62','#b4b47a')[len(farmland)%4])
    # Parcel boundaries come from OSM; crop row spacing and season are illustrative.
    verts=[];faces=[]
    for z in range(bounds[2],bounds[3],2):
        for x in range(bounds[0],bounds[1],5):
            if inside(x,z,pts) and not inside(x,z,site) and inside(x+4.5,z,pts):
                k=len(verts)
                verts += [bp(x,.032,z-.12),bp(x+4.5,.032,z-.12),bp(x+4.5,.032,z+.12),bp(x,.032,z+.12)]
                faces.append((k+3,k+2,k+1,k))
    if verts:mesh_object('estimated_crop_rows_'+wid,verts,faces,'#919b58')

polygon('ground_floor_bogam_lawn',site,.07,'#82905b')
roads=[]
for wid,w in ways.items():
    roadtype=w['tags'].get('highway')
    if not roadtype:continue
    width={'trunk':17,'primary':12,'secondary':8,'tertiary':7,'unclassified':4.6,'track':2.6,'service':3.6}.get(roadtype,2.5)
    for i,(a,b) in enumerate(zip(w['points'],w['points'][1:])):
        clipped=clip_segment(a,b)
        if not clipped:continue
        a,b=clipped
        if math.dist(a,b)<.2:continue
        roads.append((a,b,width))
        segment(f'road-edge_{wid}_{i}',a,b,width+.6,.055,'#c6c5b1',group='01_OSM_Landscape')
        segment(f'road_{wid}_{i}',a,b,width,.08,'#c3c4bb',group='01_OSM_Landscape')
        if width>=7:
            segment(f'road_center_{wid}_{i}',a,b,.11,.006,'#e4d6a0',base=.081)

# Recorded historical measurements establish scale. Current restored surfaces are inferred.
mounds=[
    dict(id=1,center=[-3,-91],width=18,depth=18,height=4.5,exponent=2,top=.12,angle=0,shape='원형, 작은 평탄 정상',dimensions_source='AKS E0011482: recorded diameter 18m, height 4.5m; current restored surface estimated'),
    dict(id=2,center=[26,-24],width=36,depth=23,height=4.3,exponent=3.7,top=.49,angle=-.19,shape='동서로 긴 네모형, 평탄 정상',dimensions_source='Photo/aerial relative-scale estimate, 36m E-W by 23m N-S; NOT a recorded current measurement'),
    dict(id=3,center=[24,35],width=38,depth=42,height=6,exponent=4.4,top=.53,angle=-.055,shape='큰 네모형, 넓은 평탄 정상',dimensions_source='NRICH 2001 report p31: pre-restoration 38m E-W, 42m N-S, height 6m; current surface estimated'),
    dict(id=4,center=[-25,49],width=23,depth=31.5,height=3.15,exponent=2.8,top=.36,angle=.20,shape='낮고 넓은 둥근 모서리형',dimensions_source='AKS E0011482: recorded remnant 23m E-W, 31.5m N-S, height 3.15m; restored shape estimated'),
]

def mound_xy(m,t,r):
    c,s=math.cos(t),math.sin(t)
    dx=math.copysign(abs(c)**(2/m['exponent']),c)*m['width']/2*r
    dz=math.copysign(abs(s)**(2/m['exponent']),s)*m['depth']/2*r
    a=m['angle']
    return m['center'][0]+dx*math.cos(a)-dz*math.sin(a),m['center'][1]+dx*math.sin(a)+dz*math.cos(a)

def mound_height(m,x,z):
    a=m['angle']; dx=x-m['center'][0];dz=z-m['center'][1]
    u=(dx*math.cos(a)+dz*math.sin(a))/(m['width']/2)
    v=(-dx*math.sin(a)+dz*math.cos(a))/(m['depth']/2)
    r=(abs(u)**m['exponent']+abs(v)**m['exponent'])**(1/m['exponent'])
    if r>1:return None
    q=min(1,(1-r)/(1-m['top']))
    return .07+m['height']*(q*q*(3-2*q))

for m in mounds:
    verts=[];faces=[];segments=112;rings=25
    for j in range(rings+1):
        q=j/rings;r=1-(1-m['top'])*q
        y=.07+m['height']*(q*q*(3-2*q))
        for i in range(segments):
            x,z=mound_xy(m,i*math.tau/segments,r)
            verts.append(bp(x,y,z))
    for j in range(rings):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments
            faces.append((a,a+segments,b+segments,b))
    faces.append(tuple(reversed(range(rings*segments,(rings+1)*segments))))
    faces.append(tuple(range(segments)))
    obj=mesh_object('mound_'+str(m['id']),verts,faces,'#82905b','02_Reference_Mounds',smooth=True)
    for face in obj.data.polygons:
        if face.normal.z<-.9:face.use_smooth=False
    obj['dimensions_source']=m['dimensions_source'];obj['restored_surface']='Photo-informed approximation, not laser scan'
    footprint=[list(mound_xy(m,i*math.tau/segments,1)) for i in range(segments)]
    solids.append(dict(name='mound_'+str(m['id']),kind='building',position=[0,.07,0],size=[1,m['height'],1],footprint=footprint,color='#82905b',collision=True))
    m['footprint']=footprint

# Short grass along the reconstructed surface, merged by material for a small GLB.
blades=[([],[]) for _ in range(3)]
for i in range(35000):
    if i<14500:
        m=mounds[i%4];x=m['center'][0]+rng.uniform(-m['width']*.55,m['width']*.55);z=m['center'][1]+rng.uniform(-m['depth']*.55,m['depth']*.55)
    else:x=rng.uniform(-125,132);z=rng.uniform(-113,85)
    if not inside(x,z,site):continue
    y=.073
    for m in mounds:
        height=mound_height(m,x,z)
        if height is not None:y=height+.008;break
    # Keep mapped approach lanes clear.
    near_road=False
    for a,b,width in roads:
        dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)))
        if math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)<width/2+.2:near_road=True;break
    if near_road:continue
    verts,faces=blades[i%3];k=len(verts);angle=rng.random()*math.tau;w=rng.uniform(.015,.035);h=rng.uniform(.055,.15)
    dx,dz=math.cos(angle)*w,math.sin(angle)*w
    verts.extend([bp(x-dx,y,z-dz),bp(x+dx,y,z+dz),bp(x+dx*.5,y+h,z+dz*.5)])
    faces.append((k,k+1,k+2))
for j,(verts,faces) in enumerate(blades):
    if verts:
        o=mesh_object('short_mown_grass_'+str(j),verts,faces,('#84934e','#adad68','#76824b')[j])
        o.data.materials[0].use_backface_culling=False

def cylinder(name,x,y,z,r,h,color):
    n=12;verts=[bp(x+r*math.cos(i*math.tau/n),yy,z+r*math.sin(i*math.tau/n)) for yy in (y-h/2,y+h/2) for i in range(n)]
    return mesh_object(name,verts,[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)],color,smooth=True)

# Low boundary planting is visible in the official photos; these exact positions are estimates.
for j,(a,b) in enumerate([([-99,82],[-61,79]),([-57,78],[-15,76]),([-47,-52],[-23,-98])]):
    n=int(math.dist(a,b)/1.6)
    for i in range(n+1):
        t=i/max(n,1);x=a[0]+(b[0]-a[0])*t;z=a[1]+(b[1]-a[1])*t
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=bp(x,.47,z))
        o=bpy.context.object;o.name=f'estimated_low_hedge_{j}_{i}';o.scale=(1.05,.75,.46)
        for c in list(o.users_collection):c.objects.unlink(o)
        groups['03_Estimated_Surface_Details'].objects.link(o);o.data.materials.append(mat('#617143'))
for j,(x,z,scale) in enumerate([(-109,77,.9),(-76,76,1),(-47,73,.9),(89,54,.85),(117,45,.95)]):
    cylinder('tree_trunk_'+str(j),x,1.4*scale,z,.11,2.8*scale,'#7f7360')
    for k,(dx,dy,dz,r) in enumerate([(0,3.3,0,1.1),(-.6,2.9,.3,.9),(.6,3.0,-.3,.95)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=r*scale,location=bp(x+dx*scale,dy*scale,z+dz*scale))
        o=bpy.context.object;o.name=f'estimated_tree_crown_{j}_{k}'
        for c in list(o.users_collection):c.objects.unlink(o)
        groups['03_Estimated_Surface_Details'].objects.link(o);o.data.materials.append(mat(('#667c44','#75894e','#7f9058')[k]))
        for face in o.data.polygons:face.use_smooth=True
    for dx,dz in [(-.45,.2),(.45,.2),(0,-.45)]:
        cylinder('tree_support_'+str(j),x+dx,.85,z+dz,.032,1.7,'#a39a7d')

# The sign format is observed at 00:55 in the official film. Placement/size are approximate.
box('estimated_information_panel',65,1.18,66.5,1.08,2.24,.14,'#cfcec5',True)
box('information_panel_base',65,.13,66.5,1.30,.26,.5,'#a6a698',True)
font_path=Path('C:/Windows/Fonts/malgunbd.ttf')
font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
for text,y,width,height in [('나주 복암리 고분군',1.91,.91,.15),('羅州 伏岩里 古墳群',1.65,.90,.12),('Bogam-ri Ancient Tombs',1.44,.88,.065),('1 · 2 · 3 · 4 호분',.65,.88,.095)]:
    curve=bpy.data.curves.new('Sign_'+text,'FONT');curve.body=text;curve.align_x='CENTER';curve.align_y='CENTER';curve.size=1;curve.extrude=.001
    if font:curve.font=font
    o=bpy.data.objects.new('sign_'+text,curve);groups['03_Estimated_Surface_Details'].objects.link(o)
    o.location=bp(65,y,66.579);o.rotation_euler=(math.pi/2,0,0);o.data.materials.append(mat('#374538'))
    bpy.context.view_layer.update()
    w=max(p[0] for p in o.bound_box)-min(p[0] for p in o.bound_box);h=max(p[1] for p in o.bound_box)-min(p[1] for p in o.bound_box)
    s=min(width/max(w,.01),height/max(h,.01));o.scale=(s,s,s)
    signs.append(dict(text=text,position=[65,y,66.579],width=width,height=height,rotation=0))
for i,(x,z) in enumerate([(58,65),(-50,71),(-17,-101)]):
    box('estimated_drain_frame_'+str(i),x,.089,z,.58,.032,.58,'#999c8d')
    box('drain_dark_inset_'+str(i),x,.108,z,.48,.015,.48,'#59615a')
    for k in range(7):box('drain_bar',x-.21+k*.07,.12,z,.026,.025,.48,'#a5aaa0')

places=[
    dict(id='approach',name='남쪽 진입로',position=[55,68],arrival=[55,68],radius=12,description='고분군과 논 사이로 이어지는 실제 지도상의 진입로입니다.'),
    dict(id='mound-3',name='3호분 앞',position=[24,35],arrival=[55,35],radius=35,description='넓고 평평한 정상부를 가진 큰 네모형 고분입니다. 조사 당시 동서 38m, 남북 42m, 높이 6m가 기록되었습니다.'),
    dict(id='mound-2',name='2호분 앞',position=[26,-24],arrival=[55,-24],radius=32,description='동서로 길게 놓인 봉분입니다. 현재 외형은 사진을 참고했고, 세부 치수는 추정했습니다.'),
    dict(id='mound-1',name='1호분 앞',position=[-3,-91],arrival=[14,-91],radius=22,description='북쪽에 자리한 원형 고분입니다. 문헌에 지름 18m, 높이 4.5m로 기록되어 있습니다.'),
    dict(id='mound-4',name='4호분 앞',position=[-25,49],arrival=[-46,49],radius=27,description='남서쪽의 낮고 넓은 봉분입니다. 복원 전 조사 치수와 복원된 외형 사진을 함께 참고했습니다.'),
]
walk_route=[[55,68],[55,35],[55,-24],[14,-70],[14,-91],[-18,-68],[-15,-28],[-4,9],[-5,26],[-46,19],[-46,49],[-48,73],[55,68]]
limitations=[
    'An exterior reference reconstruction, not a survey-grade digital twin. No current LiDAR, photogrammetry or elevation survey was available.',
    'OSM supplies the site boundary, surrounding road centrelines and broad farmland parcels. Road widths, crop rows and season are estimates.',
    'Mound numbering follows the 2001 NRICH distribution plan. Mound centres and orientation are manually inferred from 2023-04-09 Esri World Imagery; image accuracy is 5m before additional tracing error.',
    'Mounds 1, 3 and 4 use recorded historical dimensions, which are not measurements of the present restored surfaces. Mound 2 dimensions and every restored slope/top outline are photo-informed estimates.',
    'Official 2015 photographs (uploaded 2021) and frames of the 2010 heritage film inform the exterior. Excavation footage and CG chambers are not represented as present-day open entrances.',
    'The surrounding plain is level in this model. Individual trees, low hedges, drains and the sign position are estimated; internal fence lines and parking lots were not invented.',
    'Original grass textures are generated by the Blender script. Reference video, photographs and satellite tiles are not redistributed.',
]
world=dict(title='나주 산책',subtitle='복암리 고분군 · 사진과 영상 참고',source='© OpenStreetMap contributors, ODbL 1.0',source_url='https://www.openstreetmap.org/way/471352010',origin=dict(lat=LAT,lon=LON),bounds=bounds,spawn=dict(x=55,z=68,yaw=.65),solids=solids,signs=signs,places=places,buildings=[],site_osm_id='471352010',mounds=mounds,walkRoute=walk_route,limitations=limitations,reference_video='https://uci.k-heritage.tv/resolver/I801%3A1501001-001-V00276',reference_imagery=reference['imagery'])
(ROOT/'public/bogam-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(ROOT/'knowledge/sources/bogam-model-provenance.json').write_text(json.dumps({k:world[k] for k in ('source','source_url','origin','site_osm_id','mounds','limitations','reference_video','reference_imagery')},ensure_ascii=False,indent=2),encoding='utf-8')

bpy.ops.object.camera_add(location=bp(165,210,245))
camera=bpy.context.object;camera.name='Bogam_overview_camera';camera.data.type='ORTHO';camera.data.ortho_scale=330;camera.data.clip_end=2500
camera.rotation_euler=(Vector(bp(0,0,-17))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
bpy.ops.object.light_add(type='SUN',location=bp(-100,180,110))
sun=bpy.context.object;sun.name='Afternoon_sun';sun.rotation_euler=(.46,-.35,-.45);sun.data.energy=2.4;sun.data.angle=.11
scene.world=bpy.data.worlds.new('Bogam_daylight');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.77,.83,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1700;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'outputs/bogam-overview.png')
scene.view_settings.view_transform='AgX'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/bogam-tumuli.glb'),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
print(json.dumps(dict(blend=str(OUTPUT),objects=len(scene.objects),mounds=len(mounds),solids=len(solids)),ensure_ascii=False))
if '--render' in sys.argv:
    bpy.ops.render.render(write_still=True)
    camera.data.type='PERSP';camera.data.lens=29;camera.data.clip_start=.1
    scene.render.resolution_x=1600;scene.render.resolution_y=1000
    for name,eye,target in [('bogam-ground-view',(70,2.4,74),(20,3,-6)),('bogam-mounds-detail',(82,26,90),(8,0,16))]:
        camera.location=bp(*eye);camera.rotation_euler=(Vector(bp(*target))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ROOT/'outputs'/f'{name}.png');bpy.ops.render.render(write_still=True)
