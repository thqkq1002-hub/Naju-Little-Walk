"""Remove unused UV streams from Blender GLBs without changing visible geometry.

Only TEXCOORD attributes on materials with no texture slots are removed. Vertex
positions, normals, indices, transforms, texture images and materials are kept.
Buffer views are repacked losslessly; there is no mesh or texture decimation.
"""
import json,struct,hashlib
from pathlib import Path

def compact_glb(path):
    path=Path(path);raw=path.read_bytes()
    if raw[:4]!=b'glTF':raise ValueError('Expected GLB')
    length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length])
    offset=20+length;bin_length,kind=struct.unpack_from('<II',raw,offset)
    if kind!=0x004E4942:raise ValueError('Expected binary GLB chunk')
    binary=raw[offset+8:offset+8+bin_length]
    if len(doc.get('buffers',[]))!=1 or doc['buffers'][0].get('uri'):raise ValueError('Expected standalone GLB')
    if doc.get('extensionsUsed'):raise ValueError('Review extension references before compacting')
    def textured(value):
        if isinstance(value,dict):return any('texture' in k.lower() or textured(v) for k,v in value.items())
        if isinstance(value,list):return any(textured(v) for v in value)
        return False
    removed=0
    for mesh in doc.get('meshes',[]):
        for primitive in mesh['primitives']:
            material=doc.get('materials',[])[primitive['material']] if 'material' in primitive else {}
            if not textured(material):
                for key in list(primitive['attributes']):
                    if key.startswith('TEXCOORD_'):del primitive['attributes'][key];removed+=1
    used=set()
    for mesh in doc.get('meshes',[]):
        for p in mesh['primitives']:
            used.update(p['attributes'].values())
            if 'indices' in p:used.add(p['indices'])
            for target in p.get('targets',[]):used.update(target.values())
    for skin in doc.get('skins',[]):
        if 'inverseBindMatrices' in skin:used.add(skin['inverseBindMatrices'])
    for animation in doc.get('animations',[]):
        for s in animation['samplers']:used.update([s['input'],s['output']])
    remap={old:new for new,old in enumerate(sorted(used))}
    accessors=[doc['accessors'][i] for i in sorted(used)]
    for mesh in doc.get('meshes',[]):
        for p in mesh['primitives']:
            p['attributes']={key:remap[value] for key,value in p['attributes'].items()}
            if 'indices' in p:p['indices']=remap[p['indices']]
            for target in p.get('targets',[]):
                for key in target:target[key]=remap[target[key]]
    for skin in doc.get('skins',[]):
        if 'inverseBindMatrices' in skin:skin['inverseBindMatrices']=remap[skin['inverseBindMatrices']]
    for animation in doc.get('animations',[]):
        for s in animation['samplers']:
            for key in ('input','output'):s[key]=remap[s[key]]
    views=set()
    for a in accessors:
        if 'bufferView' in a:views.add(a['bufferView'])
        if 'sparse' in a:
            for key in ('indices','values'):views.add(a['sparse'][key]['bufferView'])
    for im in doc.get('images',[]):
        if 'bufferView' in im:views.add(im['bufferView'])
    vmap={};new_binary=bytearray();new_views=[];view_keys={};shared_views=0
    for i in sorted(views):
        view=dict(doc['bufferViews'][i]);start=view.get('byteOffset',0);size=view['byteLength']
        payload=binary[start:start+size]
        semantics={k:v for k,v in view.items() if k not in ('byteOffset','buffer')}
        key=(json.dumps(semantics,sort_keys=True),hashlib.sha256(payload).digest())
        if key in view_keys:
            vmap[i]=view_keys[key];shared_views+=1;continue
        vmap[i]=len(new_views);view_keys[key]=vmap[i]
        new_binary.extend(b'\0'*((-len(new_binary))%4));view['byteOffset']=len(new_binary)
        new_binary.extend(payload);new_views.append(view)
    for a in accessors:
        if 'bufferView' in a:a['bufferView']=vmap[a['bufferView']]
        if 'sparse' in a:
            for key in ('indices','values'):a['sparse'][key]['bufferView']=vmap[a['sparse'][key]['bufferView']]
    for im in doc.get('images',[]):
        if 'bufferView' in im:im['bufferView']=vmap[im['bufferView']]
    # Repeated boxes share byte-identical indices/normals. Reuse those streams
    # and their complete accessor definitions without quantizing any values.
    unique=[];accessor_keys={};amap={}
    for i,a in enumerate(accessors):
        key=json.dumps(a,sort_keys=True,separators=(',',':'))
        if key not in accessor_keys:accessor_keys[key]=len(unique);unique.append(a)
        amap[i]=accessor_keys[key]
    for mesh in doc.get('meshes',[]):
        for p in mesh['primitives']:
            p['attributes']={k:amap[v] for k,v in p['attributes'].items()}
            if 'indices' in p:p['indices']=amap[p['indices']]
            for target in p.get('targets',[]):
                for key in target:target[key]=amap[target[key]]
    for skin in doc.get('skins',[]):
        if 'inverseBindMatrices' in skin:skin['inverseBindMatrices']=amap[skin['inverseBindMatrices']]
    for animation in doc.get('animations',[]):
        for s in animation['samplers']:
            for key in ('input','output'):s[key]=amap[s[key]]
    doc['accessors']=unique;doc['bufferViews']=new_views;doc['buffers'][0]['byteLength']=len(new_binary)
    data=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf-8');data+=b' '*((-len(data))%4);new_binary.extend(b'\0'*((-len(new_binary))%4))
    result=struct.pack('<4sII',b'glTF',2,28+len(data)+len(new_binary))+struct.pack('<II',len(data),0x4E4F534A)+data+struct.pack('<II',len(new_binary),0x004E4942)+new_binary
    path.write_bytes(result)
    return dict(removedUnusedUvStreams=removed,sharedIdenticalViews=shared_views,sharedIdenticalAccessors=len(accessors)-len(unique),before=len(raw),after=len(result))

if __name__=='__main__':
    import sys
    print(compact_glb(sys.argv[1]))
