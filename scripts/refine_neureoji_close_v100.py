"""Preserve v99 and refine close hydrangeas and road-edge planting in Blender."""
import bpy,json,sys,hashlib,shutil,math,random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
from yeongsanpo_geometry import Geometry
from neureoji_glb_normals import compact_normals
from neureoji_glb_materials import preserve_foliage_materials
O=R/'outputs/neureoji-v100';O.mkdir(parents=True,exist_ok=True);K=R/'knowledge/sources/neureoji-v100';K.mkdir(parents=True,exist_ok=True)
S=R/'outputs/neureoji-v99/neureoji-reference-v99.blend';target=O/'neureoji-close-detail-v100.blend'
if target.exists():raise RuntimeError('Preserve authored revision')
sha=hashlib.sha256(S.read_bytes()).hexdigest();w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'));nav=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
shutil.copy2(R/'public/models/neureoji.glb',O/'before.glb');shutil.copy2(R/'public/neureoji-world.json',O/'world-before.json')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;g=Geometry(s)
materials=[]
for i in range(3):
 m=bpy.data.materials.new('Neureoji100_bloom_volume_'+str(i));m.use_nodes=True;m.diffuse_color=(1,1,1,1);m.use_backface_culling=False
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.93;bs.inputs['Alpha'].default_value=1
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/f'work/neureoji-v100/bloom-volume-{i}.png'))
 m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);m['bloom_surface']='Opaque volume; foliage retains alpha cutout. Procedural texture, not a photograph.';materials.append(m)
cores=[]
for ob in s.objects:
 if not ob.name.startswith('Neureoji95_bloom_core_'):continue
 i=int(ob.name.rsplit('_',1)[1]);ob.data.materials.clear();ob.data.materials.append(materials[i%3]);cores.append(ob.name)
# A few short native-looking edge tufts connect path edges to the interpreted woodland.
s.view_layers[0].update();dep=bpy.context.evaluated_depsgraph_get()
lands=[(o,BVHTree.FromObject(o,dep)) for o in s.objects if o.name in ['ground_native_DSM_interpreted','Neureoji94_graded_woodland_banks']]
def ground(x,z):
 hits=[]
 for ob,bvh in lands:
  inv=ob.matrix_world.inverted();p=bvh.ray_cast(inv@Vector((x,-z,200)),(inv.to_3x3()@Vector((0,0,-1))).normalized(),500)[0]
  if p is not None:hits.append((ob.matrix_world@p).z)
 return max(hits) if hits else None
rng=random.Random(10005);verts=[];faces=[];roots=[]
widths={'flower-road':3,'woodland-hydrangea':1.85}
for key,route in w['hydrangeaRoutes'].items():
 distance=0;next_at=2.2
 for a,b in zip(route,route[1:]):
  dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz)
  if length<.0001:continue
  while next_at<=distance+length:
   t=(next_at-distance)/length;cx=a[0]+dx*t;cz=a[1]+dz*t;nx,nz=-dz/length,dx/length
   for side in [-1,1]:
    if rng.random()<.16:continue
    offset=widths[key]/2+rng.uniform(.32,.45);x,z=cx+side*nx*offset,cz+side*nz*offset;y=ground(x,z)
    if y is None:continue
    roots.append(dict(route=key,x=x,z=z,height=y,offset=offset))
    for j in range(6):
     a0=rng.random()*math.tau;h=rng.uniform(.09,.21);width=rng.uniform(.009,.017);bend=rng.uniform(.03,.075)
     bx,bz=x+rng.uniform(-.02,.02),z+rng.uniform(-.02,.02);ux,uz=math.cos(a0),math.sin(a0);vx,vz=-uz,ux;off=len(verts)
     for yy,shift,scale in [(0,0,1),(h*.55,bend*.35,.65),(h,bend,0)]:
      for sign in [-1,1]:verts.append((bx+ux*shift+vx*width*scale*sign,y-.012+yy,bz+uz*shift+vz*width*scale*sign))
     faces.extend([(off,off+1,off+3,off+2),(off+2,off+3,off+5,off+4)])
   next_at+=rng.uniform(3.4,5.5)
  distance+=length
ob=g.mesh('Neureoji100_path_edge_tufts',verts,faces,'#566849',smooth=True);ob['keep_web']=True;ob['no_shadow']=True;ob.data.materials[0].use_backface_culling=False
# All core and path geometry, collision data, tower heights and shorelines are retained.
s['close_detail_v100']='Opaque blossom volumes, dense original petal textures and sparse short edge tufts; inferred botanical details.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));stats=export('neureoji',O,publish=False)
raw,mats=preserve_foliage_materials((O/'neureoji-web-v91.glb').read_bytes(),{m.name:list(m.diffuse_color) for m in bpy.data.materials});raw,norm=compact_normals(raw);(O/'neureoji.glb').write_bytes(raw)
d=dict(revision='neureoji-close-detail-v100',blend=target.relative_to(R).as_posix(),preservedSource=S.relative_to(R).as_posix(),preservedSourceSha256=sha,navigationSolidsSha256=nav,navigationChanged=False,opaqueCoreMeshes=cores,edgeTufts=roots,grassVertices=len(verts),maxGrassHeight=.21,restoredCutoutMaterials=mats,export=stats,normalStorage=norm)
(K/'model.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8').replace('knowledge/sources/neureoji-v95/model.json','knowledge/sources/neureoji-v100/model.json').replace("('Neureoji95_',","('Neureoji100_', 'Neureoji97_', 'Neureoji93_near_trunks_and_branches', 'Neureoji95_',").replace("p=R/'public/models/neureoji.glb'","p=R/'outputs/neureoji-v100/neureoji.glb'").replace("dest=R/'public/models'/","dest=R/'outputs/neureoji-v100'/").replace('print(json.dumps(d,ensure_ascii=False,indent=2))',"print('PACKED',d['export']['gzipBytes'])")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
assert hashlib.sha256(S.read_bytes()).hexdigest()==sha
assert hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()==nav
for name in ['neureoji.glb','neureoji.glb.gz']:shutil.copy2(O/name,R/'public/models'/name)
w.update(revision=d['revision'],navigationFromBlend=d['blend']);w['limitations'].append('v100: 꽃 중심부의 투명 구멍을 제거하고 길 밖에 낮은 풀 군집 추가. 꽃 질감·풀 종 및 개별 배치는 추정. 지도·지형·보행 바닥·충돌·전망대 표고는 유지.')
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');print('V100_COMPLETE',len(cores),len(roots),flush=True)
