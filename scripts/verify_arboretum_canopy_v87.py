"""Independent checks against saved Blender source, including path clearances."""
import bpy, collections, hashlib, json, math
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'knowledge/sources/arboretum/canopy-v87.json'
report=json.loads(P.read_text(encoding='utf-8'));changed=report['changed_objects'];cache={}
def fingerprint(o):
 m=o.data
 if m not in cache:
  v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v)
  ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids)
  lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
  cache[m]=v.tobytes()+ids.tobytes()+lengths.tobytes()
 return hashlib.sha256(cache[m]+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
def wood(m):
 return collections.Counter(tuple(sorted(tuple(round(a,6) for a in m.vertices[i].co) for i in f.vertices)) for f in m.polygons if f.material_index==0)
bpy.ops.wm.open_mainfile(filepath=str(R/report['source']));scene=bpy.context.scene
original={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed}
assert original==report['protected_geometry_hashes']
old={m.name:wood(m) for m in {o.data for o in scene.objects if o.name in changed}}
bpy.ops.wm.open_mainfile(filepath=str(R/report['output']));scene=bpy.context.scene;cache.clear()
added={o.name for o in scene.objects if o.get('canopy_revision')=='v87'}
assert original=={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed and o.name not in added},'Protected objects changed'
checked=set();pairs=collections.defaultdict(list);nearfar={}
for name,entry in changed.items():
 o=scene.objects[name];assert np.array_equal(np.asarray(o.matrix_world),np.asarray(entry['matrix']).reshape(4,4)),name+' transform'
 assert o.get('reference_habit')==entry['habit'] and o.get('canopy_form')==entry['kind']
 pairs[(tuple(entry['matrix']),entry['habit'],entry['kind'],entry['variant'])].append(entry['lod'])
 m=o.data
 if m.name in checked:continue
 checked.add(m.name);current=wood(m)
 assert all(current[p]>=n for p,n in old[entry['original_mesh']].items()),m.name+' original trunk/branch removed'
 assert abs(min(v.co.z for v in m.vertices))<1e-6,m.name+' root height'
 vertices={i for f in m.polygons if f.material_index==1 for i in f.vertices}
 crown=np.array([m.vertices[i].co[:] for i in vertices]);assert crown[:,2].min()>2.7,'Foliage obstructs eye level'
 nearfar[entry['habit'],entry['kind'],entry['variant'],entry['lod']]=crown.max(axis=0)-crown.min(axis=0)
 assert m.uv_layers.active and len(m.materials)==2
assert all(sorted(lods)==['far','near'] for lods in pairs.values()),'LOD pair mismatch'
for habit,kind,variant,lod in nearfar:
 if lod=='near':
  ratio=nearfar[habit,kind,variant,'far']/nearfar[habit,kind,variant,'near']
  assert np.all((ratio>.83)&(ratio<1.27)),(habit,kind,variant,ratio)
geometry=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'))
E=json.loads((R/'knowledge/sources/arboretum/satellite-export.json').read_text())['extent']
def px(u,v):
 x=E['xmin']+(E['xmax']-E['xmin'])*u/1600;y=E['ymax']-(E['ymax']-E['ymin'])*v/1200
 return ((x/6378137*180/math.pi-126.8256689)*111320*math.cos(math.radians(35.00648)),-(math.atan(math.sinh(y/6378137))*180/math.pi-35.00648)*111320)
paths=[]
for way in geometry['ways']:
 if way['tags'].get('highway'):paths.extend(zip(way['points'],way['points'][1:]))
for trace in json.loads((R/'knowledge/sources/arboretum/detail-traces.json').read_text())['traces']:
 if 'walk' in trace['name'] or 'connection' in trace['name']:
  points=[px(*v) for v in trace['pixels']];paths.extend(zip(points,points[1:]))
for i,entry in enumerate(report['groundcover'],1):
 x,z=entry['position'];distances=[]
 for a,b in paths:
  dx,dz=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz or 1)))
  distances.append(math.hypot(x-a[0]-t*dx,z-a[1]-t*dz))
 assert min(distances)>=2.4-1e-6,'Groundcover path clearance'
 near=scene.objects['verge_mondo_v87_'+str(i)];far=scene.objects['distant_verge_mondo_v87_'+str(i)]
 assert np.array_equal(np.asarray(near.matrix_world),np.asarray(far.matrix_world))
 assert max(v.co.z for v in near.data.vertices)*near.scale.z<.55,'Groundcover height'
assert len(added)==len(report['groundcover'])*2
assert hashlib.sha256((R/'public/naju-arboretum-world.json').read_bytes()).hexdigest()==report['world_sha256']
result=dict(blend_revision=report['output'],blend_sha256=hashlib.sha256((R/report['output']).read_bytes()).hexdigest(),protected_meshes=len(original),tree_objects=len(changed),tree_pairs=len(pairs),shared_prototypes=len(checked),wood_preserved=True,transforms_preserved=True,world_unchanged=True,matched_lod_volume=True,groundcover_pairs=len(report['groundcover']),groundcover_path_clearance=True,groundcover_height_under_55cm=True)
P.with_name('canopy-v87-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result,flush=True)
