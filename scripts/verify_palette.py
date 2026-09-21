"""Verify every Blender colour edit preserves model geometry, textures and protected PBR."""
import json,struct,hashlib,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[1];reports=[]
def read(path):
 b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[20+n:]
for audit in sorted((R/'knowledge/sources/palette-v51').glob('*.json')):
 if audit.name=='summary.json':continue
 a=json.loads(audit.read_text(encoding='utf-8'));path=R/'public/models'/a['model'];before,bin0=read(R/'work/palette-v51'/a['model']);after,bin1=read(path)
 assert bin0==bin1 and hashlib.sha256(bin1).hexdigest()==a['binary_sha256'],a['model']
 changed={c['index'] for c in a['changes']}
 for i,(m,n) in enumerate(zip(before['materials'],after['materials'])):
  if i in changed:
   assert n.get('pbrMetallicRoughness',{}).get('baseColorFactor')==next(c['after'] for c in a['changes'] if c['index']==i)
   m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=n['pbrMetallicRoughness']['baseColorFactor']
  assert m==n,(a['model'],i)
 assert before==after,a['model']
 assert path.stat().st_size<32*1024*1024
 if Path(str(path)+'.gz').exists():assert gzip.decompress(Path(str(path)+'.gz').read_bytes())==path.read_bytes()
 reports.append(dict(model=a['model'],changed=len(changed),protected=len(a['protected']),geometry_unchanged=True))
assert len(reports)==17,len(reports)
print(json.dumps(reports,indent=2));print('ALL MAP PALETTE VERIFIED:',sum(r['changed'] for r in reports),'materials across',len(reports),'models')
