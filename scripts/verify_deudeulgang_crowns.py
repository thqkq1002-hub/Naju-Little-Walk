"""Protect mapped facilities, every plant root/transform and the walking world."""
import bpy,json,hashlib,sys,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];revision='v71' if '--fine' in sys.argv else 'v70';report=json.loads((R/('knowledge/sources/deudeulgang/pine-crowns-'+revision+'.json')).read_text(encoding='utf8'))
def fingerprint(o):
    m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
    ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
    lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
    return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']))
before={o.name:np.asarray(o.matrix_world).copy() for o in bpy.context.scene.objects if o.name.startswith(('old_pine_','distant_pine_'))}
root={o.name:sorted(set(tuple(v.co) for p in o.data.polygons if p.material_index<2 for v in [o.data.vertices[i] for i in p.vertices])) for o in bpy.context.scene.objects if o.name.startswith(('old_pine_','distant_pine_'))}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']))
for name,h in report['protected_geometry_hashes'].items():assert fingerprint(bpy.data.objects[name])==h,name
for name,transform in before.items():
    o=bpy.data.objects[name];assert np.array_equal(np.asarray(o.matrix_world),transform),name
    after=sorted(set(tuple(v.co) for p in o.data.polygons if p.material_index<2 for v in [o.data.vertices[i] for i in p.vertices]))
    assert root[name]==after,'Wood/root geometry changed: '+name
assert hashlib.sha256((R/'public/deudeulgang-world.json').read_bytes()).hexdigest()==report['world_sha256']
assert len(before)==560
for prefix,lod in [('old_pine_','near'),('distant_pine_','far')]:
    for o in bpy.context.scene.objects:
        if not o.name.startswith(prefix):continue
        assert o['vegetation_lod']==lod
        assert any(p.material_index==6 for p in o.data.polygons),'Missing continuous needle volume'
bank=bpy.data.objects['background_woodland_bank_fringe_v70'];assert max(v.co.x for v in bank.data.vertices)<-194
result={'protected_meshes':len(report['protected_geometry_hashes']),'unchanged_pine_transforms':560,'wood_and_roots_exact':True,'world_unchanged':True,'background_outside_walk_boundary':True}
(R/('knowledge/sources/deudeulgang/pine-crowns-'+revision+'-verification.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
print('PINE VERIFIED',json.dumps(result),flush=True)
