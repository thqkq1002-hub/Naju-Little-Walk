from pathlib import Path
import zipfile,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/neureoji-v100/authoring';O.mkdir(parents=True,exist_ok=True)
name='outputs/neureoji-v100/neureoji-close-detail-v100.blend';p=R/name
model=json.loads((R/'knowledge/sources/neureoji-v100/model.json').read_text(encoding='utf8'))
d=dict(created='2026-10-05',latestBlend=name,files=[dict(path=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())],preservedSource=model['preservedSource'],preservedSourceSha256=model['preservedSourceSha256'],previousArchive='https://github.com/reinhardt7177-lab/naju-little-walk/releases/tag/observatory-refinement-v99-20261005',deploymentIncludesBlender=False)
mp=O/'manifest.json';mp.write_text(json.dumps(d,indent=2),encoding='utf8');archive=O/'neureoji-authoring-v100.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(p,name);z.write(mp,'manifest.json');z.writestr('RESTORE.txt','Restore the preserved .blend at its original relative path under the repository root. Textures are packed. Previous v96-v99 revisions remain in the linked prior release. Never overwrite an edited .blend with a generation script. Tools, libraries and downloaded reference photographs are excluded.\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
d.update(archiveBytes=archive.stat().st_size,archiveSha256=hashlib.sha256(archive.read_bytes()).hexdigest());mp.write_text(json.dumps(d,indent=2),encoding='utf8')
(R/'knowledge/sources/neureoji-v100/authoring-archive.json').write_text(json.dumps(d,indent=2),encoding='utf8');print('V100_AUTHORING_ARCHIVE',archive.stat().st_size)
