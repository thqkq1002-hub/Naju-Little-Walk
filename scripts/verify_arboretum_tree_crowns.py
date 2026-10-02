"""Independent saved-model preservation and representation checks."""
import bpy,json,hashlib,collections,sys
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];revision='v74' if '--dense' in sys.argv else 'v73';P=R/('knowledge/sources/arboretum/tree-crowns-'+revision+'.json')
report=json.loads(P.read_text(encoding='utf-8'));changed=report['changed_objects']
geometry_bytes={}
def fingerprint(o):
 m=o.data
 if m not in geometry_bytes:
  v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
  ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
  lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
  geometry_bytes[m]=v.tobytes()+ids.tobytes()+lengths.tobytes()
 return hashlib.sha256(geometry_bytes[m]+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
def wood(m):
 return collections.Counter(tuple(sorted(tuple(round(a,6) for a in m.vertices[i].co) for i in p.vertices)) for p in m.polygons if p.material_index==0)
def bounds(m):
 return np.array([[min(v.co[a] for v in m.vertices) for a in range(3)],[max(v.co[a] for v in m.vertices) for a in range(3)]])
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']));scene=bpy.context.scene
original={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed}
old={m.name:dict(wood=wood(m),bounds=bounds(m),triangles=sum(len(p.vertices)-2 for p in m.polygons)) for m in {o.data for o in scene.objects if o.name in changed}}
assert original==report['protected_geometry_hashes'],'Source protection report mismatch'
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));scene=bpy.context.scene
geometry_bytes.clear()
assert original=={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed},'Other objects changed'
checked=set();pairs=collections.defaultdict(list)
for name,entry in changed.items():
 o=scene.objects[name];assert np.array_equal(np.asarray(o.matrix_world),np.asarray(entry['matrix']).reshape(4,4)),name+' transform'
 assert o.get('reference_habit')==entry['habit'] and o.get('tree_crown_variant')==entry['variant']
 pairs[(tuple(entry['matrix']),entry['habit'],entry['variant'])].append(entry['lod'])
 m=o.data
 if m.name in checked:continue
 checked.add(m.name);base=old[entry['original_mesh']];current=wood(m)
 assert all(current[p]>=n for p,n in base['wood'].items()),m.name+' original wood removed or moved'
 assert abs(bounds(m)[0,2])<1e-6 and abs(bounds(m)[1,2]-base['bounds'][1,2])<1e-5,m.name+' height changed'
 verts={i for p in m.polygons if p.material_index>0 for i in p.vertices};foliage=np.array([m.vertices[i].co[:] for i in verts])
 assert np.all(foliage.min(axis=0)>=base['bounds'][0]-1e-5) and np.all(foliage.max(axis=0)<=base['bounds'][1]+1e-5),m.name+' foliage expands beyond previous envelope'
 assert sum(len(p.vertices)-2 for p in m.polygons)<base['triangles'],m.name+' budget grew'
 assert m.uv_layers.active and len(m.materials)==3
assert all(sorted(lods)==['far','near'] for lods in pairs.values()),'Tree LOD pair mismatch'
assert hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest()==report['world_sha256'],'World changed'
result=dict(protected_meshes=len(original),tree_objects=len(changed),tree_pairs=len(pairs),shared_prototypes=len(checked),wood_preserved=True,transforms_preserved=True,foliage_envelope_preserved=True,world_unchanged=True,all_prototypes_lower_triangle_count=True)
P.with_name('tree-crowns-'+revision+'-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result,flush=True)
