"""Preserve v94h and refine its flower planting from June 2026 photographs.

Geometry stays in Blender. Existing walking surfaces and mapped river are unchanged.
"""
import bpy, json, math, random, sys, gzip, struct, hashlib
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
O=R/'outputs/neureoji-v95';O.mkdir(parents=True,exist_ok=True)
SOURCE=R/'outputs/neureoji-v94/neureoji-hydrangea-v94h.blend'
TARGET=O/'neureoji-hydrangea-v95a.blend'
if TARGET.exists():raise RuntimeError('Choose a new revision; preserve the existing artist file')
source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
world_path=R/'public/neureoji-world.json';w=json.loads(world_path.read_text(encoding='utf8'))
nav_sha=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
T=json.loads((R/'knowledge/sources/neureoji-v94/trail.json').read_text(encoding='utf8'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;g=Geometry(s)
rng=random.Random(95104)
for ob in list(s.objects):
    if ob.name.startswith(('Neureoji94_hydrangea','Neureoji94_shrub_leaf','Neureoji94_flower_heads','Neureoji94_lacecap')):
        bpy.data.objects.remove(ob,do_unlink=True)

class Batch:
    def __init__(self,name,mat,smooth=False):self.name=name;self.mat=mat;self.v=[];self.f=[];self.uv=[];self.smooth=smooth
    def add(self,v,f,uv=None):
        n=len(self.v);self.v.extend(v);self.f.extend(tuple(n+i for i in p) for p in f)
        self.uv.extend(uv or [(p[0],p[2]) for p in v])
    def tube(self,a,b,r,n=5):
        a,b=Vector(a),Vector(b);ax=(b-a).normalized();u=ax.cross(Vector((0,1,0)))
        if u.length<.001:u=ax.cross(Vector((1,0,0)))
        u.normalize();v=ax.cross(u)
        self.add([tuple(p+r*(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))) for p in [a,b] for i in range(n)],
                 [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    def finish(self):
        if not self.v:return
        ob=g.mesh(self.name,self.v,self.f,'#ffffff',smooth=self.smooth);ob.data.materials[0]=self.mat
        ob['keep_web']=True;ob['no_shadow']=True
        for f in ob.data.polygons:
            for li in f.loop_indices:ob.data.uv_layers.active.data[li].uv=self.uv[ob.data.loops[li].vertex_index]
        return ob

palette=['#6d9edc','#9a7eda','#d762ad','#eeeece','#814cba','#b93188']
petal_mats=[]
for i,color in enumerate(palette):
    m=g.mat(color);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.83
    petal_mats.append(m)
leaf_original=bpy.data.materials['Neureoji94_leaf_cutout'];leaf_mats=[]
for i,tint in enumerate([(0.64,.79,.49,1),(.76,.87,.59,1),(.48,.68,.38,1)]):
    m=leaf_original.copy();m.name=f'Neureoji95_leaf_{i}';m.diffuse_color=tint;leaf_mats.append(m)
stem=Batch('Neureoji95_hydrangea_stems',g.mat('#576048'),True)
bush_count=round_count=lace_count=petal_count=leaf_count=0

def leaf(batch,c,angle,size,tilt):
    global leaf_count
    # Six toothed-texture triangles have a raised midrib and curved leaf edges.
    c=Vector(c);u=Vector((math.cos(angle)*size,tilt*size,math.sin(angle)*size))
    v=Vector((-math.sin(angle)*size*.43,size*.45,math.cos(angle)*size*.43))
    vs=[c-u-v,c+u-v,c+u,c+u+v,c-u+v,c-u,c+Vector((0,.055,0))]
    batch.add([tuple(p) for p in vs],[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)],[(0,0),(1,0),(1,.5),(1,1),(0,1),(0,.5),(.5,.5)])
    leaf_count+=1

def floret(batch,center,normal,size,angle):
    global petal_count
    c=Vector(center);n=Vector(normal).normalized();u=n.cross(Vector((0,1,0)))
    if u.length<.01:u=n.cross(Vector((1,0,0)))
    u.normalize();v=n.cross(u);uu=u*math.cos(angle)+v*math.sin(angle);vv=-u*math.sin(angle)+v*math.cos(angle)
    for k in range(4):
        a=k*math.pi/2;out=uu*math.cos(a)+vv*math.sin(a);across=n.cross(out)
        # Broad rounded sepals, a shallow cup and folded edges rather than pointed flat stars.
        vs=[c,c+out*size*.30-across*size*.40+n*size*.13,
            c+out*size*.73-across*size*.35+n*size*.22,c+out*size+n*size*.10,
            c+out*size*.73+across*size*.35+n*size*.18,c+out*size*.30+across*size*.40+n*size*.11]
        batch.add([tuple(p) for p in vs],[(0,1,2,3),(0,3,4,5)])
        petal_count+=1

def round_head(core,petals,c,r,col):
    global round_count
    vs=[];uv=[];rows=4;cols=10
    for j in range(rows+1):
        t=.04+(math.pi-.08)*j/rows
        for i in range(cols+1):
            a=i*math.tau/cols;rr=r*(1+.035*math.sin(a*3+t*4))
            vs.append((c[0]+rr*math.sin(t)*math.cos(a),c[1]+rr*.82*math.cos(t),c[2]+rr*math.sin(t)*math.sin(a)));uv.append((i/cols,1-j/rows))
    fs=[]
    for j in range(rows):
        for i in range(cols):q=j*(cols+1)+i;fs.append((q,q+1,q+cols+2,q+cols+1))
    core.add(vs,fs,uv)
    for j in range(13):
        yy=.97-j*1.40/12;az=j*2.399963;rr=math.sqrt(1-yy*yy)
        n=Vector((math.cos(az)*rr,yy,math.sin(az)*rr));p=Vector(c)+Vector((n.x*r,n.y*r*.82,n.z*r))
        floret(petals[col],p,n,rng.uniform(.033,.047),az)
    round_count+=1

def lacecap(core,petals,c,r,col):
    global lace_count
    # Small central fertile florets, surrounded by larger four-sepal sterile flowers.
    vs=[(c[0],c[1]+.03,c[2])];uv=[(.5,.5)]
    for j in range(13):
        a=j*math.tau/12;vs.append((c[0]+math.cos(a)*r*.68,c[1],c[2]+math.sin(a)*r*.68));uv.append((.5+.46*math.cos(a),.5+.46*math.sin(a)))
    core.add(vs,[(0,j+1,j+2) for j in range(12)],uv)
    for j in range(9):
        a=j*2.399963;rr=r*(.73 if j%3 else .92)
        floret(petals[col],(c[0]+math.cos(a)*rr,c[1]+rng.uniform(.005,.025),c[2]+math.sin(a)*rr),
               (math.cos(a)*.15,1,math.sin(a)*.15),rng.uniform(.038,.055),a)
    lace_count+=1

def sample(route,d):
    pts=route['samples'];i=next((i for i,p in enumerate(pts[1:],1) if p['distance']>=d),len(pts)-1)
    a,b=pts[i-1],pts[i];t=(d-a['distance'])/max(.001,b['distance']-a['distance'])
    return {k:a[k]+(b[k]-a[k])*t for k in ['x','y','z','nx','nz','distance']}

for route in T['routes']:
    forest=route['id']=='woodland-hydrangea';width=route['width'];rid=route['id']
    leaves=[Batch(f'Neureoji95_leaves_{rid}_{i}',m,True) for i,m in enumerate(leaf_mats)]
    cores=[Batch(f'Neureoji95_bloom_core_{rid}_{i}',bpy.data.materials[f'Neureoji94_bloom_cutout_{i}'],True) for i in range(4)]
    petals=[Batch(f'Neureoji95_sepal_{rid}_{i}',m,True) for i,m in enumerate(petal_mats)]
    def shrub(q,side,outer=False):
        global bush_count
        offset=width/2+(rng.uniform(1.30,1.68) if outer else rng.uniform(.61,.86))
        x=q['x']+side*q['nx']*offset;z=q['z']+side*q['nz']*offset;y=q['y']-.09
        # Photo-observed colour masses: blue/violet with pink/magenta near the booth.
        col=0 if forest and rng.random()<.55 else [0,1,2,4,5][int(q['distance']/11+side+2)%5]
        if not forest and 83<q['distance']<113:col=5 if rng.random()<.62 else 2
        h=rng.uniform(.84,1.36)+(0.13 if outer else 0);spread=rng.uniform(.36,.47)
        bush_count+=1
        for branch in range(6):
            a=branch*2.399963+rng.uniform(-.2,.2);cx=x+math.cos(a)*spread;cz=z+math.sin(a)*spread
            stem.tube((x,y+.06,z),(cx,y+h*.84,cz),.008)
            for j in range(6):
                t=.15+j*.12;angle=a+(math.pi if j%2 else 0)
                leaf(leaves[(branch+j)%3],(x+(cx-x)*t,y+h*t,z+(cz-z)*t),angle,rng.uniform(.22,.32),rng.uniform(-.28,.12))
        # Lower leaf skirt closes the previous exposed stems without a large spherical card.
        for j in range(9):
            a=j*2.399963;leaf(leaves[j%3],(x+math.cos(a)*.19,y+.25,z+math.sin(a)*.19),a,.29,-.35)
        for j in range(5):
            a=j*2.399963;rr=spread*(.55 if j%2 else .86)
            c=(x+math.cos(a)*rr,y+h-rng.uniform(0,.27),z+math.sin(a)*rr)
            if forest and rng.random()<.71:lacecap(cores[col%4],petals,c,rng.uniform(.17,.22),col)
            else:round_head(cores[col%4],petals,c,rng.uniform(.18,.24),col)
    distance=2.8
    while distance<route['lengthMetres']-3:
        q=sample(route,distance)
        if forest and q['z']<-194:break
        for side in [-1,1]:
            shrub(q,side)
            # Staggered second row only in selected patches, leaving soil and woodland gaps.
            if math.sin(distance*.17+side)>.45:shrub(sample(route,min(distance+.44,route['lengthMetres']-3)),side,True)
        distance+=rng.uniform(1.03,1.35)
    for batch in [*leaves,*cores,*petals]:batch.finish()
stem.finish()

for font in bpy.data.fonts:
    if font.filepath and Path(font.filepath).is_file() and not font.packed_file:font.pack()
s['hydrangea_v95_reference']='June 19 and June 27, 2026 photographs: layered planting, leafy skirts, lacecaps, four-sepal florets, colour masses.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));stats=export('neureoji',O,publish=False)
p=O/'neureoji-web-v91.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc['materials']:
    bm=bpy.data.materials.get(m['name'])
    if m['name'].startswith(('Neureoji93_crown_','Neureoji93_near_leaves','Neureoji94_leaf_cutout','Neureoji94_bloom_cutout','Neureoji95_leaf_')):
        m.update(alphaMode='MASK',alphaCutoff=.38,doubleSided=True)
        m['pbrMetallicRoughness']['baseColorFactor']=[min(1,c) for c in bm.diffuse_color]
    if m['name'].startswith('Neureoji93_crown_'):
        m.setdefault('extensions',{})['KHR_materials_unlit']={};m.pop('emissiveFactor',None);m.pop('emissiveTexture',None)
doc['extensionsUsed']=list(dict.fromkeys(doc.get('extensionsUsed',[])+['KHR_materials_unlit']))
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
raw,normal_stats=compact_normals(raw);packed=gzip.compress(raw,9,mtime=0)
assert len(packed)<25*1024**2,'Model exceeds the established transport budget'
for suffix,data in [('.glb',raw),('.glb.gz',packed)]:
    dest=R/'public/models'/('neureoji'+suffix);temp=dest.with_suffix(dest.suffix+'.v95.tmp');temp.write_bytes(data);temp.replace(dest)
w.update(revision='neureoji-hydrangea-v95a',navigationFromBlend=TARGET.relative_to(R).as_posix(),
         hydrangeaPlanting=dict(bushes=bush_count,roundHeads=round_count,lacecapHeads=lace_count,modeledSepals=petal_count,leaves=leaf_count))
assert hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()==nav_sha
world_path.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha
stats.update(bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest())
record=dict(revision=w['revision'],blend=w['navigationFromBlend'],preservedSource=SOURCE.relative_to(R).as_posix(),preservedSourceSha256=source_sha,
            navigationSolidsSha256=nav_sha,navigationChanged=False,export=stats,planting=w['hydrangeaPlanting'],normalStorage=normal_stats,
            sourceURLs=['https://akekanfl.tistory.com/8708274','https://naju-senior.com/local-news/21984/'])
K=R/'knowledge/sources/neureoji-v95';K.mkdir(parents=True,exist_ok=True)
(K/'model.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NEUREOJI_V95_COMPLETE',json.dumps(record,ensure_ascii=False),flush=True)
