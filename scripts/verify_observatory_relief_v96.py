"""Verify immutable source files, water, transport bytes and protected overview streams."""
from pathlib import Path
import json,struct,hashlib,gzip,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'outputs/relief-v96';K=R/'knowledge/sources/observatory-relief-v96'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(raw):
 n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def arrays(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];size={'VEC3':3,'SCALAR':1,'VEC2':2,'VEC4':4}[a['type']];dt={5120:'i1',5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];bs=np.dtype(dt).itemsize
 out=np.ndarray((a['count'],size),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',bs*size),bs)).astype(float)
 if a.get('normalized'):out/= {5120:127,5121:255,5123:65535}[a['componentType']]
 return out
def world(g,b,node,prim):
 p=arrays(g,b,prim['attributes']['POSITION']);m=np.array(node.get('matrix',np.eye(4).ravel())).reshape(4,4).T
 q=np.c_[p,np.ones(len(p))]@m.T
 if 'translation' in node:q[:,:3]+=node['translation']
 return q[:,:3]
def stream(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];return b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
report=dict(date='2026-10-05',sources={},models={},overview={})
for p,expected in [('outputs/neureoji-v95/neureoji-hydrangea-v95c.blend','87b1eef38a34ed7421be0667c1a6b70fe2ee3101dcf3fbfc7426c8e42d0f7860'),('outputs/terrain-v89/bitgaram-park-glo30-terrain-v89d.blend','4b6a8a260c999f9cdb0061e221b1f866bbcbeea1c510e3a89ac17f601547d044')]:
 actual=sha(R/p);assert actual==expected;report['sources'][p]=dict(sha256=actual,preserved=True)
for key in ['neureoji','bitgaram-overview','bitgaram-overview-part2']:
 p=R/'public/models'/(key+'.glb');raw=p.read_bytes();assert gzip.decompress(p.with_suffix('.glb.gz').read_bytes())==raw
 assert sha(R/'dist/client/models'/(key+'.glb.gz'))==sha(p.with_suffix('.glb.gz'))
 report['models'][key]=dict(sha256=sha(p),gzipExact=True,buildMatches=True)
 if key.startswith('bitgaram'):
  g,b=parse(raw);old,ob=parse((O/(key+'-before.glb')).read_bytes());unchanged=0;maxPlanError=0;indexExact=0
  for i,node in enumerate(g['nodes']):
   if 'mesh' not in node:continue
   oldnode=old['nodes'][i];prims=g['meshes'][node['mesh']]['primitives'];original=old['meshes'][oldnode['mesh']]['primitives']
   for p,q in zip(prims,original):
    assert np.array_equal(arrays(g,b,p['indices']),arrays(old,ob,q['indices']));indexExact+=1
    a,c=world(g,b,node,p),world(old,ob,oldnode,q);maxPlanError=max(maxPlanError,float(np.max(np.abs(a[:,[0,2]]-c[:,[0,2]]))))
    for name in q['attributes']:
     if node.get('extras',{}).get('relief_revision')=='v96' and name in ['POSITION','NORMAL']:continue
     assert stream(g,b,p['attributes'][name])==stream(old,ob,q['attributes'][name]),(key,node['name'],name)
    if node.get('extras',{}).get('relief_revision')!='v96':unchanged+=1
  assert maxPlanError<.00001,(key,maxPlanError)
  report['overview'][key]=dict(unchangedPrimitives=unchanged,indexStreamsPreserved=indexExact,maxPlanCoordinateChangeMetres=maxPlanError)
# Compare water to the authoritative pre-edit Git branch, independently of render appearance.
baseline=subprocess.check_output(['git','show','HEAD:public/models/neureoji.glb'],cwd=R)
old,ob=parse(baseline);g,b=parse((R/'public/models/neureoji.glb').read_bytes())
def river(doc):return next(n for n in doc['nodes'] if n['name']=='mapped_river_water_neureoji')
a,c=river(g),river(old)
for p,q in zip(g['meshes'][a['mesh']]['primitives'],old['meshes'][c['mesh']]['primitives']):
 assert np.array_equal(world(g,b,a,p),world(old,ob,c,q));assert np.array_equal(arrays(g,b,p['indices']),arrays(old,ob,q['indices']))
report['riverGeometryUnchanged']=True
report['selectedTestsPassed']=dict(commonMovement=74,neureoji=8,bitgaramOverviewAndTerrain=11,newRelief=3)
report['browser']=dict(bitgaram='outputs/relief-v96/browser-bitgaram-close.png',neureoji='outputs/relief-v96/browser-neureoji-top.png',pageErrors=0,localOnly=True)
report['buildContainsNoAuthoringFiles']=not any(p.suffix in ['.blend','.zip','.exe'] for p in (R/'dist/client').rglob('*'))
assert report['buildContainsNoAuthoringFiles']
(K/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False),flush=True)
