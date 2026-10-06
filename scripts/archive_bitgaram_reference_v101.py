"""Archive editable revisions and the preserved park source outside web assets."""
import json,hashlib,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];K=R/'knowledge/sources/bitgaram/access-v101';O=R/'outputs/bitgaram-v101/authoring';O.mkdir(exist_ok=True,parents=True)
build=json.loads((K/'build.json').read_text());cab=json.loads((K/'cabin.json').read_text());overview=json.loads((K/'overview.json').read_text())
names=[build['output'],cab['output'],overview['output'],build['source'],cab['source']]
files=[dict(path=Path(name).as_posix(),bytes=(R/name).stat().st_size,sha256=hashlib.sha256((R/name).read_bytes()).hexdigest()) for name in names]
manifest=dict(created='2026-10-05',files=files,previousOverviewSourceArchive='https://github.com/reinhardt7177-lab/naju-little-walk/releases/tag/observatory-refinement-v99-20261005',deploymentIncludesBlender=False)
mp=O/'manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf8');archive=O/'bitgaram-authoring-v101.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(R/f['path'],f['path'])
 z.write(mp,'manifest.json');z.writestr('RESTORE.txt','Restore files to their relative paths under the repository root. Never overwrite user-edited .blend files with a generator. Packed textures are included. Reference photos, satellite imagery, tools, libraries and Blender executables are excluded. The preserved v96 overview source remains available in the previous release.\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
manifest.update(archiveBytes=archive.stat().st_size,archiveSha256=hashlib.sha256(archive.read_bytes()).hexdigest());mp.write_text(json.dumps(manifest,indent=2),encoding='utf8');(K/'authoring-archive.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('AUTHORING_ARCHIVED',archive.stat().st_size)
