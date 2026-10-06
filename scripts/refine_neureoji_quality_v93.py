"""Refine a preserved Blender scene, retaining real river geometry and working stairs."""
import bpy, math, json, sys, random, hashlib, gzip, struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export, surface
O=R/'outputs/neureoji-v93';O.mkdir(parents=True,exist_ok=True)
rev=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'a'
SOURCE=R/'outputs/neureoji-v92/neureoji-v92e.blend';TARGET=O/f'neureoji-quality-v93{rev}.blend'
if TARGET.exists():raise RuntimeError('Preserve existing artist revision; create a new refinement revision')
source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;g=Geometry(s)
base=R/'work/neureoji-v93/base-world.json'
w=json.loads((base if base.exists() else R/'public/neureoji-world.json').read_text(encoding='utf8'));B=w['spawn']['height'];top=w['topDeckHeightMetres']
D=json.loads((R/'work/neureoji-v93/landscape.json').read_text());F=json.loads((R/'work/neureoji-v93/distant-terrain.json').read_text())
A=R/'assets/neureoji-v93';rng=random.Random(9393)
removed=[]
for ob in list(s.objects):
    if ob.type=='MESH' and ob.name.startswith(('ground_native_DSM_interpreted','background_forest_canopy_','near_deciduous_tree','v79_layered_leaf_canopies','hydrangea','tower_canopy','tower_finial')):
        removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)

def material(name,color=(1,1,1),image=None,leaf=False,metal=0,rough=.82):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    if image:
        im=bpy.data.images.load(str(A/image),check_existing=True);im.pack()
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        if leaf:
            m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
    return m

class Batch:
    def __init__(self,name,mat,shadow=False):self.name=name;self.mat=mat;self.v=[];self.f=[];self.uv=[];self.shadow=shadow
    def add(self,v,f,uv=None):
        n=len(self.v);self.v.extend(v);self.f.extend(tuple(n+i for i in p) for p in f);self.uv.extend(uv or [(0,0)]*len(v))
    def card(self,center,u,v):
        c=Vector(center);u=Vector(u);v=Vector(v)
        self.add([tuple(c-u-v),tuple(c+u-v),tuple(c+u+v),tuple(c-u+v)],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)])
    def box(self,x,y,z,ww,hh,dd):
        vs=[(xx,yy,zz) for yy in [y-hh/2,y+hh/2] for xx,zz in [(x-ww/2,z-dd/2),(x+ww/2,z-dd/2),(x+ww/2,z+dd/2),(x-ww/2,z+dd/2)]]
        self.add(vs,[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
    def tube(self,a,b,r,n=7):
        a,b=Vector(a),Vector(b);ax=(b-a).normalized();u=ax.cross(Vector((0,1,0)))
        if u.length<.001:u=ax.cross(Vector((1,0,0)))
        u.normalize();v=ax.cross(u)
        self.add([tuple(p+r*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))) for p in [a,b] for i in range(n)],
            [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(reversed(range(n))),tuple(range(n,2*n))])
    def finish(self):
        if not self.v:return None
        ob=g.mesh(self.name,self.v,self.f,'#ffffff');ob.data.materials[0]=self.mat;ob['keep_web']=True;ob['no_shadow']=not self.shadow
        uv=ob.data.uv_layers.active
        for f in ob.data.polygons:
            for li in f.loop_indices:uv.data[li].uv=self.uv[ob.data.loops[li].vertex_index]
        return ob

# The regenerated land mesh is clipped at the original mapped water; it cannot protrude through the river.
land=g.mesh('ground_native_DSM_interpreted',D['vertices'],D['faces'],'#ffffff',smooth=True);land['keep_web']=True;land['no_shadow']=True
land.data.materials[0]=material('Neureoji93_mapped_landcover',image='landcover-original.png')
for li,loop in enumerate(land.data.loops):
    q=land.data.vertices[loop.vertex_index].co;land.data.uv_layers.active.data[li].uv=((q.x+3100)/6200,(2300+q.y)/5000)

