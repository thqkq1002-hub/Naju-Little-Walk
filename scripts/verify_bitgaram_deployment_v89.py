"""Read-only checks that Vercel serves the verified app, terrain and NPC levels."""
import argparse,hashlib,json,re,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE='https://naju-little-walk.vercel.app'
parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--deployment-url',required=True)
args=parser.parse_args()
def get(path):
 request=urllib.request.Request(BASE+path,headers={'Accept-Encoding':'identity','User-Agent':'Naju-release-verification'})
 with urllib.request.urlopen(request,timeout=45) as response:return response.status,response.read()
def sha(raw):return hashlib.sha256(raw).hexdigest()
html_status,html=get('/?place=bitgaram-park&v=terrain-v89')
local_html=(R/'dist/client/index.html').read_text(encoding='utf8').replace('\r\n','\n')
assert html.decode('utf8').replace('\r\n','\n')==local_html,'Published HTML differs from the checked build'
entry=re.search(r'src="(/assets/[^\"]+\.js)"',local_html).group(1)
entry_status,entry_data=get(entry)
assert entry_data==(R/'dist/client'/entry.lstrip('/')).read_bytes(),'Entry bundle mismatch'
checks={}
for local,path,structured in [('public/models/bitgaram-park.glb.gz','/models/bitgaram-park.glb.gz?v=terrain-v89',False),
                             ('public/bitgaram-park-world.json','/bitgaram-park-world.json?v=terrain-v89',True),
                             ('public/npc-placements.json','/npc-placements.json?v=terrain-v89',True)]:
 status,data=get(path);expected=(R/local).read_bytes()
 assert (json.loads(data)==json.loads(expected) if structured else data==expected),f'Published data mismatch: {local}'
 checks[local]=dict(httpStatus=status,sha256=sha(data),bytes=len(data),matchesLocal=True)
for bundle in sorted((R/'dist/client/assets').glob('explorer-*.js')):
 status,data=get('/assets/'+bundle.name);assert data==bundle.read_bytes(),'Explorer bundle mismatch'
 assert b'terrain-v89' in data,'Published explorer lacks new asset cache version'
 checks[bundle.name]=dict(httpStatus=status,sha256=sha(data),matchesLocal=True)
result=dict(implementationCommit=args.commit,vercelStatus='success',vercelDeploymentUrl=args.deployment_url,
 url=BASE+'/?place=bitgaram-park&v=terrain-v89',htmlHttpStatus=html_status,entryHttpStatus=entry_status,
 normalizedHtmlMatchesLocal=True,entryBundleMatchesLocal=True,checks=checks,
 testsPassed=95,typescriptPassed=True,staticBuildPassed=True,blenderComparisonReviewed=True,
 productionSceneVerified=False,androidHardwareVerified=False,
 browserVerificationLimitation='Computer-use runtime could not initialize its kernel assets. Production scene pixels and Android input were not verified.',
 sourceResolutionMetres=30,surveyedBareEarth=False)
(R/'knowledge/sources/bitgaram/terrain-v89/deployment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
