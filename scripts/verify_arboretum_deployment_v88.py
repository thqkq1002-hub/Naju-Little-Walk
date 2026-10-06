"""Read-only verification of published HTML, model and navigation metadata."""
import hashlib,json,re,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1]
BASE='https://naju-little-walk.vercel.app'
def get(path):
 request=urllib.request.Request(BASE+path,headers={'Accept-Encoding':'identity','User-Agent':'Naju-release-verification'})
 with urllib.request.urlopen(request,timeout=60) as response:return response.status,response.read()
def sha(raw):return hashlib.sha256(raw).hexdigest()
html_status,html=get('/?place=naju-arboretum&v=central-platanus-v88')
local_html=(R/'dist/client/index.html').read_text(encoding='utf-8').replace('\r\n','\n')
assert html.decode('utf-8').replace('\r\n','\n')==local_html,'Published HTML differs from the checked build'
entry=re.search(r'src="(/assets/[^\"]+\.js)"',local_html).group(1)
entry_status,entry_data=get(entry)
assert entry_data==(R/'dist/client'/entry.lstrip('/')).read_bytes(),'Entry bundle mismatch'
model_status,model=get('/models/naju-arboretum.glb.gz?v=central-platanus-v88')
assert model==(R/'public/models/naju-arboretum.glb.gz').read_bytes(),'Published model mismatch'
world_status,world=get('/naju-arboretum-world.json?v=central-platanus-v88')
assert json.loads(world)==json.loads((R/'public/naju-arboretum-world.json').read_bytes()),'Published world metadata mismatch'
result=dict(date='2026-10-03',implementation_commit='666b5025eac8b23fa5713d86a6831bfdb90bedb5',vercel_deployment='7xrZE5WYDnLbERENdUXGMsVCDgQ5',vercel_status='success',
 github_status_url='https://vercel.com/reinhardt7177-labs-projects/naju-little-walk/7xrZE5WYDnLbERENdUXGMsVCDgQ5',url=BASE+'/?place=naju-arboretum&v=central-platanus-v88',
 html_http_status=html_status,entry_http_status=entry_status,model_http_status=model_status,world_http_status=world_status,
 normalized_html_matches_built_entry=True,app_entry_script=entry,entry_bundle_matches_local=True,model_matches_local=True,world_matches_local=True,
 model_gzip_sha256=sha(model),model_gzip_bytes=len(model),tests_passed=83,typescript_passed=True,static_build_passed=True,
 blender_comparison_reviewed=True,production_scene_verified=False,browser_verification_limitation='Computer-use runtime failed to initialize: kernel assets path not found. v88 app pixels and tablet input were not reverified.',android_hardware_verified=False,terrain_implementation_complete=False)
(R/'knowledge/sources/arboretum/central-platanus-v88-deployment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
