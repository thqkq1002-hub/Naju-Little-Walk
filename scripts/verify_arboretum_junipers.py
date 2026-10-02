"""Independent source geometry, planted transforms, LOD and envelope checks."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];name='juniper-budget-v66' if '--budget' in sys.argv else 'juniper-quality-v62';P=R/('knowledge/sources/arboretum/'+name+'.json');report=json.loads(P.read_text(encoding='utf-8'));changed=set(report['changed_objects'])
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']))
original={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed}
placements={o.name:np.asarray(o.matrix_world).copy() for o in bpy.context.scene.objects if o.name in changed}
before={o.name:np.asarray([v.co[:] for v in o.data.vertices]) for o in bpy.context.scene.objects if o.name in changed}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));bpy.context.view_layer.update()
actual={o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name not in changed}
assert original==actual,'Protected garden and scene geometry changed'
assert len(changed)==492,'Expected 246 retained junipers with both LODs'
near=[];far=[];counts={}
for o in bpy.context.scene.objects:
 lod=o.get('vegetation_lod')
 if lod:
  key=tuple(round(v,5) for row in o.matrix_world for v in row)+(o.get('vegetation_distance'),o.get('juniper_variant',-1))
  (near if lod=='near' else far).append(key)
 if o.name not in changed:continue
 assert np.allclose(np.asarray(o.matrix_world),placements[o.name],atol=1e-6,rtol=0),'Plant placement changed'
 old=before[o.name];new=np.asarray([v.co[:] for v in o.data.vertices]);assert np.all(new.min(axis=0)>=old.min(axis=0)-.00001);assert np.all(new.max(axis=0)<=old.max(axis=0)+.00001)
 assert abs(new[:,2].max()-old[:,2].max())<.00001,'Tree height changed'
 assert abs(new[:,2].min())<.00001,'Trunk is not rooted'
 assert all(m is not None for m in o.data.materials)
 counts[o['reference_habit']+'_'+lod]=counts.get(o['reference_habit']+'_'+lod,0)+1
assert sorted(near)==sorted(far),'LOD transform, distance or variant mismatch'
world=hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest();assert world==report['world_sha256']
result={'source':report['source'],'revision':report['output'],'protected_meshes':len(actual),'protected_geometry_matches_source':True,'changed_objects':len(changed),'counts':counts,'retained_placements_and_heights':True,'canopies_within_original_envelope':True,'paired_vegetation_instances':len(near),'lod_transform_distance_variant_match':True,'collision_layout_unchanged':True,'world_sha256':world}
(R/('knowledge/sources/arboretum/'+name+'-verification.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('JUNIPERS VERIFIED',json.dumps(result),flush=True)
if '--budget' in sys.argv and '--export' in sys.argv:
 target=R/'outputs/quality-v66/naju-arboretum-v66.glb'
 if target.exists():raise RuntimeError('Existing export preserved')
 bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
 print('VERIFIED EXPORT',target,flush=True)
