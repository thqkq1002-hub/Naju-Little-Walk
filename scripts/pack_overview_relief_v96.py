"""Compact Blender-authored overview positions; retain all triangles and other streams."""
import json,struct,gzip,hashlib,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'outputs/relief-v96';K=R/'knowledge/sources/observatory-relief-v96'
def load(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]),raw[28+n:]
def read(g,b,i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];n={'VEC3':3,'VEC4':4,'SCALAR':1,'VEC2':2}[a['type']]
    dt={5120:'i1',5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];size=np.dtype(dt).itemsize
    return np.ndarray((a['count'],n),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*size),size)).astype(np.float64)
report=dict(revision='overview-relief-v96',parts=[])
for key in ['bitgaram-overview','bitgaram-overview-part2']:
    g,b=load(O/(key+'-v96.glb'));old,oldb=load(O/(key+'-before.glb'));replacement={};err=0
    for ni,node in enumerate(g['nodes']):
        if node.get('extras',{}).get('relief_revision')!='v96':continue
        arrays=[];prims=g['meshes'][node['mesh']]['primitives']
        for prim in prims:
            ai=prim['attributes']['POSITION'];pos=read(g,b,ai)
            if ai<len(old['accessors']):
                mat=np.array(old['nodes'][ni]['matrix']).reshape(4,4).T;pos=(np.c_[pos,np.ones(len(pos))]@mat.T)[:,:3]
            arrays.append(pos)
        # Retain the original quantization lattice in plan. Re-quantizing the
        # entire city batch would move protected distant buildings by millimetres.
        oldmat=np.array(old['nodes'][ni]['matrix']).reshape(4,4).T
        scale=float(oldmat[0,0]);lo=oldmat[:3,3].copy()
        oldprims=old['meshes'][old['nodes'][ni]['mesh']]['primitives']
        original=[(np.c_[read(old,oldb,p['attributes']['POSITION']),np.ones(old['accessors'][p['attributes']['POSITION']]['count'])]@oldmat.T)[:,:3] for p in oldprims]
        shifts=np.concatenate([a[:,1]-s[:,1] for a,s in zip(arrays,original)])
        if np.ptp(shifts)<.0001:lo[1]+=float(np.mean(shifts))
        else:
            low=min(a[:,1].min() for a in arrays)
            if low<lo[1]:lo[1]+=math.floor((low-lo[1])/scale)*scale
        hi=np.max(np.vstack([a.max(axis=0) for a in arrays]),axis=0)
        assert np.max((hi-lo)/scale)<65536,(node['name'],hi,lo,scale)
        node['matrix']=[scale,0,0,0,0,scale,0,0,0,0,scale,0,*lo.tolist(),1]
        for prim,pos in zip(prims,arrays):
            ai=prim['attributes']['POSITION'];a=g['accessors'][ai]
            quant=np.rint((pos-lo)/scale).clip(0,65535).astype('<u2');err=max(err,float(np.max(np.linalg.norm(quant.astype(float)*scale+lo-pos,axis=1))))
            packed=np.zeros((len(pos),4),dtype='<u2');packed[:,:3]=quant
            vi=len(g['bufferViews']);g['bufferViews'].append(dict(buffer=0,byteLength=packed.nbytes,byteStride=8,target=34962));replacement[vi]=packed.tobytes()
            a.update(bufferView=vi,byteOffset=0,componentType=5123,min=quant.min(axis=0).tolist(),max=quant.max(axis=0).tolist());a.pop('normalized',None)
    used=sorted({ai for m in g['meshes'] for p in m['primitives'] for ai in [p['indices'],*p['attributes'].values()]})
    amap={ai:i for i,ai in enumerate(used)};views=sorted({g['accessors'][ai]['bufferView'] for ai in used});vmap={vi:i for i,vi in enumerate(views)};out=bytearray()
    newviews=[]
    for vi in views:
        v=g['bufferViews'][vi].copy();raw=replacement.get(vi)
        if raw is None:raw=b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
        out.extend(b'\0'*((-len(out))%4));v['byteOffset']=len(out);out.extend(raw);newviews.append(v)
    g['accessors']=[g['accessors'][ai] for ai in used]
    for a in g['accessors']:a['bufferView']=vmap[a['bufferView']]
    for m in g['meshes']:
        for p in m['primitives']:
            p['indices']=amap[p['indices']];p['attributes']={k:amap[i] for k,i in p['attributes'].items()}
    out.extend(b'\0'*((-len(out))%4));g['bufferViews']=newviews;g['buffers'][0]['byteLength']=len(out)
    encoded=json.dumps(g,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
    raw=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(out))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(out),b'BIN\0')+out
    assert len(raw)<32*1024**2
    assert err<.04,(key,err)  # Existing whole-district lattice; walking meshes are separate.
    dest=R/'public/models'/(key+'.glb');tmp=dest.with_suffix('.v96.tmp');tmp.write_bytes(raw);tmp.replace(dest)
    packed=dest.with_suffix('.glb.gz');tmp=packed.with_suffix('.v96.tmp');tmp.write_bytes(gzip.compress(raw,9,mtime=0));tmp.replace(packed)
    report['parts'].append(dict(key=key,bytes=len(raw),maximumPositionErrorMetres=err,sha256=hashlib.sha256(raw).hexdigest(),changedNodes=[n['name'] for n in g['nodes'] if n.get('extras',{}).get('relief_revision')=='v96']))
w=json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'));upper=w['spawn']['height']
p=R/'public/bitgaram-orbit.json';orbit=json.loads(p.read_text(encoding='utf8'))
for pin in orbit['pins']:
    if pin['id']=='bitgaram-park':pin['position'][1]=34+upper-16
orbit['reliefRevision']='overview-relief-v96';p.write_text(json.dumps(orbit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report.update(upperMetres=upper,previousUpperMetres=16,sourceBlender='outputs/relief-v96/bitgaram-overview-relief-v96.blend')
(K/'overview-model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report),flush=True)
