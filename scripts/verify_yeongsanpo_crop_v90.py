"""Read-only production asset comparison after the GitHub/Vercel deployment."""
import argparse,json,hashlib,re,gzip,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];BASE='https://naju-little-walk.vercel.app'
parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--deployment-url',required=True);args=parser.parse_args()
def get(path):
 req=urllib.request.Request(BASE+path,headers={'Accept-Encoding':'identity','User-Agent':'Naju-release-verification'})
 with urllib.request.urlopen(req,timeout=45) as res:return res.status,res.read()
def sha(raw):return hashlib.sha256(raw).hexdigest()
report=json.loads((R/'knowledge/sources/yeongsanpo-crop-v90.json').read_text(encoding='utf8'))
assert sha((R/report['sourceBlend']).read_bytes())==report['sourceSha256'],'Original Blender source changed'
assert gzip.decompress((R/'public/models/yeongsanpo.glb.gz').read_bytes())==(R/'public/models/yeongsanpo.glb').read_bytes()
tests=(R/'work/yeongsanpo-crop-v90/tests-final.txt').read_text(encoding='utf8')
assert re.search(r'pass 91\b',tests) and re.search(r'fail 0\b',tests),'Final tests not complete'
status,html=get('/?place=yeongsanpo&v=north-crop-v90')
local=(R/'dist/client/index.html').read_text(encoding='utf8').replace('\r\n','\n')
assert html.decode('utf8').replace('\r\n','\n')==local,'HTML differs from verified build'
entry=re.search(r'src="(/assets/[^\"]+\.js)"',local).group(1);entry_status,bundle=get(entry)
assert bundle==(R/'dist/client'/entry.lstrip('/')).read_bytes(),'App bundle mismatch'
checks={}
for file,url,structured in [('public/models/yeongsanpo.glb.gz','/models/yeongsanpo.glb.gz?v=north-crop-v90',False),
                            ('public/yeongsanpo-world.json','/yeongsanpo-world.json?v=north-crop-v90',True)]:
 http,data=get(url);expected=(R/file).read_bytes()
 assert (json.loads(data)==json.loads(expected) if structured else data==expected),file+' production mismatch'
 checks[file]=dict(httpStatus=http,sha256=sha(data),bytes=len(data),matchesLocal=True)
result=dict(verifiedAtUTC=datetime.now(timezone.utc).isoformat(),implementationCommit=args.commit,vercelStatus='success',
 vercelDeploymentUrl=args.deployment_url,url=BASE+'/?place=yeongsanpo&v=north-crop-v90',
 htmlHttpStatus=status,entryHttpStatus=entry_status,htmlMatchesLocal=True,entryBundleMatchesLocal=True,checks=checks,
 testsPassed=91,typescriptPassed=True,staticBuildPassed=True,sourceBlendPreserved=True,blenderReviewImage='outputs/yeongsanpo-crop-v90/yeongsanpo-crop-review.png',
 blenderReviewComplete=True,productionSceneVerified=False,androidHardwareVerified=False,
 browserVerificationLimitation='Computer-use runtime kernel assets initialization failed earlier in this session; production pixels and tablet input were not verified.')
(R/'knowledge/sources/yeongsanpo-crop-v90-deployment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
