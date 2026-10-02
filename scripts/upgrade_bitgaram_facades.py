"""Replace schematic apartment ribbons with coherent individual window stacks in Blender."""
import bpy,sys,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector
import numpy as np

R=Path(__file__).resolve().parents[1];S=R/'knowledge/sources/bitgaram';O=R/'outputs/quality-v60'
O.mkdir(parents=True,exist_ok=True)
target=O/'bitgaram-apartment-facades-v60.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
sys.path.insert(0,str(R/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/bitgaram/bitgaram-color-detail-v9.blend'))
scene=bpy.context.scene

# Reuse the current published palette rather than reverting to the older v9 paint.
palette={}
for name in ['bitgaram-overview','bitgaram-overview-part2']:
 raw=(R/'public/models'/(name+'.glb')).read_bytes();size=struct.unpack_from('<I',raw,12)[0]
 gltf=json.loads(raw[20:20+size]);palette.update({m['name']:m for m in gltf['materials']})
synced=0
for mat in bpy.data.materials:
 current=palette.get(mat.name)
 if not current:continue
 pbr=current.get('pbrMetallicRoughness',{});color=pbr.get('baseColorFactor',[1,1,1,1]);mat.diffuse_color=color
 bsdf=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
 if bsdf:
  bsdf.inputs['Base Color'].default_value=color
  bsdf.inputs['Roughness'].default_value=pbr.get('roughnessFactor',1)
  bsdf.inputs['Metallic'].default_value=pbr.get('metallicFactor',1)
 synced+=1

def triangles():return sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH')
before_triangles=triangles()

def fingerprint(obj):
 mesh=obj.data;vertices=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',vertices)
 indices=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',indices)
 lengths=np.empty(len(mesh.polygons),dtype=np.int32);mesh.polygons.foreach_get('loop_total',lengths)
 return hashlib.sha256(vertices.tobytes()+indices.tobytes()+lengths.tobytes()+np.asarray(obj.matrix_world,dtype=np.float64).tobytes()).hexdigest()

ways={}
for name in ['geometry.json','district-2026-09-20.json']:
 ways.update({w['id']:w for w in json.loads((S/name).read_text(encoding='utf-8'))['ways']})
completion=json.loads((S/'district-completion-metrics.json').read_text(encoding='utf-8'))
known_heights={str(b['id']):b['height'] for b in completion['buildings']}
apartments=[]
for ident,w in ways.items():
 if 'apartment' not in w['tags'].get('building',''):continue
 body=bpy.data.objects.get('building_'+ident)
 height=max((body.matrix_world@v.co).z for v in body.data.vertices) if body and body.type=='MESH' else known_heights.get(ident)
 if not height:continue
 poly=w['points'][:-1] if w['points'][0]==w['points'][-1] else w['points']
 levels=w['tags'].get('building:levels','')
 apartments.append(dict(id=ident,polygon=poly,height=height,levels=int(levels) if str(levels).isdigit() else None,estimated_footprint=False))
for b in json.loads((S/'district-block-infill-metrics.json').read_text(encoding='utf-8'))['buildings']:
 if 'apartment' in b['kind']:apartments.append(dict(id=str(b['id']),polygon=b['polygon'],height=b['height'],levels=None,estimated_footprint=True))

def segment_distance(x,y,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
 t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/den)) if den else 0
 return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)

# Index original footprints; only replace components within 0.7m of their facade.
grid={}
for i,b in enumerate(apartments):
 p=b['polygon'];xs=[q[0] for q in p];zs=[q[1] for q in p]
 for x in range(math.floor((min(xs)-1)/100),math.floor((max(xs)+1)/100)+1):
  for z in range(math.floor((min(zs)-1)/100),math.floor((max(zs)+1)/100)+1):grid.setdefault((x,z),[]).append(i)

def at_apartment(center):
 x,z,height=center.x,-center.y,center.z;best=None;distance=.7
 for i in grid.get((math.floor(x/100),math.floor(z/100)),[]):
  b=apartments[i]
  if height<2 or height>b['height']+.5:continue
  p=b['polygon'];d=min(segment_distance(x,z,a,c) for a,c in zip(p,p[1:]+p[:1]))
  if d<distance:best=i;distance=d
 return best

