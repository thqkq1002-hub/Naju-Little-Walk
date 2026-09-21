"""Replace draft hill primitives with a continuous west-bank wooded ridge."""
import bpy,sys,math,json,struct,gzip,random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from museum_geometry import MuseumGeometry
R=Path(__file__).resolve().parents[1];O=R/'outputs/deudeulgang';target=O/'deudeulgang-pine-grove-v3.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(O/'deudeulgang-pine-grove-v2.blend'))
scene=bpy.context.scene;g=MuseumGeometry(scene,(0,0),0)
for o in list(scene.objects):
 if o.name.startswith('estimated_west_hills'):bpy.data.objects.remove(o,do_unlink=True)
def height(x,z):
 edge=max(0,min(1,(-x-194)/110));peaks=24+32*math.exp(-((z+220)/240)**2)+38*math.exp(-((z-260)/220)**2)
 return edge*(peaks+5*math.sin(z/53+x/70)+3*math.sin(z/27-x/61))-.09
verts=[];faces=[];nx,nz=29,91
for j in range(nz):
 for i in range(nx):
  x=-600+i*14.5;z=-680+j*15;verts.append((x,height(x,z),z))
for j in range(nz-1):
 for i in range(nx-1):
  n=j*nx+i;faces.append((n,n+1,n+1+nx,n+nx))
g.mesh('estimated_continuous_west_ridge',verts,faces,'#506e46',smooth=True)
g.collider('background_ridge_boundary',[(-600,-680),(-194,-680),(-194,670),(-600,670)],-10,130)
world_path=R/'public/deudeulgang-world.json';world=json.loads(world_path.read_text(encoding='utf-8'))
world['solids']=[s for s in world['solids'] if s['name']!='background_ridge_boundary']+g.solids
world_path.write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
rr=random.Random(820);source=next(o for o in scene.objects if o.name.startswith('distant_pine_'))
for i in range(170):
 x=rr.uniform(-490,-230);z=rr.uniform(-360,410);o=source.copy();o.name='west_bank_background_pine';scene.collection.objects.link(o);o.location=g.bp(x,height(x,z),z);scale=rr.uniform(.55,.95);o.scale=(scale,scale,scale);o.rotation_euler.z=rr.random()*math.tau;o.hide_render=False
 if 'vegetation_lod' in o:del o['vegetation_lod']
 if 'vegetation_distance' in o:del o['vegetation_distance']
scene.camera.location=g.bp(-260,290,420);scene.camera.rotation_euler=(Vector(g.bp(-10,0,35))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=38
bpy.ops.wm.save_as_mainfile(filepath=str(target))
out=R/'public/models/deudeulgang.glb';bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,use_visible=False,use_renderable=False)
blob=out.read_bytes();n=struct.unpack_from('<I',blob,12)[0];d=json.loads(blob[20:20+n]);tail=blob[20+n:]
for m in d['materials']:
 if m.get('name')=='Pine_needles_alpha_clip':m['alphaMode']='MASK';m['alphaCutoff']=.48;m['doubleSided']=True
j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail)
with gzip.open(str(out)+'.gz','wb',compresslevel=9) as f:f.write(out.read_bytes())
p=R/'knowledge/sources/deudeulgang/metrics.json';d=json.loads(p.read_text());d.update(background_pines=170,glb_bytes=out.stat().st_size,gzip_bytes=Path(str(out)+'.gz').stat().st_size);p.write_text(json.dumps(d,indent=2))
scene.render.filepath=str(O/'overview-v3.png');bpy.ops.render.render(write_still=True)
scene.camera.location=g.bp(-28,1.72,15);scene.camera.rotation_euler=(Vector(g.bp(-130,7,70))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=26
scene.render.filepath=str(O/'riverside-v3.png');bpy.ops.render.render(write_still=True)
print('RIVERBANK FINISH COMPLETE',flush=True)
