"""Quantize only new decorative planting. Walking/river geometry stays byte-for-byte intact."""
import json,struct,gzip,hashlib,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];p=R/'public/models/neureoji.glb';raw=p.read_bytes()
n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
nodes=list(doc['nodes']);selected={node['mesh'] for node in nodes if 'mesh' in node and node.get('name','').startswith(('Neureoji95_','Neureoji94_trail_leaf_clusters_','Neureoji94_trail_trunks','Neureoji93_near_leaves','Neureoji93_near_branches'))}
replacement={};transforms={};max_error=0;count=0
for index in selected:
    primitives=doc['meshes'][index]['primitives'];arrays=[]
    for prim in primitives:
        a=doc['accessors'][prim['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
        assert a['componentType']==5126 and v.get('byteStride',12)==12 and not a.get('sparse')
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        arrays.append(np.frombuffer(binary,dtype='<f4',count=a['count']*3,offset=offset).reshape(-1,3))
    lo=np.min(np.vstack([a.min(axis=0) for a in arrays]),axis=0).astype(np.float64)
    hi=np.max(np.vstack([a.max(axis=0) for a in arrays]),axis=0).astype(np.float64);span=float(np.max(hi-lo))
    transforms[index]=(lo.tolist(),[span]*3)
    for prim,positions in zip(primitives,arrays):
        a=doc['accessors'][prim['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
        q=np.rint((positions.astype(np.float64)-lo)/span*65535).clip(0,65535).astype('<u2')
        error=np.linalg.norm(q.astype(np.float64)/65535*span+lo-positions,axis=1)
        max_error=max(max_error,float(error.max()));count+=len(q)
        stored=np.zeros((len(q),4),dtype='<u2');stored[:,:3]=q
        replacement[a['bufferView']]=stored.tobytes();v['byteStride']=8
        a.update(componentType=5123,normalized=True,byteOffset=0,min=q.min(axis=0).tolist(),max=q.max(axis=0).tolist())
# Uniform scale preserves the authored normals; parent extras continue to apply to the primitive.
for node in nodes:
    if node.get('mesh') not in transforms:continue
    mesh=node.pop('mesh');translation,scale=transforms[mesh];child=len(doc['nodes'])
    doc['nodes'].append(dict(name=node.get('name','')+'_position_storage',mesh=mesh,translation=translation,scale=scale))
    node.setdefault('children',[]).append(child)
def has_texture(value):
    if isinstance(value,dict):return any(k.endswith('Texture') or has_texture(v) for k,v in value.items())
    if isinstance(value,list):return any(has_texture(v) for v in value)
    return False
assert not doc.get('skins') and not doc.get('animations')
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        if not has_texture(doc['materials'][prim['material']]):
            for key in list(prim['attributes']):
                if key.startswith('TEXCOORD_'):del prim['attributes'][key]
used={a for m in doc['meshes'] for q in m['primitives'] for a in q['attributes'].values()}
used.update(q['indices'] for m in doc['meshes'] for q in m['primitives'] if 'indices' in q)
mapping={a:i for i,a in enumerate(sorted(used))}
doc['accessors']=[doc['accessors'][i] for i in sorted(used)]
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        prim['attributes']={k:mapping[a] for k,a in prim['attributes'].items()}
        if 'indices' in prim:prim['indices']=mapping[prim['indices']]
used_views={a['bufferView'] for a in doc['accessors']}
used_views.update(i['bufferView'] for i in doc.get('images',[]) if 'bufferView' in i)
view_mapping={a:i for i,a in enumerate(sorted(used_views))}
packed=bytearray()
for i,v in enumerate(doc['bufferViews']):
    if i not in used_views:continue
    packed.extend(b'\0'*((-len(packed))%4));data=replacement.get(i)
    if data is None:data=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
    v.update(byteOffset=len(packed),byteLength=len(data));packed.extend(data)
doc['bufferViews']=[doc['bufferViews'][i] for i in sorted(used_views)]
for a in doc['accessors']:a['bufferView']=view_mapping[a['bufferView']]
for i in doc.get('images',[]):
    if 'bufferView' in i:i['bufferView']=view_mapping[i['bufferView']]
packed.extend(b'\0'*((-len(packed))%4));doc['buffers'][0]['byteLength']=len(packed)
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
result=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(packed))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(packed),b'BIN\0')+packed
transport=gzip.compress(result,9,mtime=0)
assert max_error<.006,'Decorative plant deviation exceeds 6mm: '+str(max_error)
assert len(transport)<16*1024**2,'Neureoji download budget exceeded: '+str(len(transport))
for suffix,data in [('.glb',result),('.glb.gz',transport)]:
    dest=R/'public/models'/('neureoji'+suffix);temp=dest.with_suffix(dest.suffix+'.v95.tmp');temp.write_bytes(data);temp.replace(dest)
k=R/'knowledge/sources/neureoji-v95/model.json';d=json.loads(k.read_text(encoding='utf8'))
d['plantPositionStorage']=dict(vertices=count,maxDecorativePlantErrorMetres=max_error,walkingAndRiverPositionChanges=0,uniformScale=True)
d['export'].update(bytes=len(result),gzipBytes=len(transport),sha256=hashlib.sha256(result).hexdigest(),gzipSha256=hashlib.sha256(transport).hexdigest())
k.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(d,ensure_ascii=False,indent=2))
