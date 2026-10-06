from pathlib import Path
import requests,hashlib,json
R=Path(__file__).resolve().parents[1];base='https://najuwalk.mumuworld.com';s=requests.Session()
w=s.get(base+'/neureoji-world.json?v=v98-proof-20261005',timeout=60);w.raise_for_status();d=w.json();assert d['revision']=='neureoji-polish-v98',d['revision']
b=s.get(base+'/models/neureoji.glb.gz?v=neureoji-polish-v98',timeout=90);b.raise_for_status();expected=json.loads((R/'knowledge/sources/neureoji-polish-v98/model.json').read_text(encoding='utf8'))['export']['gzipSha256'];assert hashlib.sha256(b.content).hexdigest()==expected
out=dict(url=base,revision=d['revision'],sourceCommit='850f7b6d11275a482dac3715a722a0f50e1f28ba',deployment='dpl_AE2ZoNtFkGNkzSSPzQYLMo4E9kDV',remoteGzipSha256=hashlib.sha256(b.content).hexdigest(),bytes=len(b.content),productionAssetExact=True)
p=R/'work/neureoji-v99/v98-deployment-proof.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2),encoding='utf8');print('V98_PRODUCTION_VERIFIED')

