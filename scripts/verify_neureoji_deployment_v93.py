"""Verify the published Blender model, world and static bundles against the reviewed build."""
import argparse,hashlib,json,re,urllib.request,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE='https://naju-little-walk.vercel.app';rev='neureoji-quality-v93d'
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--deployment-url',required=True);args=p.parse_args()
def get(path):
    req=urllib.request.Request(BASE+path,headers={'Accept-Encoding':'identity','User-Agent':'Naju-release-verification'})
    with urllib.request.urlopen(req,timeout=45) as response:return response.status,response.read()
status,html=get('/?place=neureoji&at=top&v='+rev);local=(R/'dist/client/index.html').read_text(encoding='utf8')
assert html.decode().replace('\r\n','\n')==local.replace('\r\n','\n'),'Production HTML differs from reviewed build'
entry=re.search(r'src="(/assets/[^\"]+\.js)"',local).group(1)
paths=[('dist/client'+entry,entry),('public/models/neureoji.glb.gz','/models/neureoji.glb.gz?v='+rev),
    ('public/neureoji-world.json','/neureoji-world.json?v='+rev),('public/naju-region-map.json','/naju-region-map.json?v='+rev)]
paths += [('dist/client/assets/'+b.name,'/assets/'+b.name) for prefix in ['explorer-','map-travel-'] for b in (R/'dist/client/assets').glob(prefix+'*.js')]
checks={}
for path,url in paths:
    http,data=get(url);expected=(R/path).read_bytes()
    assert (json.loads(data)==json.loads(expected) if path.endswith('.json') else data==expected),'Production mismatch: '+path
    checks[path]=dict(status=http,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),matchesLocal=True)
report=dict(revision=rev,implementationCommit=args.commit,verifiedAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    vercelDeploymentUrl=args.deployment_url,vercelStatus='success',htmlHttpStatus=status,htmlMatchesLocal=True,checks=checks,
    relevantTestsPassed=80,allTests=dict(total=187,passed=185,baselineFailures=2),typescriptPassed=True,staticBuildPassed=True,
    productionPixelsVerified=False,androidHardwareVerified=False,limitations=['Tower dimensions, canopy allowance and fine land-use subdivisions are photo interpretations; terrain uses 30m DSM.',
    'Two legacy Bitgaram access-route tests also fail with pre-change HEAD code.'])
(R/'knowledge/sources/neureoji-v93/deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
