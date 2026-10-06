"""Same tree envelopes: detailed leaves near the visitor, solid silhouettes at distance."""
import bpy,bmesh,math,json,struct,gzip,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/dasi-v80'
helper=(R/'scripts/refine_yeongsanpo_v79.py').read_text(encoding='utf-8').split('stats=[]')[0]
exec(compile(helper,__file__,'exec'));O=R/'outputs/dasi-v80';key='dasi'
source=R/'outputs/palette-v51/dasi-neighborhood-color-v51.blend'
bpy.ops.wm.open_mainfile(filepath=str(O/'dasi-neighborhood-detail-v80.blend'));scene=bpy.context.scene
leaf=bpy.data.objects.get('dasi_v80_leaf_canopies')
groups={};far_groups={}
if leaf:
    m=leaf.data.materials[0]
    for p in leaf.data.polygons:
        vv=[leaf.matrix_world@leaf.data.vertices[i].co for i in p.vertices]
        c=sum(vv,Vector())/len(vv);cell=(math.floor(c.x/48),math.floor(-c.y/48))
        groups.setdefault(cell,Batch('dasi_v80_leaves_near_'+str(cell),m)).add([tuple(v) for v in vv],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)])
    bpy.data.objects.remove(leaf,do_unlink=True)
    far=bpy.data.materials.new('D80_distant_canopy');far.use_nodes=True;far.diffuse_color=(*linear((.36,.48,.25)),1)
    bs=far.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=far.diffuse_color;bs.inputs['Roughness'].default_value=.98
    with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('tree-crown_')]
    source_objects=[]
    for o in b.objects:
        if not o or o.type!='MESH':continue
        vv=[o.matrix_world@v.co for v in o.data.vertices];c=sum(vv,Vector())/len(vv);cell=(math.floor(c.x/48),math.floor(-c.y/48))
        batch=far_groups.setdefault(cell,Batch('dasi_v80_canopies_far_'+str(cell),far))
        batch.add([tuple(v) for v in vv],[tuple(p.vertices) for p in o.data.polygons]);source_objects.append(o)
    bpy.data.batch_remove(source_objects)
    def cell_origin(ob,cell,lod):
        origin=Vector(((cell[0]+.5)*48,-(cell[1]+.5)*48,0))
        for v in ob.data.vertices:v.co-=origin
        ob.location=origin;ob['authored_vegetation']=True;ob['vegetation_lod']=lod;ob['vegetation_distance']=90
        ob['no_receive_shadow']=True
        for p in ob.data.polygons:p.use_smooth=True
    for cell,batch in groups.items():cell_origin(batch.finish(leaf=True,shadow=True),cell,'near')
    for cell,batch in far_groups.items():cell_origin(batch.finish(shadow=True),cell,'far')
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'dasi-neighborhood-detail-v80.blend'))
else:
    groups={o.name:o for o in scene.objects if o.get('vegetation_lod')=='near'}
    far_groups={o.name:o for o in scene.objects if o.get('vegetation_lod')=='far'}
    assert groups and far_groups,'Expected an unfinalized scene or an existing vegetation LOD scene'
# Library-linked objects need a dependency-graph update before reading matrix_world.
# Rebuild only the distant display from the original placed canopies, never at origin.
bpy.data.batch_remove([o for o in scene.objects if o.get('vegetation_lod')=='far'])
far=bpy.data.materials.get('D80_distant_canopy');far_groups={}
with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('tree-crown_')]
source_objects=[o for o in b.objects if o and o.type=='MESH']
for o in source_objects:scene.collection.objects.link(o)
bpy.context.view_layer.update()
for o in source_objects:
    vv=[o.matrix_world@v.co for v in o.data.vertices];c=sum(vv,Vector())/len(vv);cell=(math.floor(c.x/48),math.floor(-c.y/48))
    far_groups.setdefault(cell,Batch('dasi_v80_canopies_far_'+str(cell),far)).add([tuple(v) for v in vv],[tuple(p.vertices) for p in o.data.polygons])
bpy.data.batch_remove(source_objects)
for cell,batch in far_groups.items():
    ob=batch.finish(shadow=True);origin=Vector(((cell[0]+.5)*48,-(cell[1]+.5)*48,0))
    for v in ob.data.vertices:v.co-=origin
    ob.location=origin;ob['authored_vegetation']=True;ob['vegetation_lod']='far';ob['vegetation_distance']=90;ob['no_receive_shadow']=True
    for p in ob.data.polygons:p.use_smooth=True
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(O/'dasi-neighborhood-detail-v80.blend'))
code=(R/'scripts/refine_dasi_v80.py').read_text(encoding='utf-8')
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return Vector([min(v[i] for v in pts) for i in range(3)]),Vector([max(v[i] for v in pts) for i in range(3)])
exec(compile(code[code.index('def batch_web():'):code.index('merged=batch_web();')],__file__,'exec'))
merged=batch_web();webobjects=sum(o.type=='MESH' for o in scene.objects)
target=O/'dasi-neighborhood-web-v80.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_apply=True)
raw=target.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc.get('materials',[]):
    bm=bpy.data.materials.get(m.get('name',''))
    if bm and bm.name.startswith('D80_'):
        if 'baseColorTexture'in m.get('pbrMetallicRoughness',{}):m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color)
        if bm.name.endswith('_cutout'):m['alphaMode']='MASK';m['alphaCutoff']=.42;m['doubleSided']=True;m['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,1]
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary;packed=gzip.compress(raw,9,mtime=0)
assert len(packed)<12*1024*1024
for suffix,payload in [('.glb',raw),('.glb.gz',packed)]:(R/f'public/models/dasi-neighborhood{suffix}').write_bytes(payload)
stat=json.loads((O/'build-summary.json').read_text(encoding='utf-8'));stat.update(webObjects=webobjects,compressedBytes=len(packed),rawBytes=len(raw),materials=len(doc['materials']),images=len(doc['images']),nearVegetationCells=len(groups),farVegetationCells=len(far_groups),triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'] if 'indices'in p))
(O/'build-summary.json').write_text(json.dumps(stat,indent=2),encoding='utf-8');print('D80_FINAL',json.dumps(stat),flush=True)
