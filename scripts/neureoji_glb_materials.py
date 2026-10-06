"""Retain authored cutout foliage and prepainted distant-crown shading on every export."""
import json,struct

def preserve_foliage_materials(raw,tints=None):
    n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[20+n:]
    cutouts=('Neureoji93_crown_','Neureoji93_near_leaves','Neureoji94_leaf_cutout',
             'Neureoji94_bloom_cutout','Neureoji95_leaf_','Neureoji97_leaf_')
    patched=[]
    for m in g['materials']:
        name=m.get('name','')
        if name.startswith(cutouts):
            m.update(alphaMode='MASK',alphaCutoff=.38,doubleSided=True)
            if tints and name in tints:m['pbrMetallicRoughness']['baseColorFactor']=[min(1,c) for c in tints[name]]
            patched.append(name)
        if name.startswith('Neureoji93_crown_'):
            m.setdefault('extensions',{})['KHR_materials_unlit']={};m.pop('emissiveFactor',None);m.pop('emissiveTexture',None)
    g['extensionsUsed']=list(dict.fromkeys(g.get('extensionsUsed',[])+['KHR_materials_unlit']))
    text=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();text+=b' '*((-len(text))%4)
    return struct.pack('<4sII',b'glTF',2,20+len(text)+len(binary))+struct.pack('<I4s',len(text),b'JSON')+text+binary,patched
