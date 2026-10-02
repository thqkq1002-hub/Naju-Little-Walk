"""Correct inferred planting alignment against the retained OSM road; guarded output."""
import bpy,json,math,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];revision='v64' if '--clear-crossings' in sys.argv else 'v63';O=R/('outputs/quality-'+revision);O.mkdir(parents=True,exist_ok=True)
source=R/'outputs/quality-v62/naju-arboretum-junipers-v62.blend';target=O/('naju-arboretum-juniper-avenue-'+revision+'.blend')
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
world_path=R/'public/naju-arboretum-world.json';world=json.loads(world_path.read_text(encoding='utf-8'));world_before=hashlib.sha256(world_path.read_bytes()).hexdigest()
data=json.loads((R/'knowledge/sources/arboretum/geometry.json').read_text(encoding='utf-8'));road=next(w for w in data['ways'] if w['id']=='1258471015')['points']
def local(x,z):return ((.98*(x+475)+.2*(z+50))/1.0004,(-.2*(x+475)+.98*(z+50))/1.0004)
def worldpoint(s,t):return (-475+.98*s-.2*t,-50+.2*s+.98*t)
road_local=[local(*p) for p in road]
def center(s):
 for (a,t),(b,u) in zip(road_local,road_local[1:]):
  if min(a,b)<=s<=max(a,b):return t+(u-t)*(s-a)/(b-a)
 a,t=road_local[-2:][0] if s<road_local[-1][0] else road_local[0];return t
def avenue(s,t):return 47.9<=s<=424.1 and min(abs(t+181),abs(t+169))<.02
crossings=[]
for wid in ['1258471018','1258471019']:
 points=[local(*p) for p in next(w for w in data['ways'] if w['id']==wid)['points']]
 s,t=min(points,key=lambda p:abs(p[1]-center(p[0])))
 if abs(t-center(s))<.1:crossings.append(s)
moved={};old_avenue=[];new_avenue=[]
for o in scene.objects:
 if o.type!='MESH' or o.get('reference_habit') not in ['column','oval']:continue
 x,z=o.location.x,-o.location.y;s,t=local(x,z)
 if not avenue(s,t):continue
 new_s=s
 if revision=='v64':
  for junction in crossings:
   if abs(new_s-junction)<5.5:new_s=junction+(-5.5 if new_s<junction else 5.5)
 side=-1 if abs(t+181)<.02 else 1;new_t=center(new_s)+side*6;nx,nz=worldpoint(new_s,new_t)
 moved[o.name]={'before':[x,z],'after':[nx,nz],'side':side,'s':s,'new_s':new_s,'old_t':t,'new_t':new_t,'matrix_before':[v for row in o.matrix_world for v in row]}
 o.location.x=nx;o.location.y=-nz;o['avenue_alignment']='OSM road 1258471015 centreline; row offset 6m remains photo estimate'
 if o.get('vegetation_lod')=='near':
  old_avenue.append((x,z,o));new_avenue.append((nx,nz))
# Only original avenue trunk proxies are changed. Remove independently identified ghosts.
updated=[];removed=[];solids=[]
for solid in world['solids']:
 if solid['name']!='tree_trunk':solids.append(solid);continue
 x,z=solid['position'][0],solid['position'][2];s,t=local(x,z)
 if not avenue(s,t):solids.append(solid);continue
 match=next(((tx,tz,o) for tx,tz,o in old_avenue if math.hypot(tx-x,tz-z)<.02),None)
 if match is None:removed.append(solid);continue
 o=match[2];item=moved[o.name];new=json.loads(json.dumps(solid));new['position'][0],new['position'][2]=item['after']
 # Dense low foliage is physical: conservative horizontal crown radius at walking level.
 r=max(math.hypot(v.co.x*o.scale.x,v.co.y*o.scale.y) for v in o.data.vertices)
 new['size'][0]=new['size'][2]=round(r*2,5);new['reference']='Inferred juniper envelope aligned to mapped road; dimensions estimated'
 solids.append(new);updated.append({'before':solid,'after':new,'tree':o.name})
