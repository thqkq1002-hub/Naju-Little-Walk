"""Remove obsolete guessed access in Blender and export the same new facilities.

Existing district vertex/material streams remain byte-for-byte unchanged. Only
Blender-selected obsolete approach indices are omitted from the two transports.
"""
import bpy,bmesh,json,struct,gzip,hashlib,shutil,math,sys
from mathutils import Matrix
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/bitgaram-v101';K=R/'knowledge/sources/bitgaram/access-v101'
source=R/'outputs/relief-v96/bitgaram-overview-relief-v96b.blend';target=O/('bitgaram-overview-v101b.blend' if '--clear-facilities' in sys.argv else 'bitgaram-overview-v101.blend')
if target.exists():raise RuntimeError('Preserve artist revision')
source_hash=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source))
colors={'a37a53','75644d','9a714b','52615b','6b6556','aa7d50','735a40','8f6948','45524c','f0e5be'}
report=dict(source=str(source.relative_to(R)),sourceSha256=source_hash,output=str(target.relative_to(R)),parts=[])
tree_masks={};cleared_centres=[]
profiles=json.loads((K/'navigation-profiles.json').read_text());routes=[profiles['slide_route'],profiles['outdoor_route']]
def distance(x,z,route):
 best=1e9
 for a,b in zip(route,route[1:]):
  dx,dz=b[0]-a[0],b[2]-a[2];t=max(0,min(1,((x-a[0])*dx+(z-a[2])*dz)/(dx*dx+dz*dz or 1)))
  best=min(best,math.hypot(x-a[0]-t*dx,z-a[2]-t*dz))
 return best
