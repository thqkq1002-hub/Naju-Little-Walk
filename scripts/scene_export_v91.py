"""Blender-only surface authoring and bounded, self-contained web exports."""
import bpy,json,gzip,struct,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
helpers={'__file__':str(R/'scripts/refine_yeongsanpo_v79.py')}
source=(R/'scripts/refine_yeongsanpo_v79.py').read_text(encoding='utf8').split('stats=[]')[0]
source=source.replace("if o.type!='MESH' or len(o.data.materials)!=1:continue", "if o.get('keep_web') or o.type!='MESH' or len(o.data.materials)!=1:continue")
exec(compile(source,str(R/'scripts/refine_yeongsanpo_v79.py'),'exec'),helpers)
helpers['cache']={}
def surface(ob,kind):
    if ob.type!='MESH':return
    for i,m in enumerate(list(ob.data.materials)):
        if m:ob.data.materials[i]=helpers['make_mat'](kind,m)
    helpers['uv'](ob,.65 if kind=='wood' else 1)
def export(key,out,publish=True):
    # Keep editable text in .blend, but batch tessellated glyphs in the web copy.
    bpy.ops.object.select_all(action='DESELECT')
    text_objects=[o for o in bpy.context.scene.objects if o.type=='FONT']
    for o in text_objects:o.select_set(True);o['no_shadow']=True
    if text_objects:
        bpy.context.view_layer.objects.active=text_objects[0]
        bpy.ops.object.convert(target='MESH')
    helpers['key']=key;merged=helpers['group_scene']()
    for o in bpy.context.scene.objects:
        if o.type=='MESH':
            a=helpers['np'].empty(len(o.data.vertices)*3,dtype=helpers['np'].float32)
            o.data.vertices.foreach_get('co',a);o.data.vertices.foreach_set('co',helpers['np'].round(a*10000)/10000)
    path=out/(key+'-web-v91.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_active_scene=True,export_extras=True,
        export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_apply=True)
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
    for m in doc.get('materials',[]):
        bm=bpy.data.materials.get(m.get('name',''))
        if bm and bm.name.startswith('Y79_') and 'baseColorTexture' in m.get('pbrMetallicRoughness',{}):
            m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color) if bm.name!='Y79_leaf_cutout' else [1,1,1,1]
        if bm and bm.name.startswith('Y79_leaf_cutout'):m.update(alphaMode='MASK',alphaCutoff=.42,doubleSided=True)
    encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
    packed=gzip.compress(raw,9,mtime=0)
    if publish:
        if len(packed)>25*1024*1024:raise RuntimeError('25 MiB model transport budget exceeded')
        for suffix,data in [('.glb',raw),('.glb.gz',packed)]:
            p=R/'public/models'/(key+suffix);tmp=p.with_suffix(p.suffix+'.v91.tmp');tmp.write_bytes(data);tmp.replace(p)
    else:
        # Let a caller finalize normals/material metadata before applying the final budget.
        path.write_bytes(raw)
    return dict(merged=merged,meshes=len(doc['meshes']),materials=len(doc['materials']),images=len(doc.get('images',[])),
        bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest())