# Far mountain silhouette is native terrain geometry, not a photographic backdrop.
far=g.mesh('Neureoji93_native_distant_mountains',F['vertices'],F['faces'],'#ffffff',smooth=True);far['keep_web']=True;far['no_shadow']=True
m=material('Neureoji93_distant_woodland');bs=m.node_tree.nodes.get('Principled BSDF');node=m.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='LandscapeColor'
m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);far.data.materials[0]=m
colors=far.data.color_attributes.new(name='LandscapeColor',type='FLOAT_COLOR',domain='POINT')
for i,color in enumerate(F['colors']):colors.data[i].color=color

crown_mats=[material('Neureoji93_crown_'+str(i),color=c,image='crown-original.png',leaf=True) for i,c in enumerate([(1,1,1),(.85,.97,.82),(.74,.88,.76),(.95,1.08,.88)])]
crowns=[Batch('Neureoji93_woodland_crowns_'+str(i),m) for i,m in enumerate(crown_mats)]
for x,y,z,h,color in D['trees']:
    if math.hypot(x,z)<180:h=min(h,top-2.1-y)
    if h<2:continue
    for a in [rng.random()*math.tau+i*math.pi/3 for i in range(3)]:
        crowns[color].card((x,y+h*.52,z),(math.cos(a)*h*1.12,0,math.sin(a)*h*1.12),(0,h*.52,0))
for b in crowns:b.finish()
print('Mapped dense woodland crowns:',len(D['trees']),flush=True)

# Original foliage atlas is scaled as clusters of small leaves on actual branch envelopes.
leafmat=material('Neureoji93_near_leaves',image='leaf-cluster-original.png',leaf=True)
leaves=Batch('Neureoji93_near_leaf_clusters',leafmat,True)
bark=g.mat('#665b46');branches=Batch('Neureoji93_near_trunks_and_branches',bark,True)
pine=Batch('Neureoji93_pine_needle_clusters',crown_mats[2],True)
near=[]
for k in range(34):
    a=k*math.tau/34;rr=rng.uniform(12,36);x=math.cos(a)*rr;z=math.sin(a)*rr
    if z>5 and abs(x-3.2)<4:continue
    base=B-1.6;h=rng.uniform(7.5,10.8);is_pine=k%3==0;near.append(dict(x=x,z=z,height=h,type='pine' if is_pine else 'broadleaf'))
    branches.tube((x,base,z),(x+.15,base+h*.72,z),.13 if is_pine else .17)
    if is_pine:
        for layer in range(6):
            yy=base+h*(.35+layer*.095);radius=(1-layer*.115)*rng.uniform(1.4,2.4)
            for j in range(6):
                aa=j*math.tau/6+layer*.55;xx=x+math.cos(aa)*radius;zz=z+math.sin(aa)*radius
                branches.tube((x,yy,z),(xx,yy+.22,zz),.035)
                for q in range(4):
                    t=.4+q*.19;cx=x+(xx-x)*t;cz=z+(zz-z)*t
                    for rotation in [aa,aa+math.pi/2]:pine.card((cx,yy+.25,cz),(math.cos(rotation)*.55,0,math.sin(rotation)*.55),(0,.37,0))
    else:
        for j in range(8):
            aa=j*math.tau/8;radius=rng.uniform(1.4,2.6);cx=x+math.cos(aa)*radius;cz=z+math.sin(aa)*radius;yy=base+h*.75+rng.uniform(-.8,.9)
            branches.tube((x,base+h*.42,z),(cx,yy,cz),.043)
            for q in range(58):
                az=rng.random()*math.tau;u=rng.uniform(-1,1);rad=math.sqrt(1-u*u)*rng.uniform(.4,1)
                center=(cx+math.cos(az)*rad*1.35,yy+u*1.25,cz+math.sin(az)*rad*1.35)
                aa=rng.random()*math.tau;l=rng.uniform(.34,.64)
                leaves.card(center,(math.cos(aa)*l,0,math.sin(aa)*l),(0,l*.72,0))