assert len(old_avenue)==91 and len(updated)==91 and len(removed)==5,'Review the changed source inventory'
world['solids']=solids
# Named arrival uses the actual mapped centreline and follows the road into the campus.
s=120;t=center(s);x,z=worldpoint(s,t);a,b=road[1],road[0];yaw=math.atan2(-(b[0]-a[0]),-(b[1]-a[1]))
world.setdefault('arrivals',{})['juniper']={'x':x,'z':z,'yaw':yaw}
world['places']=[dict(p,position=[x,z],arrival=[x,z]) if p['id']=='juniper' else p for p in world['places']]
def material(name,rgb):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1);bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.9;return m
asphalt=material('Avenue_fine_asphalt',(.16,.17,.175));n=256;rr=np.random.default_rng(630);field=rr.random((n,n));low=field.copy()
for _ in range(15):low=(low+np.roll(low,1,0)+np.roll(low,-1,0)+np.roll(low,1,1)+np.roll(low,-1,1))/5
value=.84+.22*field+.18*(low-.5);pixels=np.ones((n,n,4),np.float32)
for i,c in enumerate([.16,.17,.175]):pixels[:,:,i]=c*value
im=bpy.data.images.new('Avenue_asphalt_authored_color',width=n,height=n);im.pixels.foreach_set(pixels.ravel());im.pack();tex=asphalt.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;asphalt.node_tree.links.new(tex.outputs['Color'],asphalt.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
gx=np.roll(value,-1,1)-np.roll(value,1,1);gy=np.roll(value,-1,0)-np.roll(value,1,0);normal=np.stack([-gx*.5,-gy*.5,np.ones_like(gx)],axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True);pixels[:,:,:3]=normal*.5+.5
im=bpy.data.images.new('Avenue_asphalt_authored_normal',width=n,height=n);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(pixels.ravel());im.pack();tex=asphalt.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;nm=asphalt.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.23;asphalt.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);asphalt.node_tree.links.new(nm.outputs['Normal'],asphalt.node_tree.nodes['Principled BSDF'].inputs['Normal'])
roads=[]
for o in scene.objects:
 if o.type!='MESH' or not o.name.startswith('mapped_path_1258471015'):continue
 # Original road geometry and elevation stay exact; only material and metre UV change.
 o.data.materials.clear();o.data.materials.append(asphalt)
 for face in o.data.polygons:face.material_index=0
 uv=o.data.uv_layers.active
 for loop in o.data.loops:
  p=o.matrix_world@o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(p.x*2,p.y*2)
 roads.append(o.name)
# Reduce the stretched horizontal noise only on the new evergreen cores.
core=bpy.data.materials['Reference_dense_foliage'].copy();core.name='Clipped_juniper_dense_veins';bs=core.node_tree.nodes['Principled BSDF']
for node in core.node_tree.nodes:
 if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.16
new_meshes={o.data for o in scene.objects if o.type=='MESH' and o.get('juniper_revision')}
for mesh in new_meshes:
 mesh.materials[1]=core
 layer=mesh.uv_layers.active
 for face in mesh.polygons:
  if face.material_index!=1:continue
  for li in face.loop_indices:
   u,v=layer.data[li].uv;layer.data[li].uv=(u*12,v*5)
markers=[];yellow=material('Avenue_photo_yellow_line',(.57,.39,.07));white=material('Avenue_photo_white_edge',(.66,.66,.60))
def stripe(name,a,b,offset,width,mat):
 a,b=Vector(a),Vector(b);direction=(b-a).normalized();side=Vector((-direction.y,direction.x));a+=side*offset;b+=side*offset
 pts=[a-side*width/2,b-side*width/2,b+side*width/2,a+side*width/2]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(p.x,-p.y,.106) for p in pts],[],[(3,2,1,0)]);mesh.materials.append(mat);mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o['reference']='Line appearance from 2021 visit photo; width estimated';markers.append(o.name)
for i,(a,b) in enumerate(zip(road,road[1:])):
 stripe('juniper_yellow_centre_'+str(i),a,b,0,.12,yellow)
 for sign in [-1,1]:stripe('juniper_white_edge_'+str(i)+'_'+str(sign),a,b,sign*1.79,.10,white)
bpy.context.view_layer.update()
report={'source':str(source.relative_to(R)),'output':str(target.relative_to(R)),'moved_trees':moved,'updated_colliders':updated,'removed_ghost_colliders':removed,'road_material_objects':roads,'new_markings':markers,'road_source_id':'1258471015','mapped_crossings_s':crossings,'world_before_sha256':world_before,'world_output':str((O/('naju-arboretum-world-'+revision+'.json')).relative_to(R)),'reference':'https://hangamja.tistory.com/1607','limitation':'Retained OSM road centreline; planting offsets, species, dimensions and current marking condition remain estimates.'}
(O/('naju-arboretum-world-'+revision+'.json')).write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(R/('knowledge/sources/arboretum/juniper-avenue-'+revision+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));bpy.ops.export_scene.gltf(filepath=str(O/('naju-arboretum-'+revision+'.glb')),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False,export_animations=False)
print('ALIGNED JUNIPERS',len(old_avenue),len(updated),len(removed),len(roads),flush=True)
