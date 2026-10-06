"""Preserve v96; replace its nearest crossed canopy cards with grounded 3D trees."""
import bpy,bmesh,json,math,random,sys,hashlib,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
from neureoji_glb_materials import preserve_foliage_materials
O=R/'outputs/quality-v97';O.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/observatory-quality-v97';K.mkdir(parents=True,exist_ok=True)
S=R/'outputs/relief-v96/neureoji-relief-v96.blend';target=O/'neureoji-canopy-v97b.blend'
if target.exists():raise RuntimeError('Preserve existing authored revision')
source_sha=hashlib.sha256(S.read_bytes()).hexdigest()
wp=R/'public/neureoji-world.json';w=json.loads(wp.read_text(encoding='utf8'))
nav_sha=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
if not (O/'neureoji-before.glb').exists(): (O/'neureoji-before.glb').write_bytes((R/'public/models/neureoji.glb').read_bytes())
(O/'neureoji-world-before.json').write_text(json.dumps(w,ensure_ascii=False),encoding='utf8')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;g=Geometry(s);rng=random.Random(97105)
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
ground=[]
for name in ['ground_native_DSM_interpreted','Neureoji94_graded_woodland_banks']:
    ob=s.objects.get(name)
    if ob:ground.append((ob,BVHTree.FromObject(ob,dep)))
def height(x,z):
    hits=[]
    for ob,bvh in ground:
        inv=ob.matrix_world.inverted();a=inv@Vector((x,-z,200));direction=(inv.to_3x3()@Vector((0,0,-1))).normalized()
        p,normal,index,distance=bvh.ray_cast(a,direction,260)
        if p is not None:hits.append((ob.matrix_world@p).z)
    return max(hits) if hits else None
routes=[p for route in w['hydrangeaRoutes'].values() for p in route]+w['hydrangeaConnector']
pathkd=KDTree(len(routes))
for i,p in enumerate(routes):pathkd.insert((p[0],p[1],0),i)
pathkd.balance()
roots=[];removed=0
for ob in list(s.objects):
    if not ob.name.startswith('Neureoji93_woodland_crowns_'):continue
    old=ob.data;verts=list(old.vertices);keep=[]
    assert len(verts)%12==0
    for i in range(0,len(verts),12):
        pts=[ob.matrix_world@v.co for v in verts[i:i+12]]
        x=sum(p.x for p in pts)/12;z=-sum(p.y for p in pts)/12;r=math.hypot(x,z)
        if 42<r<165 and pathkd.find((x,z,0))[2]>5:
            y=height(x,z)
            if y is not None:
                h=max(p.z for p in pts)-min(p.z for p in pts)
                if r<180:h=min(h,w['topDeckHeightMetres']-2.6-y)
                if h>=2.2:roots.append(dict(x=x,z=z,base=y,height=h));removed+=1;continue
        keep.extend(range(i,i+12))
    if len(keep)==len(verts):continue
    mapping={v:i for i,v in enumerate(keep)};mesh=bpy.data.meshes.new(old.name+'_retain_distant')
    fs=[f for f in old.polygons if all(i in mapping for i in f.vertices)]
    mesh.from_pydata([tuple(verts[i].co) for i in keep],[],[tuple(mapping[i] for i in f.vertices) for f in fs]);mesh.update()
    for mat in old.materials:mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name='Original UV')
    for face,original in zip(mesh.polygons,fs):
        face.material_index=original.material_index
        for li,oi in zip(face.loop_indices,original.loop_indices):uv.data[li].uv=old.uv_layers.active.data[oi].uv
    ob.data=mesh
class Batch:
    def __init__(self,name,mat):self.name=name;self.mat=mat;self.v=[];self.f=[];self.uv=[]
    def add(self,v,f,uv=None):
        off=len(self.v);self.v.extend(v);self.f.extend(tuple(i+off for i in p) for p in f);self.uv.extend(uv or [(0,0)]*len(v))
    def tube(self,a,b,r0,r1,n=5):
        a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0)))
        if u.length<.01:u=axis.cross(Vector((1,0,0)))
        u.normalize();v=axis.cross(u)
        vertices=[tuple(p+r*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))) for p,r in [(a,r0),(b,r1)] for i in range(n)]
        self.add(vertices,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(reversed(range(n))),tuple(range(n,2*n))])
    def card(self,c,u,v):
        c,u,v=Vector(c),Vector(u),Vector(v)
        self.add([tuple(c-u-v),tuple(c+u-v),tuple(c+u+v),tuple(c-u+v)],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)])
    def finish(self,smooth=True):
        if not self.v:return
        ob=g.mesh(self.name,self.v,self.f,'#ffffff',smooth=smooth);ob.data.materials[0]=self.mat;ob['keep_web']=True;ob['no_shadow']=True
        for f in ob.data.polygons:
            for li in f.loop_indices:ob.data.uv_layers.active.data[li].uv=self.uv[ob.data.loops[li].vertex_index]
        return ob
bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1)
bm.verts.ensure_lookup_table();bm.verts.index_update()
ico=[tuple(v.co) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free()
greens=['#456340','#527746','#617f48','#3b5c3c']
crowns=[Batch('Neureoji97_volume_crowns_'+str(i),g.mat(c)) for i,c in enumerate(greens)]
trunks=Batch('Neureoji97_grounded_trunks',g.mat('#66594a'))
leafmat=bpy.data.materials['Neureoji93_near_leaves'].copy();leafmat.name='Neureoji97_leaf_detail'
shader=next(n for n in leafmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');shader.inputs['Roughness'].default_value=.92
leaves=Batch('Neureoji97_leaf_packets',leafmat)
lobes=cards=0
for k,tree in enumerate(roots):
    x,y,z,h=tree['x'],tree['base'],tree['z'],tree['height'];angle=rng.random()*math.tau
    bend=rng.uniform(-.24,.24);radius=max(.8,min(2.4,h*.27));color=k%4
    trunks.tube((x,y-.04,z),(x+bend,y+h*.76,z+.13),max(.06,h*.018),.035)
    # A narrow leader and six unequal spreading limbs leave light gaps inside a crown.
    centres=[(x+bend,y+h*.84,z+.1)]
    for j in range(6):
        a=angle+j*2.3999632297;rr=radius*rng.uniform(.55,1);yy=y+h*rng.uniform(.59,.81)
        center=(x+math.cos(a)*rr,yy,z+math.sin(a)*rr);centres.append(center)
        trunks.tube((x+bend*.4,y+h*.42,z),(center[0],center[1]-.15,center[2]),.055,.018)
    for j,c in enumerate(centres):
        rr=radius*rng.uniform(.45,.68);vertical=min(rr*.82,h*.14)
        vertices=[]
        for vx,vy,vz in ico:
            rough=rng.uniform(.87,1.13)
            vertices.append((c[0]+vx*rr*rough,c[1]+vy*vertical*rough,c[2]+vz*rr*rough))
        crowns[(color+j//3)%4].add(vertices,faces);lobes+=1
        for q in range(2):
            a=rng.random()*math.tau;u=rng.uniform(-.75,.9);side=math.sqrt(1-u*u)
            point=(c[0]+math.cos(a)*rr*side,c[1]+u*vertical,c[2]+math.sin(a)*rr*side)
            turn=a+rng.uniform(-.45,.45);sz=rng.uniform(.22,.43)
            leaves.card(point,(math.cos(turn)*sz,.08,math.sin(turn)*sz),(0,sz*.82,0));cards+=1
trunks.finish();leaves.finish(False)
for b in crowns:b.finish()
s['canopy_revision']='v97: grounded 3D volume crowns replace nearest crossed cards; individual tree species are photo-informed interpretations.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
stats=export('neureoji',O,publish=False)
raw,material_names=preserve_foliage_materials((O/'neureoji-web-v91.glb').read_bytes(),{m.name:list(m.diffuse_color) for m in bpy.data.materials})
raw,normals=compact_normals(raw);(R/'public/models/neureoji.glb').write_bytes(raw)
record=dict(revision='neureoji-canopy-v97b',blend=target.relative_to(R).as_posix(),preservedSource=S.relative_to(R).as_posix(),preservedSourceSha256=source_sha,
    navigationSolidsSha256=nav_sha,navigationChanged=False,trees=roots,removedCrossedCards=removed*3,volumeLobes=lobes,leafPackets=cards,restoredCutoutMaterials=material_names,export=stats,normalStorage=normals)
kp=K/'model.json';kp.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8')
code=code.replace("knowledge/sources/neureoji-v95/model.json","knowledge/sources/observatory-quality-v97/model.json")
code=code.replace("('Neureoji95_',", "('Neureoji97_', 'Neureoji93_near_trunks_and_branches', 'Neureoji95_',")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
assert hashlib.sha256(S.read_bytes()).hexdigest()==source_sha
assert hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()==nav_sha
w['revision']=record['revision'];w['navigationFromBlend']=target.relative_to(R).as_posix()
w['limitations'].append('v97: 근거리 숲의 가지·입체 수관·작은 잎 군집은 사진 참고 해석. 기존 추정 식재 위치를 사용하고 뿌리 높이는 표시 지형에서 조회. 수종·개별 수형은 현장 실측 아님.')
wp.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print('CANOPY_V97_COMPLETE',len(roots),flush=True)


