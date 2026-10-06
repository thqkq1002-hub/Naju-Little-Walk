"""Finalize a preserved v95 artist study without recreating or overwriting its geometry."""
import bpy,json,struct,gzip,hashlib,sys,argparse
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
p=argparse.ArgumentParser();p.add_argument('--from-revision',default='a');p.add_argument('--to-revision',default='b');p.add_argument('--reduce-sepals',action='store_true')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
S=R/f'outputs/neureoji-v95/neureoji-hydrangea-v95{args.from_revision}.blend'
TARGET=S.with_name(f'neureoji-hydrangea-v95{args.to_revision}.blend');O=S.parent/f'export-{args.to_revision}';O.mkdir(exist_ok=True)
if TARGET.exists():raise RuntimeError('Preserve existing revision')
source_sha=hashlib.sha256(S.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(S));scene=bpy.context.scene
if args.reduce_sepals:
    for ob in scene.objects:
        if ob.type!='MESH' or not ob.name.startswith('Neureoji95_sepal_'):continue
        old=ob.data;keep={i for i in range(len(old.vertices)) if (i//24)%2==0}
        ids=sorted(keep);mapping={old_id:i for i,old_id in enumerate(ids)}
        mesh=bpy.data.meshes.new(old.name+'_web_detail')
        mesh.from_pydata([tuple(old.vertices[i].co) for i in ids],[],[tuple(mapping[i] for i in face.vertices) for face in old.polygons if all(i in keep for i in face.vertices)])
        for mat in old.materials:mesh.materials.append(mat)
        for face in mesh.polygons:face.use_smooth=True
        ob.data=mesh
    # Solid-colour petal and stem meshes need no texture coordinates.
    for ob in scene.objects:
        if ob.type=='MESH' and ob.name.startswith(('Neureoji95_sepal_','Neureoji95_hydrangea_stems')):
            for uv in list(ob.data.uv_layers):ob.data.uv_layers.remove(uv)
planting=dict(bushes=0,roundHeads=0,lacecapHeads=0,modeledSepals=0,leaves=0)
for ob in scene.objects:
    if ob.type!='MESH':continue
    if ob.name=='Neureoji95_hydrangea_stems':planting['bushes']=len(ob.data.vertices)//60
    if ob.name.startswith('Neureoji95_bloom_core_'):
        planting['roundHeads']+=sum(len(p.vertices)==4 for p in ob.data.polygons)//40
        planting['lacecapHeads']+=sum(len(p.vertices)==3 for p in ob.data.polygons)//12
    if ob.name.startswith('Neureoji95_sepal_'):planting['modeledSepals']+=len(ob.data.vertices)//6
    if ob.name.startswith('Neureoji95_leaves_'):planting['leaves']+=len(ob.data.vertices)//7
# A tint multiply keeps the editable Blender view consistent with its GLB base colour factor.
for m in bpy.data.materials:
    if not m.name.startswith('Neureoji95_leaf_'):continue
    bs=m.node_tree.nodes.get('Principled BSDF');link=next(iter(bs.inputs['Base Color'].links),None)
    if link and link.from_node.type!='MIX_RGB':
        tex=link.from_socket;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY'
        mix.inputs[0].default_value=1;mix.inputs[2].default_value=m.diffuse_color
        m.node_tree.links.new(tex,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
scene['hydrangea_planting_counts']=json.dumps(planting)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));stats=export('neureoji',O,publish=False)
raw=(O/'neureoji-web-v91.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc['materials']:
    bm=bpy.data.materials.get(m['name'])
    if m['name'].startswith(('Neureoji93_crown_','Neureoji93_near_leaves','Neureoji94_leaf_cutout','Neureoji94_bloom_cutout','Neureoji95_leaf_')):
        m.update(alphaMode='MASK',alphaCutoff=.38,doubleSided=True)
        # The multiply is represented by this standard base factor; source image remains original.
        m['pbrMetallicRoughness']['baseColorFactor']=[min(1,c) for c in bm.diffuse_color]
    if m['name'].startswith('Neureoji93_crown_'):
        m.setdefault('extensions',{})['KHR_materials_unlit']={};m.pop('emissiveFactor',None);m.pop('emissiveTexture',None)
doc['extensionsUsed']=list(dict.fromkeys(doc.get('extensionsUsed',[])+['KHR_materials_unlit']))
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
raw,normal_stats=compact_normals(raw);packed=gzip.compress(raw,9,mtime=0)
if len(packed)>=25*1024**2:raise RuntimeError('Final model transport budget exceeded: '+str(len(packed)))
for suffix,data in [('.glb',raw),('.glb.gz',packed)]:
    dest=R/'public/models'/('neureoji'+suffix);temp=dest.with_suffix(dest.suffix+'.v95.tmp');temp.write_bytes(data);temp.replace(dest)
p=R/'public/neureoji-world.json';w=json.loads(p.read_text(encoding='utf8'))
nav_sha=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
w.update(revision=f'neureoji-hydrangea-v95{args.to_revision}',navigationFromBlend=TARGET.relative_to(R).as_posix(),hydrangeaPlanting=planting)
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
assert hashlib.sha256(S.read_bytes()).hexdigest()==source_sha
stats.update(bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest())
record=dict(revision=w['revision'],blend=w['navigationFromBlend'],preservedSource=S.relative_to(R).as_posix(),preservedSourceSha256=source_sha,
    navigationSolidsSha256=nav_sha,navigationChanged=False,export=stats,planting=planting,normalStorage=normal_stats,
    sourceURLs=['https://akekanfl.tistory.com/8708274','https://naju-senior.com/local-news/21984/'])
K=R/'knowledge/sources/neureoji-v95';K.mkdir(parents=True,exist_ok=True)
(K/'model.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('NEUREOJI_V95_COMPLETE',json.dumps(record,ensure_ascii=False),flush=True)
