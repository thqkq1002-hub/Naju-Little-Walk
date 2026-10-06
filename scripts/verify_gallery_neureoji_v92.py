"""Record concrete final artifacts and checks without copying reference images into deployment."""
from pathlib import Path
import json,hashlib,gzip,datetime
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
wp=R/'public/neureoji-world.json';w=json.loads(wp.read_text(encoding='utf8'));w['limitations']=list(dict.fromkeys(w['limitations']));wp.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
models=[]
for id,ref in [('yeongsanpo-history','history-gallery-v91.json'),('neureoji','neureoji-v92/model.json')]:
 p=R/'knowledge/sources'/ref;record=json.loads(p.read_text(encoding='utf8'));raw=R/'public/models'/(id+'.glb');packed=raw.with_suffix('.glb.gz');assert gzip.decompress(packed.read_bytes())==raw.read_bytes()
 blend=R/record.get('editedBlend',record.get('blend'));world=R/'public'/(id+'-world.json')
 assert sha(raw)==record['export']['sha256'];assert sha(packed)==record['export']['gzipSha256']
 record['finalBlendSha256']=sha(blend);record['worldSha256']=sha(world);record['verification']=dict(functionalTests=97,typeCheck='passed',staticBuild='passed',browserPixelCheck='unavailable',androidHardwareCheck='not run')
 p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');models.append(dict(scene=id,blend=blend.relative_to(R).as_posix(),blendSha256=sha(blend),worldSha256=sha(world),modelSha256=sha(raw),compressedSha256=sha(packed),gzipBytes=packed.stat().st_size))
report=dict(revision='gallery-neureoji-v92',createdAtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),models=models,tests=97,typeCheck=True,staticBuild=True,
    originalGalleryPreserved=True,limitations=['No complete current gallery floor plan / verified second-floor use.', '30m DSM interpreted ground and photo-estimated tower dimensions.', 'Geometry and production files verified; no live browser pixel or Android hardware check.'])
(R/'knowledge/sources/gallery-neureoji-v92-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Verified final Blender exports, compressed transport and provenance')
