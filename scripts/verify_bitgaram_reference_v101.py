"""Check preserved authoring source, transport bytes and deployment exclusion."""
import json,hashlib,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[1];K=R/'knowledge/sources/bitgaram/access-v101'
build=json.loads((K/'build.json').read_text());cab=json.loads((K/'cabin.json').read_text())
assert hashlib.sha256((R/build['source']).read_bytes()).hexdigest()==build['sourceSha256']
assets={}
for stem in ('bitgaram-park','bitgaram-monorail','bitgaram-overview','bitgaram-overview-part2','bitgaram-access-overview'):
 raw=(R/f'public/models/{stem}.glb').read_bytes();gz=(R/f'public/models/{stem}.glb.gz').read_bytes()
 assert gzip.decompress(gz)==raw
 assert (R/f'dist/client/models/{stem}.glb.gz').read_bytes()==gz
 assets[stem]=dict(gzipBytes=len(gz),gzipSha256=hashlib.sha256(gz).hexdigest(),rawSha256=hashlib.sha256(raw).hexdigest())
assert assets['bitgaram-park']['rawSha256']==build['modelSha256']
overview=json.loads((K/'overview.json').read_text())
assert hashlib.sha256((R/overview['source']).read_bytes()).hexdigest()==overview['sourceSha256']
for part in overview['parts']:
 old=(R/f"outputs/bitgaram-v101/{part['key']}-source-v96.glb").read_bytes();new=(R/f"public/models/{part['key']}.glb").read_bytes()
 old_bin=old[28+int.from_bytes(old[12:16],'little'):];new_bin=new[28+int.from_bytes(new[12:16],'little'):]
 assert new_bin[:len(old_bin)]==old_bin,'Original district geometry/color/normal streams changed'
world=json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))
assert world['revision']=='bitgaram-access-v101'
assert json.loads((R/'dist/client/bitgaram-park-world.json').read_text(encoding='utf8'))==world
assert (R/world['navigationFromBlend']).exists()
assert 'OpenStreetMap' in world['source'] and 'ODbL' in world['source']
for p in (R/'dist/client').rglob('*'):
 assert p.suffix.lower() not in ('.blend','.zip','.tif','.exe','.py'),p
 assert 'satellite-native' not in p.name
report=dict(sourceUnchanged=True,transportExact=True,distMatchesPublic=True,referenceImageryDeployed=False,authoringFilesDeployed=False,assets=assets,parkAuthoring=build['output'],cabinAuthoring=cab['output'],protectedMeshes=build['protectedMeshes'],surveyed=False)
report.update(overviewAuthoring=overview['output'],overviewOriginalStreamsExact=True,removedObsoleteOverviewTriangles=sum(p['trianglesRemoved'] for p in overview['parts']))
(K/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('V101_VERIFIED',json.dumps(report))