def components(mesh):
 parent=list(range(len(mesh.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for e in mesh.edges:parent[root(e.vertices[1])]=root(e.vertices[0])
 # Join UV/normal seam duplicates for whole crowns, not clipped triangles.
 seen={}
 for v in mesh.vertices:
  key=tuple(round(c,4) for c in v.co)
  if key in seen:parent[root(v.index)]=root(seen[key])
  else:seen[key]=v.index
 groups={}
 for face in mesh.polygons:groups.setdefault(root(face.vertices[0]),[]).append(face.index)
 for faces in groups.values():
  ids={i for f in faces for i in mesh.polygons[f].vertices};pts=[mesh.vertices[i].co for i in ids]
  lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
  yield faces,lo,hi
if '--clear-facilities' in sys.argv:
 greens={'4b6941','6f814c','68874c','799258','7d9467'}
 browns={'776653','84745e','685a48','79684d','846950','7e6e57'}
 for group in (greens,browns):
  for ob in list(bpy.context.scene.objects):
   if ob.type!='MESH' or ':overview_batch_Museum_' not in ob.name:continue
   color=ob.name.split(':overview_batch_Museum_')[1].split(':')[0].split('.')[0]
   if color not in group:continue
   for faces,lo,hi in components(ob.data):
    x=(lo[0]+hi[0])/2;z=-(lo[1]+hi[1])/2;radius=max(hi[0]-lo[0],hi[1]-lo[1])/2
    if not (-48<x<22 and 14<z<116 and .15<radius<8 and hi[2]-lo[2]<20):continue
    hit=min(distance(x,z,r) for r in routes)<radius+1.8 if group is greens else any(math.hypot(x-a,z-b)<2.5 for a,b in cleared_centres)
    if hit:
     tree_masks.setdefault(ob.name,set()).update(faces)
     if group is greens:cleared_centres.append((x,z))
 print('CLEAR_INFERRED_CROWNS',len(cleared_centres),flush=True)
def dump(g,b):
 b+=b'\0'*((-len(b))%4);g['buffers'][0]['byteLength']=len(b);j=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4)
 return struct.pack('<4sII',b'glTF',2,28+len(j)+len(b))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(b),b'BIN\0')+b
for key in ('bitgaram-overview','bitgaram-overview-part2'):
 path=R/f'public/models/{key}.glb';backup=O/(key+'-source-v96.glb')
 if not backup.exists():shutil.copyfile(path,backup)
 raw=backup.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=bytearray(raw[28+n:]);removed=0;changed=[];before_total=0
 for node in g['nodes']:
  if 'mesh' not in node:continue
  name=node.get('name','')
  for pi,prim in enumerate(g['meshes'][node['mesh']]['primitives']):
   acc=g['accessors'][prim['indices']];before_total+=acc['count']//3
   old_access=name.startswith('overview_batch_Museum_') and name.removeprefix('overview_batch_Museum_').split('.')[0] in colors
   if not old_access and f'{key}:{name}:{pi}' not in tree_masks:continue
   obj=bpy.data.objects.get(f'{key}:{name}:{pi}')
   if obj is None:continue
   drop=set(tree_masks.get(obj.name,set()))
   for face in obj.data.polygons:
    vv=[obj.matrix_world@obj.data.vertices[i].co for i in face.vertices]
    if old_access and all(5.5<p.x<23 and 14.5<-p.y<101 for p in vv):drop.add(face.index)
   if not drop:continue
   assert len(obj.data.polygons)==acc['count']//3 and acc['componentType']==5123
   view=g['bufferViews'][acc['bufferView']];start=view.get('byteOffset',0)+acc.get('byteOffset',0)
   indices=struct.unpack_from('<'+'H'*acc['count'],binary,start);drop_set=set(drop)
   kept=[v for i in range(len(indices)//3) if i not in drop_set for v in indices[3*i:3*i+3]]
   if kept:
    payload=struct.pack('<'+'H'*len(kept),*kept);binary.extend(b'\0'*((-len(binary))%4));vi=len(g['bufferViews']);g['bufferViews'].append(dict(buffer=0,byteOffset=len(binary),byteLength=len(payload),target=34963));binary.extend(payload)
    acc.update(bufferView=vi,byteOffset=0,count=len(kept),min=[min(kept)],max=[max(kept)])
   else:prim['_v101_remove']=True
   bm=bmesh.new();bm.from_mesh(obj.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in drop],context='FACES_ONLY');bm.to_mesh(obj.data);bm.free()
   removed+=len(drop);changed.append(dict(node=name,trianglesRemoved=len(drop)))
 meshmap={};newmeshes=[]
 for i,mesh in enumerate(g['meshes']):
  mesh['primitives']=[p for p in mesh['primitives'] if not p.pop('_v101_remove',False)]
  if mesh['primitives']:meshmap[i]=len(newmeshes);newmeshes.append(mesh)
 for node in g['nodes']:
  if 'mesh' in node:
   if node['mesh'] in meshmap:node['mesh']=meshmap[node['mesh']]
   else:node.pop('mesh')
 g['meshes']=newmeshes
 out=dump(g,binary);assert len(out)<32*1024*1024;path.write_bytes(out);path.with_suffix('.glb.gz').write_bytes(gzip.compress(out,9,mtime=0))
 report['parts'].append(dict(key=key,sourceSha256=hashlib.sha256(raw).hexdigest(),sha256=hashlib.sha256(out).hexdigest(),trianglesBefore=before_total,trianglesRemoved=removed,trianglesAfter=before_total-removed,changed=changed,existingAttributeStreamsPreserved=True))
print('REMOVED_OLD_ACCESS',sum(p['trianglesRemoved'] for p in report['parts']),flush=True)
# Append only Blender-authored facilities from the latest walking revision.
world=json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'));park=R/world['navigationFromBlend']
prefixes=('access101_','walk-floor_access101_','walk-floor_outdoor_timber_stairs','walk-floor_slide_side_stairs','photo_stone_slide','slide_gallery_','mapped_monorail_','monorail_running_strip','monorail_rack_teeth','monorail_support')
with bpy.data.libraries.load(str(park),link=False) as (src,dst):dst.objects=[name for name in src.objects if name.startswith(prefixes)]
added=[]
for ob in dst.objects:
 if ob is not None:bpy.context.scene.collection.objects.link(ob);added.append(ob)
with bpy.data.libraries.load(str(O/'bitgaram-monorail-v101.blend'),link=False) as (src,dst):dst.objects=list(src.objects)
cab=[ob for ob in dst.objects if ob is not None]
a,b=world['monorail']['route'][-2:];yaw=math.atan2(a[0]-b[0],a[2]-b[2]);matrix=Matrix.Translation((b[0],-b[2],b[1]))@Matrix.Rotation(yaw,4,'Z')
for ob in cab:
 bpy.context.scene.collection.objects.link(ob)
 if ob.parent is None:ob.matrix_world=matrix@ob.matrix_world
added.extend(cab)
bpy.ops.object.select_all(action='DESELECT')
for ob in added:ob.select_set(True)
bpy.context.view_layer.objects.active=added[0]
extra=R/'public/models/bitgaram-access-overview.glb';bpy.ops.export_scene.gltf(filepath=str(extra),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False,export_animations=False)
extra.with_suffix('.glb.gz').write_bytes(gzip.compress(extra.read_bytes(),9,mtime=0))
report['facilityObjects']=len(added);report['facilityBytes']=extra.stat().st_size;report['facilityGzipBytes']=extra.with_suffix('.glb.gz').stat().st_size
report['clearedInferredCanopyComponents']=len(cleared_centres)
assert report['facilityGzipBytes']<3*1024*1024
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
(K/'overview.json').write_text(json.dumps(report,indent=2),encoding='utf8')
orbit_path=R/'public/bitgaram-orbit.json';orbit=json.loads(orbit_path.read_text(encoding='utf8'));orbit['accessRevision']='bitgaram-access-v101';orbit_path.write_text(json.dumps(orbit,ensure_ascii=False,indent=2),encoding='utf8')
print('OVERVIEW_V101',json.dumps(report),flush=True)
