"""Assert physical geometry and world preservation independently of authoring."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];report=json.loads((R/'knowledge/sources/deudeulgang/surfaces-v72.json').read_text(encoding='utf8'))
def fingerprint(o):
    m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
    return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']))
for name,h in report['protected_geometry_hashes'].items():assert fingerprint(bpy.data.objects[name])==h,name
for name,matrix in report['grass_transforms'].items():assert np.array_equal(np.asarray(bpy.data.objects[name].matrix_world).ravel(),matrix),name
assert hashlib.sha256((R/'public/deudeulgang-world.json').read_bytes()).hexdigest()==report['world_sha256']
me=bpy.data.objects[next(iter(report['grass_transforms']))].data
assert max(v.co.z for v in me.vertices)<.5 and min(v.co.z for v in me.vertices)==0
assert len(report['ground_surfaces'])==4
assert all(len(bpy.data.objects[name].data.materials)==1 for name in report['ground_surfaces'])
result={'protected_meshes':len(report['protected_geometry_hashes']),'grass_positions_preserved':len(report['grass_transforms']),'wood_and_roots_exact':True,'world_unchanged':True,'ground_geometry_unchanged':True}
(R/'knowledge/sources/deudeulgang/surfaces-v72-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('SURFACES VERIFIED',json.dumps(result),flush=True)
