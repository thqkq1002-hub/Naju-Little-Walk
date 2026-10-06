"""Preserve the artist source; trim the screenshot's north background in Blender.

The crop is a presentation boundary, not a change to the actual river geography.
Use --export-only to re-export an already saved crop without editing its source.
"""
import bpy,bmesh,json,math,sys,hashlib,gzip,struct
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
C=R/'outputs/yeongsanpo-crop-v90';C.mkdir(parents=True,exist_ok=True)
S=R/'outputs/yeongsanpo-v79/yeongsanpo-detail-v79.blend'
TARGET=C/('yeongsanpo-north-crop-v90b.blend' if '--bank-repair' in sys.argv else 'yeongsanpo-north-crop-v90.blend');CUT=-230.0
WEST_A=(-71.66395292358195,-175.19541600030436)
WEST_B=(-157.10627877825942,-145.6176920003128)
WEST_N=(-(WEST_B[1]-WEST_A[1]),WEST_B[0]-WEST_A[0])
REPORT=R/'knowledge/sources/yeongsanpo-crop-v90.json'
def save_json(path,value,compact=False):
 temp=path.with_suffix(path.suffix+'.writing-v90');temp.write_text(json.dumps(value,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)+'\n',encoding='utf8');temp.replace(path)
def clip(poly):
 result=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia=a[1]>=CUT;ib=b[1]>=CUT
  if ia:result.append(a)
  if ia!=ib:
   t=(CUT-a[1])/(b[1]-a[1]);result.append([a[0]+t*(b[0]-a[0]),CUT])
 return result
def half_clip(poly,a,n):
 out=[]
 def side(p):return (p[0]-a[0])*n[0]+(p[1]-a[1])*n[1]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  sp,sq=side(p),side(q);ip,iq=sp<=1e-7,sq<=1e-7
  if ip:out.append(p)
  if ip!=iq:
   t=sp/(sp-sq);out.append([p[k]+t*(q[k]-p[k]) for k in (0,1)])
 return out
def road_clip(points,west=False):
 def side(p):return (p[0]-WEST_A[0])*WEST_N[0]+(p[1]-WEST_A[1])*WEST_N[1] if west else CUT-p[1]
 parts=[];part=[]
 for a,b in zip(points,points[1:]):
  sa,sb=side(a),side(b);ia=sa<=0;ib=sb<=0
  if not ia and not ib:
   if part:parts.append(part);part=[]
   continue
  if ia!=ib:
   t=sa/(sa-sb);p=[a[k]+t*(b[k]-a[k]) for k in (0,1)]
   a,b=(a,p) if ia else (p,b)
  if not part or math.dist(part[-1],a)>1e-7:part.append(a)
  part.append(b)
  if not ib:parts.append(part);part=[]
 if part:parts.append(part)
 return parts
def extent(scene):
 points=[o.matrix_world@Vector(v) for o in scene.objects if o.type=='MESH' for v in o.bound_box]
 return [min(p.x for p in points),max(p.x for p in points),min(-p.y for p in points),max(-p.y for p in points)]
