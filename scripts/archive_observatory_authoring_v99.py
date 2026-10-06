from pathlib import Path
import zipfile,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/observatory-authoring-v99';O.mkdir(parents=True,exist_ok=True)
files=['outputs/relief-v96/neureoji-relief-v96.blend','outputs/relief-v96/bitgaram-overview-relief-v96b.blend','outputs/quality-v97/neureoji-canopy-v97b.blend','outputs/neureoji-polish-v98/neureoji-polish-v98.blend','outputs/neureoji-v99/neureoji-reference-v99.blend']
manifest=dict(created='2026-10-05',repository='reinhardt7177-lab/naju-little-walk',latestNeureoji=files[-1],latestBitgaram=files[1],preservedRevisions=[],deploymentIncludesBlender=False)
for name in files:
 p=R/name;manifest['preservedRevisions'].append(dict(path=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
mp=O/'manifest.json';mp.write_text(json.dumps(manifest,indent=2),encoding='utf8')
archive=O/'observatory-authoring-v96-v99.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in files:z.write(R/name,name)
 z.write(mp,'manifest.json')
 z.writestr('RESTORE.txt','Restore these files under the repository root. All authored revisions are preserved; use latestNeureoji and latestBitgaram from manifest.json for further editing. Do not overwrite an edited .blend by rerunning generation scripts. Tools, libraries, downloaded reference photographs and temporary source archives are excluded.\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
manifest['archiveSha256']=hashlib.sha256(archive.read_bytes()).hexdigest();manifest['archiveBytes']=archive.stat().st_size;mp.write_text(json.dumps(manifest,indent=2),encoding='utf8');print('AUTHORING_ARCHIVE',archive.stat().st_size)
