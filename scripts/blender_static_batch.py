"""Consolidate opaque static meshes without repeated dependency-graph join operators."""
import bpy
import numpy as np
def batch(scene):
 groups={};retired=[];cache={}
 for o in list(scene.objects):
  if o.type=='MESH' and not o.parent and len(o.data.materials)==1 and not o.modifiers:
   key=(o.data.materials[0],o.hide_render,bool(o.data.uv_layers.active))
   groups.setdefault(key,[]).append(o)
 for (mat,hidden,hasuv),objects in groups.items():
  if len(objects)<2:continue
  verts=[];faces=[];uvs=[];smooth=[];offset=0
  for o in objects:
   m=o.data
   if m not in cache:
    vv=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',vv);vv=vv.reshape(-1,3)
    ff=[tuple(p.vertices) for p in m.polygons];ss=[p.use_smooth for p in m.polygons];uv=None
    if hasuv:uv=np.empty(len(m.loops)*2,dtype=np.float32);m.uv_layers.active.data.foreach_get('uv',uv)
    cache[m]=(vv,ff,ss,uv)
   vv,ff,ss,uv=cache[m];mat4=np.array(o.matrix_world,dtype=np.float32)
   verts.append(vv@mat4[:3,:3].T+mat4[:3,3]);faces.extend(tuple(i+offset for i in face) for face in ff);smooth.extend(ss)
   if uv is not None:uvs.append(uv)
   offset+=len(vv)
  mesh=bpy.data.meshes.new('overview_batch_'+mat.name);mesh.from_pydata(np.concatenate(verts).tolist(),[],faces);mesh.materials.append(mat)
  if uvs:mesh.uv_layers.new(name='UVMap').data.foreach_set('uv',np.concatenate(uvs))
  mesh.polygons.foreach_set('use_smooth',smooth);mesh.update()
  obj=bpy.data.objects.new('overview_batch_'+mat.name,mesh);scene.collection.objects.link(obj);obj.hide_render=hidden;retired.extend(objects)
  print('Batched',mat.name,len(objects),flush=True)
 bpy.data.batch_remove(ids=retired)