for b in [leaves,branches,pine]:b.finish()

# A handful of distant village silhouettes fill missing map coverage; dimensions are interpreted.
for k,building in enumerate(D.get('photoContextRoofs',[])):
    points=building['points'];x=sum(p[0] for p in points)/4;z=sum(p[1] for p in points)/4;y=building['ground']
    ob=g.polygon('Neureoji93_photo_context_house_'+str(k),points,y,2.9,'#c6c6b0');ob['no_shadow']=True
    g.roof('Neureoji93_photo_context_roof_'+str(k),x,y+2.9,z,max(p[0] for p in points)-min(p[0] for p in points)+.4,
        max(p[1] for p in points)-min(p[1] for p in points)+.4,.7,['#607f8b','#7c8f85','#647d9b'][k%3],tiles=False)

# Lush but locally scoped hydrangeas: actual four-petal blossoms and visible foliage.
flower_colors=['#b3bce6','#9979c3','#d3a8d2','#c16bac']
flowers=[Batch('Neureoji93_hydrangea_petals_'+str(i),g.mat(c)) for i,c in enumerate(flower_colors)]
for side in [-1,1]:
    for k in range(20):
        x=3.2+side*rng.uniform(1.7,2.4);z=7+k*.68;base=B;col=k%4
        for j in range(20):
            a=rng.random()*math.tau;l=rng.uniform(.23,.39)
            leaves.card((x+math.cos(a)*.35,base+rng.uniform(.45,.75),z+math.sin(a)*.35),(math.cos(a)*l,0,math.sin(a)*l),(0,l*.58,0))
        for j in range(4):
            cx=x+rng.uniform(-.33,.33);cz=z+rng.uniform(-.33,.33);cy=base+rng.uniform(.72,1.05)
            for n in range(32):
                az=n*2.3999632297;u=1-2*(n+.5)/32;rad=math.sqrt(1-u*u)
                normal=Vector((rad*math.cos(az),u,rad*math.sin(az)))
                center=Vector((cx,cy,cz))+normal*.15;axis=normal.cross(Vector((0,1,0)))
                if axis.length<.001:axis=Vector((1,0,0))
                axis.normalize();other=normal.cross(axis)
                for q in range(4):
                    a=q*math.pi/2;direction=axis*math.cos(a)+other*math.sin(a)
                    flowers[col].card(center+direction*.019,direction*.018,normal.cross(direction)*.013)
