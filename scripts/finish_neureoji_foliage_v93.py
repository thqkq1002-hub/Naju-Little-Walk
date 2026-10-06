"""Preserve the C artist revision and remove crossed-card lighting seams from prepainted crowns."""
import bpy, json, sys, gzip, struct, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
O=R/'outputs/neureoji-v93';source=O/'neureoji-quality-v93c.blend';target=O/'neureoji-quality-v93d.blend'
if target.exists():raise RuntimeError('Preserve previous artist revision')
before=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source))
for m in bpy.data.materials:
    if not m.name.startswith('Neureoji93_crown_'):continue
    bs=m.node_tree.nodes.get('Principled BSDF');tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
    m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.65
    m['prepainted_canopy_unlit']=True
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));stats=export('neureoji',O)
p=R/'public/models/neureoji.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for m in doc['materials']:
    if not m['name'].startswith(('Neureoji93_crown_','Neureoji93_near_leaves')):continue
    m.update(alphaMode='MASK',alphaCutoff=.38,doubleSided=True)
    bm=bpy.data.materials.get(m['name']);m['pbrMetallicRoughness']['baseColorFactor']=[min(1,c) for c in bm.diffuse_color]
    if m['name'].startswith('Neureoji93_crown_'):
        m.setdefault('extensions',{})['KHR_materials_unlit']={};m.pop('emissiveFactor',None);m.pop('emissiveTexture',None)
doc['extensionsUsed']=list(dict.fromkeys(doc.get('extensionsUsed',[])+['KHR_materials_unlit']))
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0);p.write_bytes(raw);p.with_suffix('.glb.gz').write_bytes(packed)
stats.update(bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest())
worldp=R/'public/neureoji-world.json';w=json.loads(worldp.read_text(encoding='utf8'));w.update(revision='neureoji-quality-v93d',navigationFromBlend=target.relative_to(R).as_posix());worldp.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
kp=R/'knowledge/sources/neureoji-v93/model.json';k=json.loads(kp.read_text(encoding='utf8'));k.update(revision=w['revision'],blend=target.relative_to(R).as_posix(),export=stats,reviewPasses=4,crownShading='Prepainted foliage uses KHR_materials_unlit to avoid crossed-card brightness seams.');kp.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print('NEUREOJI_FOLIAGE_FINAL',json.dumps(stats),flush=True)
