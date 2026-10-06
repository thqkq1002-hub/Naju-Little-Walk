"""Move the lower shelter posts clear of the terrace connector, in a new blend."""
import bpy,json,gzip,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/bitgaram-v101';K=R/'knowledge/sources/bitgaram/access-v101'
source=O/'bitgaram-access-v101c.blend';target=O/'bitgaram-access-v101d.blend'
if target.exists():raise RuntimeError('Existing artist revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(source));ob=bpy.data.objects['access101_lower_station_posts'];delta=4.8*(.95-.65)
for v in ob.data.vertices:v.co.y-=delta
ob.data.update()
w=json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))
for s in w['solids']:
 if s['name']=='access101_lower_station_posts':s['footprint']=[[x,z+delta] for x,z in s['footprint']]
w['navigationFromBlend']=target.relative_to(R).as_posix();bpy.ops.wm.save_as_mainfile(filepath=str(target))
path=O/'bitgaram-park.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,use_visible=False,use_renderable=False,export_animations=False)
raw=path.read_bytes();path.with_suffix('.glb.gz').write_bytes(gzip.compress(raw,9,mtime=0))
for ext in ('.glb','.glb.gz'):shutil.copyfile(path.with_suffix(ext),R/('public/models/bitgaram-park'+ext))
(R/'public/bitgaram-park-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf8')
p=K/'build.json';d=json.loads(p.read_text());d.update(output=target.relative_to(R).as_posix(),shelterPostsClearConnector=True,gzipBytes=path.with_suffix('.glb.gz').stat().st_size,modelSha256=hashlib.sha256(raw).hexdigest());p.write_text(json.dumps(d,indent=2),encoding='utf8')