for b in flowers:b.finish()
# Leaves added for the shrubs are exported separately to avoid recreating a finished batch.
leaves.name='Neureoji93_hydrangea_leaves';leaves.v=leaves.v[-20*40*4:];leaves.f=[]
# Regenerate indices for the last 800 shrub cards, leaving the tree-leaf object unchanged.
leaves.f=[(i,i+1,i+2,i+3) for i in range(0,len(leaves.v),4)];leaves.uv=[(0,0),(1,0),(1,1),(0,1)]*(len(leaves.v)//4);leaves.finish()

# White coated steel, bolted connectors, deck board joints and canopy ribs.
steel=material('Neureoji93_coated_steel',(.78,.80,.76),metal=.24,rough=.40)
darkmetal=material('Neureoji93_fasteners',(.29,.32,.30),metal=.65,rough=.48)
fixings=Batch('Neureoji93_steel_fixings',darkmetal);beams=Batch('Neureoji93_structure_detail',steel,True)
cx,cz=-.65,-2.4;roofY=B+14.3
profile=[(roofY-.08,3.30),(roofY+.015,3.30),(roofY+.19,.18),(roofY+.2,0)];v=[];f=[]
for yy,rr in profile:
    for i in range(96):a=i*math.tau/96;v.append((cx+math.cos(a)*rr,yy,cz+math.sin(a)*rr))
for j in range(3):
    for i in range(96):a=j*96+i;f.append((a,j*96+(i+1)%96,(j+1)*96+(i+1)%96,a+96))
f.append(tuple(reversed(range(96))))
roof=g.mesh('tower_canopy',v,f,'#e4e7e1',smooth=True);roof.data.materials[0]=steel;roof['keep_web']=True
for i in range(16):
    a=i*math.tau/16
    beams.tube((cx,roofY-.10,cz),(cx+math.cos(a)*3.15,roofY-.10,cz+math.sin(a)*3.15),.022)
    a2=(i+1)*math.tau/16
    beams.tube((cx+math.cos(a)*3.27,roofY-.052,cz+math.sin(a)*3.27),(cx+math.cos(a2)*3.27,roofY-.052,cz+math.sin(a2)*3.27),.035)
beams.tube((cx,roofY+.18,cz),(cx,B+15.35,cz),.027)
for i in range(4):
    a=i*math.tau/4;beams.tube((cx+math.cos(a)*.7,roofY+.12,cz+math.sin(a)*.7),(cx,B+15.08,cz),.019)
for ob in list(s.objects):
    if ob.type!='MESH' or not ob.name.startswith(('tower_steel_column','tower_landing_crossbeam','tower_stair_stringer','walk-floor_stair_')):continue
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
    xx=(lo.x+hi.x)/2;zz=-(lo.y+hi.y)/2
    if ob.name.startswith('walk-floor_stair_'):
        for dx in [-.49,.49]:fixings.tube((xx+dx,hi.z+.004,zz),(xx+dx,hi.z+.009,zz),.013,6)
    elif ob.name.startswith('tower_steel_column'):
        for h in [B+.12,B+3.6,B+7.2,B+10.8]:
            beams.box(xx,h,zz,.36,.042,.36)
            for dx in [-.12,.12]:
                for dz in [-.12,.12]:fixings.tube((xx+dx,h+.02,zz+dz),(xx+dx,h+.065,zz+dz),.024,6)
    elif ob.name.startswith('tower_landing_crossbeam'):
        beams.box(xx,lo.z+.15,zz,hi.x-lo.x,.12,.045)
beams.finish();fixings.finish()

# Bench surfaces preserve the original seating envelopes and their collision data.
bench=Batch('Neureoji93_bench_slat_joinery',g.mat('#776047'),True)
for ob in list(s.objects):
    if ob.type!='MESH' or not ob.name.startswith('tower_view_bench'):continue
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
    x=(lo.x+hi.x)/2;z=-(lo.y+hi.y)/2
    for j in range(4):bench.box(x,hi.z+.008,z-.15+j*.10,.9,.018,.085)
bench.finish()

# An authored sky dome supplies a soft horizon, while the app only displays its exported unlit material.
sky_mat=bpy.data.materials.new('Neureoji93_original_sky');sky_mat.use_nodes=True;nodes=sky_mat.node_tree.nodes;nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(str(A/'sky-original.png'));tex.image.pack()
sky_mat.node_tree.links.new(tex.outputs['Color'],emission.inputs['Color']);sky_mat.node_tree.links.new(emission.outputs[0],out.inputs[0]);sky_mat.use_backface_culling=False
sky_v=[];sky_f=[];sky_uv=[];rows=24;cols=72
for j in range(rows+1):
    theta=.001+(math.pi-.002)*j/rows
    for i in range(cols+1):
        a=i*math.tau/cols;sky_v.append((22000*math.sin(theta)*math.cos(a),B+22000*math.cos(theta),22000*math.sin(theta)*math.sin(a)))
        sky_uv.append((i/cols,1-j/rows))
for j in range(rows):
    for i in range(cols):n=j*(cols+1)+i;sky_f.append((n,n+cols+1,n+cols+2,n+1))
sky=g.mesh('Neureoji93_original_sky_dome',sky_v,sky_f,'#ffffff',smooth=True);sky.data.materials[0]=sky_mat
sky['keep_web']=True;sky['sky_backdrop']=True;sky['no_shadow']=True;sky['no_receive_shadow']=True
for li,loop in enumerate(sky.data.loops):sky.data.uv_layers.active.data[li].uv=sky_uv[loop.vertex_index]

# Normal-width approach and slab joint lines sit on their actual walking surface.
pad=s.objects.get('walk-floor_tower_pad')
if pad:
    for q in pad.data.vertices:q.co.x=1+(q.co.x-1)*.82;q.co.y=-4+(q.co.y+4)*.70
seams=Batch('Neureoji93_approach_slab_joints',g.mat('#878c7d'))
for z in [12.0,14,16,18,20,22]:seams.box(3.2,B+.003,z,2.15,.006,.011)
for z in range(-4,12,3):seams.box(1,B+.003,z,9.70,.006,.012)
seams.finish()

for ob in s.objects:
    if ob.type=='FONT' and ob.data.body in ('느러지','전망대'):ob.data.size=.38
for font in bpy.data.fonts:
    if font.filepath and Path(font.filepath).is_file() and not font.packed_file:font.pack()

# New view direction targets the peninsula's agricultural core, rather than the opposite bank.
position=[-2.5,-3.4];target=[-550,-900];yaw=math.atan2(position[0]-target[0],position[1]-target[1])
w['walkRoute'].extend([[-2.1,-3.2,top],[*position,top]])
w['arrivals']['top']=dict(x=position[0],z=position[1],yaw=yaw,pitch=-.08,height=top)
for p in w['places']:
    if p['id']=='peninsula-view':p.update(position=position,arrival=position,arrivalYaw=yaw,arrivalPitch=-.08)
for view in w['architectureViews']:
    if view['id']=='peninsula':view.update(center=[position[0],top+1.72,position[1]],angle=yaw,elevation=.08,fov=58)
w['lighting']=dict(exposure=1.04,ambient=1.35,sun=2.65)
w['revision']=f'neureoji-quality-v93{rev}';w['panoramaTargetMetres']=target;w['visualBackgroundBounds']=[-8500,8500,-8500,8500]
w['limitations'].append('논밭 내부 구획·작물 색·개별 수림은 지도·사진 참고 추정. 원경 산은 30m DSM에 수관 보정을 적용한 시각 배경.')
w['source']='© OpenStreetMap contributors · ODbL 1.0 · Copernicus GLO-30 · 현장 사진 참고'
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
s['reference_basis']='Photographs 2024/2025, OSM river/land use, native GLO-30 DSM. Photo-inferred fine details, original surfaces.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
stats=export('neureoji',O)
# Cutout foliage must be stable depth-writing alpha masks in the web scene.
p=R/'public/models/neureoji.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc['materials']:
    if m['name'].startswith(('Neureoji93_crown_','Neureoji93_near_leaves')):
        m.update(alphaMode='MASK',alphaCutoff=.38,doubleSided=True)
        bm=bpy.data.materials.get(m['name']);m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color)
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0);p.write_bytes(raw);p.with_suffix('.glb.gz').write_bytes(packed)
stats.update(bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest())
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha
record=dict(revision=w['revision'],blend=TARGET.relative_to(R).as_posix(),preservedSource=SOURCE.relative_to(R).as_posix(),preservedSourceSha256=source_sha,
    export=stats,nearTrees=near,hydrangeaBushes=40,woodlandCrowns=len(D['trees']),eyeHeightMetres=1.72,topFloorHeight=top,
    panoramaOrigin=position,panoramaTarget=target,panoramaYaw=yaw,interpretation=w['limitations'],reviewPasses=1)
(R/'knowledge/sources/neureoji-v93/model.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NEUREOJI_V93A_COMPLETE',json.dumps(stats),flush=True)