if '--export-only' not in sys.argv:
 if TARGET.exists():raise RuntimeError('Existing edited revision preserved: choose a new filename')
 source_sha=hashlib.sha256(S.read_bytes()).hexdigest()
 world_path=R/'public/yeongsanpo-world.json';backup=C/'world-before.json'
 before=backup.read_bytes() if backup.exists() else world_path.read_bytes()
 if not backup.exists():backup.write_bytes(before)
 w=json.loads(before)
 bpy.ops.wm.open_mainfile(filepath=str(S));scene=bpy.context.scene;bpy.context.view_layer.update()
 before_extent=extent(scene);removed=[];trimmed=[]
 for o in list(scene.objects):
  if o.type!='MESH':continue
  points=[o.matrix_world@Vector(v) for v in o.bound_box];cx=sum(p.x for p in points)/8;cz=sum(-p.y for p in points)/8
  western='way/303738250' in o.name or (o.name.startswith('bridge_pier') and cx<0 and cz<80) or (o.name.startswith('road_center_mark') and cx<0 and cz<60)
  planes=[(Vector((0,-CUT,0)),Vector((0,1,0)))]
  if western:planes.append((Vector((WEST_A[0],-WEST_A[1],0)),Vector((WEST_N[0],-WEST_N[1],0)).normalized()))
  distances=[[(p-a).dot(n) for p in points] for a,n in planes]
  if o.name.startswith('north_bank_background') or any(min(ds)>=-1e-6 for ds in distances):
   removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
  if all(max(ds)<=1e-6 for ds in distances):continue
  o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
  for v in bm.verts:v.co=o.matrix_world@v.co
  for a,n in planes:
   cut=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,
     plane_co=a,plane_no=n,clear_inner=False,clear_outer=True)
   edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
   if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  inv=o.matrix_world.inverted()
  for v in bm.verts:v.co=inv@v.co
  bm.to_mesh(o.data);bm.free();o.data.update();trimmed.append(o.name)
  if not o.data.polygons:bpy.data.objects.remove(o,do_unlink=True)
 bpy.context.view_layer.update();after_extent=extent(scene)
 assert after_extent[2]>=CUT-.001,after_extent
 solids=[];changed_solids=[];removed_solids=[]
 for s in w['solids']:
  poly=s.get('footprint')
  if poly:
   p=clip(poly)
   if 'way/303738250' in s['name']:p=half_clip(p,WEST_A,WEST_N)
   if len(p)<3:removed_solids.append(s['name']);continue
   if p!=poly:s['footprint']=p;changed_solids.append(s['name'])
  solids.append(s)
 w['solids']=solids;old_bounds=w['bounds'].copy();w['bounds'][2]=CUT
 nav=w['navigationWater']
 for k in ('polygons','obstacles'):
  polys=[]
  for poly in nav[k]:
   p=clip(poly)
   if k=='obstacles' and p and max(v[0] for v in p)<0:p=half_clip(p,WEST_A,WEST_N)
   if len(p)>=3:polys.append(p)
  nav[k]=polys
 roads=[]
 for road in w['roads']:
  parts=road_clip(road['points'])
  if road['id']=='way/303738250':parts=[q for p in parts for q in road_clip(p,west=True)]
  for i,p in enumerate(parts):
   roads.append(dict(road,points=p,**({'croppedPart':i} if i else {})))
 w['roads']=roads
 w['mapCrop']=dict(revision='north-crop-v90',northCutMetres=CUT,reason='User-marked opposite-bank background removed; not a new surveyed geographic boundary.')
 for a in [w['spawn'],*w['arrivals'].values()]:assert a['z']>=CUT
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));save_json(world_path,w,compact=True)
 assert hashlib.sha256(S.read_bytes()).hexdigest()==source_sha
 save_json(REPORT,dict(sourceBlend=str(S.relative_to(R)),sourceSha256=source_sha,sourceUnchanged=True,
   editedBlend=str(TARGET.relative_to(R)),northCutMetres=CUT,oldBounds=old_bounds,newBounds=w['bounds'],
   beforeVisualExtent=before_extent,afterVisualExtent=after_extent,removedObjects=removed,trimmedObjects=trimmed,
   changedSolidNames=changed_solids,removedSolidNames=removed_solids,
   westernBridgeEndBoundary=[WEST_A,WEST_B],westernBridgeBoundarySource='Existing OSM navigationWater polygon edge; remove bridge overhang after opposite-bank background removal.',
   presentationOnly=True,geographicSourceUnmodified=True))
else:
 bpy.ops.wm.open_mainfile(filepath=str(TARGET))
# The established exporter groups by material and spatial zone. Reuse only its
# definitions; never execute the old generation loop or rewrite the v79 source.
exec(compile((R/'scripts/refine_yeongsanpo_v79.py').read_text(encoding='utf8').split('stats=[]')[0],__file__,'exec'))
key='yeongsanpo';scene=bpy.context.scene
for o in scene.objects:
 if any(s in o.name for s in ['_seam','_rib','_grille','_stitch','_mortar','label_','_pull','_hinge']):o['no_shadow']=True
merged=group_scene()
for o in scene.objects:
 if o.type=='MESH':
  coords=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',coords)
  o.data.vertices.foreach_set('co',np.round(coords*10000)/10000);o.data.update()
export=C/'yeongsanpo-web-v90.glb'
bpy.ops.export_scene.gltf(filepath=str(export),export_format='GLB',use_active_scene=True,export_extras=True,
 export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_apply=True)
raw=export.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc.get('materials',[]):
 bm=bpy.data.materials.get(m.get('name',''))
 if bm and bm.name.startswith('Y79_'):
  if 'baseColorTexture' in m.get('pbrMetallicRoughness',{}):m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color) if bm.name!='Y79_leaf_cutout' else [1,1,1,1]
  if bm.name=='Y79_leaf_cutout':m['alphaMode']='MASK';m['alphaCutoff']=.42;m['doubleSided']=True
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0);assert len(packed)<25*1024*1024
for suffix,payload in [('.glb',raw),('.glb.gz',packed)]:
 p=R/f'public/models/yeongsanpo{suffix}';temp=p.with_suffix(p.suffix+'.writing-v90');temp.write_bytes(payload);temp.replace(p)
report=json.loads(REPORT.read_text(encoding='utf8'));report.update(webMeshes=len(doc['meshes']),mergedObjects=merged,
 modelBytes=len(raw),gzipBytes=len(packed),modelSha256=hashlib.sha256(raw).hexdigest())
save_json(REPORT,report);print('CROP_V90',json.dumps({k:v for k,v in report.items() if k not in ['trimmedObjects','removedObjects']}),flush=True)
