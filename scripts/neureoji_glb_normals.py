"""Compact only lighting normals; keep authored positions and collision geometry exact.

KHR_mesh_quantization BYTE normalized normals have 4-byte element alignment.
https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_mesh_quantization
"""
import json, struct, math

def compact_normals(raw):
    length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
    indices={p['attributes']['NORMAL'] for m in doc['meshes'] for p in m['primitives'] if 'NORMAL' in p['attributes']}
    replacements={};count=0;maximum_error=0
    for index in indices:
        a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
        if a['componentType']!=5126 or a['type']!='VEC3' or a.get('sparse'):continue
        users=[i for i,q in enumerate(doc['accessors']) if q.get('bufferView')==a['bufferView']]
        if users!=[index]:continue
        out=bytearray();stride=view.get('byteStride',12);offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        for i in range(a['count']):
            normal=struct.unpack_from('<3f',binary,offset+i*stride);q=[max(-127,min(127,round(v*127))) for v in normal]
            out.extend(struct.pack('<4b',*q,0));size=math.sqrt(sum(v*v for v in q));source_size=math.sqrt(sum(v*v for v in normal))
            if size and source_size:maximum_error=max(maximum_error,math.acos(max(-1,min(1,sum(x*y for x,y in zip(normal,q))/(source_size*size)))))
        replacements[a['bufferView']]=bytes(out);view['byteStride']=4
        a.update(componentType=5120,normalized=True,byteOffset=0);a.pop('min',None);a.pop('max',None);count+=a['count']
    packed=bytearray()
    for i,view in enumerate(doc['bufferViews']):
        packed.extend(b'\0'*((-len(packed))%4));data=replacements.get(i)
        if data is None:data=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        view.update(byteOffset=len(packed),byteLength=len(data));packed.extend(data)
    packed.extend(b'\0'*((-len(packed))%4));doc['buffers'][0]['byteLength']=len(packed)
    for key in ['extensionsUsed','extensionsRequired']:doc[key]=list(dict.fromkeys(doc.get(key,[])+['KHR_mesh_quantization']))
    encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    result=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(packed))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(packed),b'BIN\0')+packed
    assert maximum_error<math.radians(.4)
    return result,dict(vertices=count,maximumLightingNormalErrorDegrees=math.degrees(maximum_error),positionChanges=0)
