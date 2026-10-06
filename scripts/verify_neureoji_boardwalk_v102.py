"""Check all protected geometry and the Blender source after the surface-only fix."""
from pathlib import Path
import json,gzip,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/neureoji-v102';K=R/'knowledge/sources/neureoji-v102'
helpers={'__file__':str(R/'scripts/verify_neureoji_close_v100.py')}
exec((R/'scripts/verify_neureoji_close_v100.py').read_text(encoding='utf8').split('before,bb=load')[0],helpers)
load,stream,triangles=[helpers[k] for k in ['load','stream','triangles']]
before,bb=load(O/'before.glb');after,ab=load(R/'public/models/neureoji.glb')
by={m['name']:m for m in before['meshes']};checked=[]
assert set(by)=={m['name'] for m in after['meshes']}
for m in after['meshes']:
 old=by[m['name']]
 if m['name']=='walk-floor_hydrangea_woodland-hydrangea':
  assert triangles(after,ab,m)==triangles(before,bb,old),m['name']
 else:
  assert len(m['primitives'])==len(old['primitives'])
  for q,p in zip(m['primitives'],old['primitives']):
   assert q['attributes'].keys()==p['attributes'].keys()
   for key in q['attributes']:assert stream(after,ab,q['attributes'][key])==stream(before,bb,p['attributes'][key]),(m['name'],key)
 checked.append(m['name'])
oldw=json.loads((O/'world-before.json').read_text(encoding='utf8'))
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
for key in ['solids','arrivals','walkRoute','hydrangeaRoutes','spawn','topDeckHeightMetres','towerHeightMetres']:assert w[key]==oldw[key],key
d=json.loads((K/'model.json').read_text(encoding='utf8'))
assert hashlib.sha256((R/d['preservedSource']).read_bytes()).hexdigest()==d['preservedSourceSha256']
raw=(R/'public/models/neureoji.glb').read_bytes();packed=(R/'public/models/neureoji.glb.gz').read_bytes()
assert gzip.decompress(packed)==raw and len(packed)<16*1024**2
assert (R/'dist/client/models/neureoji.glb.gz').read_bytes()==packed
assert (R/'dist/client/neureoji-world.json').read_bytes()==(R/'public/neureoji-world.json').read_bytes()
report=dict(revision=w['revision'],preservedMeshes=len(checked),woodlandTrianglesExact=True,otherAttributesExact=True,navigationExact=True,sourcePreserved=True,transportExact=True,staticBuildExact=True,gzipBytes=len(packed),gzipSha256=hashlib.sha256(packed).hexdigest())
(K/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