changed=[];active=set();removed={'ribbons':0,'panes':0,'sills':0}
for obj in list(scene.objects):
 if obj.type!='MESH' or not obj.name.startswith('district_#'):continue
 key=obj.name.split('#')[1].split('.')[0]
 category='ribbons' if key in ['66838b','78959a'] else 'panes' if key in ['63828d','96aeb2','758e98'] else 'sills' if key=='dce0d7' else None
 if not category:continue
 mesh=obj.data;parent=list(range(len(mesh.vertices)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for face in mesh.polygons:
  ids=list(face.vertices);root=find(ids[0])
  for i in ids[1:]:parent[find(i)]=root
 groups={}
 for i in range(len(parent)):groups.setdefault(find(i),[]).append(i)
 drop=set()
 for root,ids in groups.items():
  center=sum((obj.matrix_world@mesh.vertices[i].co for i in ids),Vector())/len(ids)
  apartment=at_apartment(center)
  if apartment is not None:
   drop.add(root);active.add(apartment);removed[category]+=1
 if not drop:continue
 kept=[i for i in range(len(parent)) if find(i) not in drop];index={old:new for new,old in enumerate(kept)}
 faces=[p for p in mesh.polygons if find(p.vertices[0]) not in drop]
 new=bpy.data.meshes.new(mesh.name+'_apartment_trim');new.from_pydata([mesh.vertices[i].co for i in kept],[],[tuple(index[i] for i in p.vertices) for p in faces])
 for material in mesh.materials:new.materials.append(material)
 for old,newface in zip(faces,new.polygons):newface.material_index=old.material_index;newface.use_smooth=old.use_smooth
 new.update();obj.data=new;changed.append(obj.name)
print('Removed apartment components',removed,'buildings',len(active),flush=True)

def linear(hex):
 rgb=[int(hex[i:i+2],16)/255 for i in [1,3,5]]
 return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]

def material(name,color,roughness,metal):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;rgba=(*linear(color),1);mat.diffuse_color=rgba
 bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=rgba;bsdf.inputs['Roughness'].default_value=roughness;bsdf.inputs['Metallic'].default_value=metal
 mat.use_backface_culling=True
 return mat

glass=[material('Apartment_glass_stack_'+str(i),color,.43,.08) for i,color in enumerate(['#76868a','#7e8e90','#6d7d82'])]
frame=material('Apartment_pale_window_reveal','#c6cbc5',.82,0)
parts={m.name:(m,[],[]) for m in glass+[frame]}
window_count=0;placements=[]
def quad(mat,verts):
 _,vs,fs=parts[mat.name];offset=len(vs);vs.extend(verts);fs.append(tuple(offset+i for i in range(4)))

for index in sorted(active):
 b=apartments[index];p=b['polygon'];height=b['height'];area=sum(a[0]*c[1]-c[0]*a[1] for a,c in zip(p,p[1:]+p[:1]))
 levels=b['levels'] or max(2,round(height/3.2));step=height/levels
 if not 2.5<=step<=4.5:levels=max(2,round(height/3.2));step=height/levels
 seed=int(b['id']);count=0;edges=[]
 for edge,(a,c) in enumerate(zip(p,p[1:]+p[:1])):
  length=math.dist(a,c)
  if length<6:continue
  ux,uz=(c[0]-a[0])/length,(c[1]-a[1])/length;nx,nz=(uz,-ux) if area>0 else (-uz,ux)
  columns=max(1,math.floor((length-3)/4.5));gap=(length-3)/columns;width=min(2.05,gap*.62)
  # Gable faces have fewer narrow stacks; elevations keep their existing envelope.
  if length<16:columns=max(1,math.floor((length-3)/5.5));gap=(length-3)/columns;width=min(1.55,gap*.5)
  pane_height=min(1.55,step*.50);edge_windows=0
  for col in range(columns):
   distance=1.5+gap*(col+.5);cx,cz=a[0]+ux*distance+nx*.14,a[1]+uz*distance+nz*.14
   mat=glass[(seed+edge+col//3)%len(glass)]
   for floor in range(1,levels):
    y=floor*step+.58
    if y+pane_height>height-.7:continue
    def vertex(horizontal,vertical):return (cx+ux*horizontal,-cz-uz*horizontal,vertical)
    def face(mat,l,r,bottom,top):
     # Correct exterior winding for both orientations of the original mapped polygon.
     vs=[vertex(l,bottom),vertex(r,bottom),vertex(r,top),vertex(l,top)]
     if area>0:vs.reverse()
     quad(mat,vs)
    left,right=-width/2,width/2;thickness=.10
    face(mat,left,right,y,y+pane_height)
    # Four coplanar border strips surround an open center: no stacked planes or z-fighting.
    face(frame,left-thickness,left,y-thickness,y+pane_height+thickness)
    face(frame,right,right+thickness,y-thickness,y+pane_height+thickness)
    face(frame,left,right,y-thickness,y)
    face(frame,left,right,y+pane_height,y+pane_height+thickness)
    count+=1;edge_windows+=1
  edges.append(dict(edge=edge,length=length,columns=columns,windows=edge_windows))
 placements.append(dict(**b,display_levels=levels,levels_source='OSM building:levels' if b['levels']==levels else 'estimated from retained model height',windows=count,edges=edges,facade_details='estimated repeated window modules; not a surveyed window schedule'))
 window_count+=count
for name,(mat,verts,faces) in parts.items():
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(mat);mesh.update()
 obj=bpy.data.objects.new('apartment_finish_'+name,mesh);scene.collection.objects.link(obj)

protected={o.name:fingerprint(o) for o in scene.objects if o.type=='MESH' and o.name not in changed and not o.name.startswith('apartment_finish_')}
after_triangles=triangles()
report={'source':'outputs/bitgaram/bitgaram-color-detail-v9.blend','output':str(target.relative_to(R)),'palette_snapshot':palette,'palette_materials_synced':synced,'changed_existing_meshes':changed,'protected_geometry_hashes':protected,'removed_components':removed,'apartments':placements,'new_windows':window_count,'polygon_triangle_estimates':{'before':before_triangles,'after':after_triangles},'reference':'User drone frame work/observatory-video/0-1.png and Naju-provided aerial photo in Seoul newspaper 2025-09-19; photo acquisition date unknown. Window module sizes and colours remain estimates.'}
(S/'district-facade-v60.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

# Identical neutral daylight cameras, before/after are rendered by a separate comparison script.
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.6
bpy.ops.wm.save_as_mainfile(filepath=str(target))
from blender_static_batch import batch
batch(scene)
bpy.ops.export_scene.gltf(filepath=str(O/'bitgaram-overview-full-v60.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
raw=(O/'bitgaram-overview-full-v60.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+size])
report['export_triangles']={'after':sum(gltf['accessors'][p['indices']]['count']//3 for m in gltf['meshes'] for p in m['primitives'])}
(S/'district-facade-v60.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('APARTMENT FINISH',len(active),window_count,before_triangles,after_triangles,flush=True)
