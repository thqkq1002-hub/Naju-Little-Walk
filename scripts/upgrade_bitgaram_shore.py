"""Replace only cell-based visual lawn and short raised bank pieces in a new revision."""
import bpy,json,hashlib,sys,math,random
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from museum_geometry import MuseumGeometry
O=R/'outputs/quality-v75';TARGET=O/'bitgaram-shore-v75.blend'
if TARGET.exists():raise RuntimeError('Existing artist revision preserved')
SOURCE=R/'outputs/quality-v69/bitgaram-access-v69.blend'
data=json.loads((O/'shore-surface-v75.json').read_text(encoding='utf8'))
world=R/'public/bitgaram-park-world.json';world_hash=hashlib.sha256(world.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
def fingerprint(o):
 m=o.data;v=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',v);ids=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ids);lengths=np.empty(len(m.polygons),np.int32);m.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(v.tobytes()+ids.tobytes()+lengths.tobytes()+np.asarray(o.matrix_world,np.float64).tobytes()).hexdigest()
remove=[o for o in scene.objects if o.name=='surrounding_park_lawn' or o.name.startswith('mapped_lake_bank')]
assert len(remove)==109,len(remove)
removed_names=[o.name for o in remove]
protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in removed_names}
before_triangles=sum(len(o.data.polygons) for o in remove)
for o in remove:bpy.data.objects.remove(o,do_unlink=True)
g=MuseumGeometry(scene,(0,0),0)
mesh=g.mesh('mapped_park_lawn_shore_v75',data['vertices'],data['faces'],'#a8b886',group='01_OSM_Envelope')
mesh['osm_park_id']='508048299';mesh['visual_context_only']=True;mesh['cast_shadow']=False;mesh['receive_shadow']=False
if hasattr(mesh,'visible_shadow'):mesh.visible_shadow=False
# Own procedural grass/earth detail. No downloaded reference pixels.
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def texture(name,colors,scale):
 size=256;image=bpy.data.images.new(name,width=size,height=size);pixels=[];rng=random.Random(75002+scale)
 for j in range(size):
  for i in range(size):
   # Periodic low frequency variation and restrained grain; no square cell boundary.
   u,v=i/size*math.tau,j/size*math.tau
   w=.5+.12*math.sin(3*u+math.cos(2*v))+.1*math.sin(2*v+math.sin(u))+.06*math.cos(7*u-5*v)+rng.uniform(-.035,.035)
   w=max(0,min(1,w));pixels.extend([linear(colors[0][k]*(1-w)+colors[1][k]*w) for k in range(3)]+[1])
 image.pixels.foreach_set(pixels);image.pack();mat=bpy.data.materials.new(name);mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.91
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 return mat
lawn=texture('Authored_park_grass_v75',[[.60,.68,.45],[.69,.73,.54]],0)
bank=texture('Authored_park_grass_earth_bank_v75',[[.44,.46,.31],[.62,.63,.44]],1)
mesh.data.materials.clear();mesh.data.materials.append(lawn);mesh.data.materials.append(bank)
uv=mesh.data.uv_layers.active
for p,mi in zip(mesh.data.polygons,data['material_indices']):
 p.material_index=mi
 for li in p.loop_indices:
  co=mesh.data.vertices[mesh.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x/18,co.y/18)
after={o.name:fingerprint(o) for o in scene.objects if o.name in protected};assert after==protected
assert hashlib.sha256(world.read_bytes()).hexdigest()==world_hash
report={'source':str(SOURCE.relative_to(R)),'output':str(TARGET.relative_to(R)),'removed_objects':removed_names,'protected_geometry':protected,'protected_meshes':len(protected),'old_surface_triangles':before_triangles,'new_surface_triangles':len(data['faces']),'world_sha256':world_hash,'geometry_source_sha256':data['source_sha256'],'mapped_land_area':data['mapped_land_area'],'visual_context_only':True,'texture_method':'Own periodic procedural color grain, observation reference only','shore_width_estimate':data['shore_width_estimate'],'shore_height_estimate':data['shore_height_estimate']}
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.export_scene.gltf(filepath=str(O/'bitgaram-park-v75.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(R/'knowledge/sources/bitgaram/shore-v75.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('SHORE AUTHOR',json.dumps({k:v for k,v in report.items() if k not in ['protected_geometry','removed_objects']},ensure_ascii=False),flush=True)
