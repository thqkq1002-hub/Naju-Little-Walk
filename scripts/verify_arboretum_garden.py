"""Independently verify protected geometry, rooted flowers, paired transforms and routes."""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'knowledge/sources/arboretum/garden-quality-v61.json'
report=json.loads(P.read_text(encoding='utf-8'));changed=set(report['changed_objects'])
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']))
original={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed}
placements={o.name:np.asarray(o.matrix_world).copy() for o in bpy.context.scene.objects if o.name in changed}
canopies={o.name:[list(o.matrix_world@v.co) for v in o.data.vertices] for o in bpy.context.scene.objects if o.name in changed and report['changed_objects'][o.name]['category']=='canopy'}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));bpy.context.view_layer.update()
actual={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed}
assert actual==original,'Protected source geometry changed'
near=[];far=[];rooted=0;trees=0;canopy_count=0
for o in bpy.context.scene.objects:
 lod=o.get('vegetation_lod')
 if lod:
  key=tuple(round(v,5) for row in o.matrix_world for v in row)+(o.get('vegetation_distance'),)
  (near if lod=='near' else far).append(key)
 if o.name not in changed:continue
 old=placements[o.name];new=np.asarray(o.matrix_world);category=report['changed_objects'][o.name]['category']
 # X/Y and linear transform exact; only flower root height may be corrected.
 assert np.allclose(new[:3,:3],old[:3,:3],atol=1e-6,rtol=0)
 assert np.allclose(new[:2,3],old[:2,3],atol=1e-6,rtol=0)
 if category=='flower' and o.name.startswith(('botanical_flower','distant_botanical_flower')):
  assert abs(new[2,3]-.052)<.000001
  assert min(v.co.z for v in o.data.vertices)<.01,'Stem has no root'
  rooted+=1
 else:assert np.allclose(new,old,atol=1e-6,rtol=0)
 if category=='canopy':
  before=np.asarray(canopies[o.name]);after=np.asarray([list(o.matrix_world@v.co) for v in o.data.vertices]);assert np.all(after.min(axis=0)>=before.min(axis=0)-.028);assert np.all(after.max(axis=0)<=before.max(axis=0)+.001);canopy_count+=1
 report['changed_objects'][o.name]['matrix_after']=[v for row in o.matrix_world for v in row]
assert sorted(near)==sorted(far),'LOD pair locations or switching distances differ'
world_hash=hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest();assert world_hash==report['world_sha256']
result={'source':report['source'],'revision':report['output'],'protected_meshes':len(actual),'protected_geometry_matches_source':True,'changed_objects':len(changed),'corrected_root_instances':rooted,'paired_vegetation_instances':len(near),'lod_transform_and_distance_match':True,'canopies_within_retained_envelope':canopy_count,'world_sha256':world_hash,'collision_layout_unchanged':True}
(R/'knowledge/sources/arboretum/garden-quality-v61-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');P.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('GARDEN VERIFIED',json.dumps(result),flush=True)
