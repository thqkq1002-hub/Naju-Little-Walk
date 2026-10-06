"""Independent source/revision check, navigation preserved despite label update."""
import bpy,collections,hashlib,json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v88'
report=json.loads((R/'knowledge/sources/arboretum/central-platanus-v88.json').read_text(encoding='utf-8'));names=set(report['changed_objects']);cache={}
def fingerprint(o):
 m=o.data
 if m not in cache:
  v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
  ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
  lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
  cache[m]=v.tobytes()+ids.tobytes()+lengths.tobytes()
 return hashlib.sha256(cache[m]+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
def clip_wood(m):
 result=collections.Counter()
 for f in m.polygons:
  if f.material_index!=0:continue
  pts=[m.vertices[i].co.copy() for i in f.vertices];cut=[]
  for a,b in zip(pts,pts[1:]+pts[:1]):
   if a.z<=4.05:cut.append(a)
   if (a.z<=4.05)!=(b.z<=4.05):cut.append(a.lerp(b,(4.05-a.z)/(b.z-a.z)))
  if len(cut)>=3:result[tuple(sorted(tuple(round(c,5) for c in v) for v in cut))]+=1
 return result
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']));scene=bpy.context.scene
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in names}
assert protected==report['protected_geometry_hashes']
old={(o['vegetation_lod'],int(o['tree_crown_variant'])):clip_wood(o.data) for o in scene.objects if o.name in names}
font_before={o.name:(o.data.body,list(np.asarray(o.matrix_world).ravel())) for o in scene.objects if o.type=='FONT'}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));scene=bpy.context.scene;cache.clear()
assert protected=={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in names},'Unrelated scene geometry changed'
checked=set();volumes={};pairs=collections.defaultdict(list)
for name,entry in report['changed_objects'].items():
 o=scene.objects[name];assert list(np.asarray(o.matrix_world).ravel())==entry['matrix'];assert o['canopy_form']=='plane-central'
 lod,v=entry['lod'],entry['variant'];pairs[tuple(entry['matrix'])].append(lod)
 if o.data.name in checked:continue
 checked.add(o.data.name);m=o.data
 wood=collections.Counter(tuple(sorted(tuple(round(c,5) for c in m.vertices[i].co) for i in f.vertices)) for f in m.polygons if f.material_index==0)
 assert all(wood[p]>=n for p,n in old[lod,v].items()),'Lower trunk/root geometry changed'
 assert abs(min(v.co.z for v in m.vertices))<1e-6
 vertices={i for f in m.polygons if f.material_index==1 for i in f.vertices};c=np.asarray([m.vertices[i].co[:] for i in vertices]);assert c[:,2].min()>5
 volumes[lod,v]=c.max(axis=0)-c.min(axis=0)
 assert [a.name for a in m.materials]==['Canopy_plane_bark_v87','Canopy_plane_MASK_v87']
assert len(pairs)==120 and all(sorted(a)==['far','near'] for a in pairs.values())
for v in range(3):
 ratio=volumes['far',v]/volumes['near',v];assert np.all((ratio>.83)&(ratio<1.27)),ratio
for name,(body,matrix) in font_before.items():
 o=scene.objects[name];assert list(np.asarray(o.matrix_world).ravel())==matrix
 assert o.data.body==('중앙 가로수길' if body=='메타세쿼이아길' else body)
before=json.loads((O/'world-before.json').read_text(encoding='utf-8'));after=json.loads((O/'world-after.json').read_text(encoding='utf-8'))
for key in set(before)|set(after):
 if key not in ['places','signs','limitations']:assert before.get(key)==after.get(key),key
for a,b in zip(before['places'],after['places']):
 assert {k:v for k,v in a.items() if k not in ['name','description']}=={k:v for k,v in b.items() if k not in ['name','description']}
for a,b in zip(before['signs'],after['signs']):assert {k:v for k,v in a.items() if k!='text'}=={k:v for k,v in b.items() if k!='text'}
result=dict(blend_revision=report['output'],blend_sha256=hashlib.sha256((R/report['output']).read_bytes()).hexdigest(),protected_meshes=len(protected),central_tree_pairs=len(pairs),shared_prototypes=len(checked),lower_trunk_preserved=True,transforms_preserved=True,matched_lod_volume=True,foliage_above_5m=True,navigation_unchanged=True,world_metadata_only=True,font_labels_verified=True)
(R/'knowledge/sources/arboretum/central-platanus-v88-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result,flush=True)
