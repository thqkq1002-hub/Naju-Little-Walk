"""Distance variants of the authored plants; detailed artist revision stays intact."""
import bpy,math,json,gzip,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum';target=O/'naju-arboretum-botanical-v12.blend'
if target.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-botanical-v11.blend'))
scene=bpy.context.scene
objects=[o for o in scene.objects if o.type=='MESH' and o.get('authored_vegetation')]
low={}
for data in {o.data for o in objects}:
 tree=data.name in ['Botanical_spreading','Botanical_rounded','Botanical_column']
 if tree:
  # Retain branches and selected COMPLETE leaves, enlarging the distant leaf sprays.
  verts=[];faces=[];mats=[];uvs=[];polys=list(data.polygons);i=0;leaf=0
  while i<len(polys):
   group=polys[i:i+8] if polys[i].material_index==1 else [polys[i]]
   keep=polys[i].material_index==0 or leaf%16==0
   if polys[i].material_index==1:leaf+=1
   if keep:
    ids=[v for p in group for v in p.vertices];center=sum((data.vertices[v].co for v in ids),Vector())/len(ids)
    for p in group:
     start=len(verts)
     for li in p.loop_indices:
      v=data.vertices[data.loops[li].vertex_index].co
      verts.append(tuple(center+(v-center)*(2.7 if p.material_index==1 else 1)));uvs.append(tuple(data.uv_layers.active.data[li].uv))
     faces.append(tuple(range(start,len(verts))));mats.append(p.material_index)
   i+=len(group)
  mesh=bpy.data.meshes.new(data.name+'_distant');mesh.from_pydata(verts,[],faces);mesh.update()
  for m in data.materials:mesh.materials.append(m)
  uv=mesh.uv_layers.new(name='Botanical_UV')
  for p,mi in zip(mesh.polygons,mats):
   p.material_index=mi;p.use_smooth=True
   for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
 else:
  tmp=bpy.data.objects.new('LOD_work',data.copy());scene.collection.objects.link(tmp);bpy.context.view_layer.objects.active=tmp
  dec=tmp.modifiers.new('Distant plant simplification','DECIMATE');dec.ratio=.16;bpy.ops.object.modifier_apply(modifier=dec.name)
  mesh=tmp.data;bpy.data.objects.remove(tmp,do_unlink=True)
 low[data]=mesh
 print('LOD geometry ready',data.name,len(mesh.polygons),flush=True)
for o in objects:
 tree=o.data.name in ['Botanical_spreading','Botanical_rounded','Botanical_column']
 o['vegetation_lod']='near';o['vegetation_distance']=80 if tree else 28
 other=o.copy();other.data=low[o.data];other.name='distant_'+o.name;other['vegetation_lod']='far';other.hide_render=True;scene.collection.objects.link(other)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/naju-arboretum.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
metrics=json.loads((R/'knowledge/sources/arboretum/botanical-metrics.json').read_text());metrics.update(glb_bytes=out.stat().st_size,compressed_bytes=Path(str(out)+'.gz').stat().st_size,detail_distances={'trees':80,'flowers_hedges':28},note='Blender authored near/far variants. Three.js instances matching 48m tree cells and 24m flower cells. Browser FPS not measured.')
(R/'knowledge/sources/arboretum/botanical-metrics.json').write_text(json.dumps(metrics,indent=2))
print('BOTANICAL LOD COMPLETE',flush=True)
