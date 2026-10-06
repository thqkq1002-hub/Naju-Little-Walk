"""Shared authoring helpers keep exports consistent with the preserved editable copy."""
from pathlib import Path
exec(compile((Path(__file__).resolve().parent/'refine_yeongsanpo_v79.py').read_text(encoding='utf-8').split('stats=[]')[0],__file__,'exec'))
stats=[]
for key in keys:
    cache={};bpy.ops.wm.open_mainfile(filepath=str(O/f'{key}-detail-v79.blend'));scene=bpy.context.scene
    for o in scene.objects:
        if any(s in o.name for s in ['_seam','_rib','_grille','_stitch','_mortar','label_','_pull','_hinge']):o['no_shadow']=True
    merged=group_scene();after_objects=sum(o.type=='MESH' for o in scene.objects)
    for o in scene.objects:
        if o.type=='MESH':
            coords=np.empty(len(o.data.vertices)*3,dtype=np.float32);o.data.vertices.foreach_get('co',coords);o.data.vertices.foreach_set('co',np.round(coords*10000)/10000);o.data.update()
    target=O/f'{key}-web-v79.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_active_scene=True,export_extras=True,export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_apply=True)
    raw=target.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
    for m in doc.get('materials',[]):
        bm=bpy.data.materials.get(m.get('name',''))
        if bm and bm.name.startswith('Y79_'):
            if 'baseColorTexture' in m.get('pbrMetallicRoughness',{}):m['pbrMetallicRoughness']['baseColorFactor']=list(bm.diffuse_color) if bm.name!='Y79_leaf_cutout' else [1,1,1,1]
            if bm.name=='Y79_leaf_cutout':m['alphaMode']='MASK';m['alphaCutoff']=.42;m['doubleSided']=True
    encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary;packed=gzip.compress(raw,9,mtime=0)
    if len(packed)>25*1024*1024:raise RuntimeError('Hosting model budget exceeded')
    for suffix,payload in [('.glb',raw),('.glb.gz',packed)]:
        p=R/f'public/models/{key}{suffix}';temp=p.with_suffix(p.suffix+'.v79.tmp');temp.write_bytes(payload);temp.replace(p)
    stat=json.loads((O/f'{key}-stats.json').read_text(encoding='utf-8'));stat.update(webObjects=after_objects,merged=merged,compressedBytes=len(packed),materials=len(doc.get('materials',[])),images=len(doc.get('images',[])))
    (O/f'{key}-stats.json').write_text(json.dumps(stat,indent=2),encoding='utf-8');stats.append(stat);print('V79_RESULT',json.dumps(stat),flush=True)
(O/'build-summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
