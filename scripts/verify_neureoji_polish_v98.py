from pathlib import Path
import json,struct,gzip,hashlib
R=Path(__file__).resolve().parents[1];K=R/'knowledge/sources/neureoji-polish-v98';O=R/'outputs/neureoji-polish-v98'
def load(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def stream(d,b,a):
 a=d['accessors'][a];v=d['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12);return b[start:start+a['count']*stride]
before,bb=load(O/'before.glb');after,ab=load(R/'public/models/neureoji.glb');by={m['name']:m for m in before['meshes']};checked=[]
for m in after['meshes']:
 if m['name'].startswith(('walk-floor_','mapped_river_water','ground_native_DSM_interpreted','Neureoji94_graded_woodland_banks','v79_batch_')):
  old=by[m['name']];assert len(m['primitives'])==len(old['primitives'])
  for q,p in zip(m['primitives'],old['primitives']):assert stream(after,ab,q['attributes']['POSITION'])==stream(before,bb,p['attributes']['POSITION']),m['name']
  checked.append(m['name'])
d=json.loads((K/'model.json').read_text(encoding='utf8'));assert hashlib.sha256((R/d['preservedSource']).read_bytes()).hexdigest()==d['preservedSourceSha256']
raw=(R/'public/models/neureoji.glb').read_bytes();packed=(R/'public/models/neureoji.glb.gz').read_bytes();assert gzip.decompress(packed)==raw;assert (R/'dist/client/models/neureoji.glb.gz').read_bytes()==packed
report=dict(protectedPositionMeshes=checked,protectedMeshesCount=len(checked),sourcePreserved=True,transportExact=True,productionExact=True,downloadBytes=len(packed));(K/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(len(checked),'protected meshes verified')
