"""Author textured surfaces and finer foliage in a new Blender revision."""
import bpy,sys,math,random,gzip,json
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/arboretum';target=O/'naju-arboretum-surface-v6.blend'
if target.exists():raise RuntimeError('Preserve existing revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'naju-arboretum-reference-v4.blend'))
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0);rng=random.Random(921)
def textured(name,base,bark=False):
 n=512;y,x=np.mgrid[0:n,0:n];rr=np.random.default_rng(32 if bark else 64)
 noise=rr.random((n,n))
 if bark:
  v=.72+.14*np.sin(x*.18+2*np.sin(y*.013))+.09*np.sin(x*.71+np.sin(y*.028))+.06*(noise-.5)
 else:
  coarse=rr.random((n,n))
  for _ in range(20):coarse=(coarse+np.roll(coarse,1,0)+np.roll(coarse,-1,0)+np.roll(coarse,1,1)+np.roll(coarse,-1,1))/5
  v=.89+.35*(coarse-.5)+.10*(noise-.5)
 data=np.ones((n,n,4),dtype=np.float32)
 for i,c in enumerate(base):data[:,:,i]=np.clip(c*v,0,1)
 image=bpy.data.images.new(name,width=n,height=n);image.pixels.foreach_set(data.ravel());image.pack()
 mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.93
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 # Tangent normals survive GLB export and bring out grain at walking distance.
 gy,gx=np.gradient(v);normal=np.stack((-gx*3,-gy*3,np.ones_like(v)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
 nd=np.ones((n,n,4),dtype=np.float32);nd[:,:,:3]=normal*.5+.5
 ni=bpy.data.images.new(name+'_normal',width=n,height=n);ni.colorspace_settings.name='Non-Color';ni.pixels.foreach_set(nd.ravel());ni.pack()
 nt=mat.node_tree.nodes.new('ShaderNodeTexImage');nt.image=ni;nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.55 if bark else .18
 mat.node_tree.links.new(nt.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 return mat
bark=textured('Authored_bark_grain',(.38,.29,.20),True);earth=textured('Authored_fine_path',(.64,.59,.48));grass=textured('Authored_meadow',(.34,.43,.24));wood=textured('Authored_timber',(.47,.35,.22),True)
seen=set()
for o in bpy.data.objects:
 if o.type!='MESH' or o.data in seen:continue
 seen.add(o.data)
 if o.name.startswith(('mapped_path_','garden_curved','garden_outer','round_garden_walk')):o.data.materials.clear();o.data.materials.append(earth)
 elif o.name.startswith('ground_campus'):o.data.materials.clear();o.data.materials.append(grass)
 elif o.name.startswith(('bench_seat','bench_back','avenue_deck')):o.data.materials.clear();o.data.materials.append(wood)
 elif o.name.startswith('estimated_'):
  for i,m in enumerate(o.data.materials):
   if m and (m.name.startswith('Museum_705d43') or m.name.startswith('Museum_65513c') or m.name.startswith('Museum_80694b') or m.name.startswith('Museum_917755') or m.name.startswith('Museum_745b40')):o.data.materials[i]=bark
# Replace the broad diamond leaf polygons by tapered, folded, rotated leaves.
meta=next(o for o in bpy.data.objects if o.name.startswith('estimated_meta'));mesh=meta.data
leafslots={i for i,m in enumerate(mesh.materials) if m and any(m.name.startswith('Museum_'+c) for c in ['648342','3f6337','77944a','52753c'])}
# Joined leaf sprays have unique vertices per quad, shared only by its two faces.
indices=set(v for p in mesh.polygons if p.material_index in leafslots for v in p.vertices)
# Each source leaf owns four consecutive vertices. Replace planar blocks with pointed folds.
groups={}
for i in sorted(indices):
 groups.setdefault((i-min(indices))//4,[]).append(i)
for ids in groups.values():
 if len(ids)!=4:continue
 center=sum((mesh.vertices[i].co for i in ids),Vector())/4
 angle=rng.random()*math.tau;u=Vector((math.cos(angle),math.sin(angle),rng.uniform(-.5,.5))).normalized();v=u.cross(Vector((0,0,1))).normalized()
 length=rng.uniform(.18,.28);width=rng.uniform(.055,.09)
 for i,co in zip(ids,[center-u*length,center+v*width+Vector((0,0,.035)),center+u*length,center-v*width]):mesh.vertices[i].co=co
mesh.update()
# Ground-floor detail is combined by material in the web renderer.
def local(s,t):return (-475+s*.98-t*.2,-50+s*.2+t*.98)
verts=[];faces=[]
for _ in range(4400):
 s=rng.uniform(18,427);t=rng.choice([-1,1])*rng.uniform(3.2,6.8);x,z=local(s,t);i=len(verts);r=rng.uniform(.025,.075);a=rng.random()*math.tau
 verts.extend([(x-r,.025,z),(x,.035,z-r*.5),(x+r,.025,z),(x,.04,z+r*.5)]);faces.extend([(i,i+1,i+2),(i,i+2,i+3)])
g.mesh('scattered_leaf_litter',verts,faces,'#8a754a')
# Small stones and low shrubs beside the entry soften the bare verge; positions estimated.
for s in [8,14,20,27,35,48,64]:
 for t in [-8,8]:
  x,z=local(s,t)
  for j in range(3):
   bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=g.bp(x+rng.uniform(-1,1),.25,z+rng.uniform(-.5,.5)))
   o=bpy.context.object;o.name='verge_stone';o.scale=(rng.uniform(.2,.45),rng.uniform(.2,.45),.2);o.data.materials.append(g.mat('#92917b'))
# Wood sign, photo-inspired, with clear pedestrian passage.
x,z=local(18,-7.5);g.box('timber_wayfinding',x,1.55,z,2.4,.8,.14,'#aa9169',record=False)
g.label('메타세쿼이아길',x,1.55,z+.09,2.2,.28,color='#24452d')
scene.eevee.taa_render_samples=32;scene.view_settings.exposure=.5
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));out=R/'public/models/naju-arboretum.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
cam=scene.camera;x,z=local(24,0);tx,tz=local(130,0);cam.location=g.bp(x,1.72,z);cam.rotation_euler=(Vector(g.bp(tx,4,tz))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24
scene.render.filepath=str(O/'surface-avenue.png');bpy.ops.render.render(write_still=True)
print('SURFACE DETAIL COMPLETE',out.stat().st_size)
