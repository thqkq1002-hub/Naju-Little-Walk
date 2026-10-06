"""Save a new artist revision and sync its shadow flags without changing geometry.

Internal faces of adjacent slope slabs must not cast striped self shadows.
The path continues to receive the real tree shadows in Three.js.
"""
import bpy, json, struct, gzip, hashlib, argparse, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/neureoji-v94'
parser=argparse.ArgumentParser();parser.add_argument('--from-revision',default='f');parser.add_argument('--to-revision',default='g');parser.add_argument('--concrete-forest',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
source=O/f'neureoji-hydrangea-v94{args.from_revision}.blend';target=O/f'neureoji-hydrangea-v94{args.to_revision}.blend'
if target.exists():raise RuntimeError('Preserve the existing artist revision')
sha=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source))
names=[]
for ob in bpy.context.scene.objects:
    if ob.name.startswith('walk-floor_hydrangea_'):ob['no_shadow']=True;names.append(ob.name)
assert len(names)==2
if args.concrete_forest:
    road=bpy.data.materials['Neureoji94_path_flower-road'];forest=bpy.data.materials['Neureoji94_path_woodland-hydrangea']
    image=next(n.image for n in road.node_tree.nodes if n.type=='TEX_IMAGE')
    for node in forest.node_tree.nodes:
        if node.type=='TEX_IMAGE':node.image=image
    bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(target))
p=R/'public/models/neureoji.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[20+n:]
for node in doc['nodes']:
    if node.get('name') in names:node.setdefault('extras',{})['no_shadow']=True
if args.concrete_forest:
    road=next(m for m in doc['materials'] if m.get('name')=='Neureoji94_path_flower-road')
    forest=next(m for m in doc['materials'] if m.get('name')=='Neureoji94_path_woodland-hydrangea')
    forest['pbrMetallicRoughness']['baseColorTexture']=dict(road['pbrMetallicRoughness']['baseColorTexture'])
encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4)
raw=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary
packed=gzip.compress(raw,9,mtime=0)
for suffix,data in [('.glb',raw),('.glb.gz',packed)]:
    dest=R/'public/models'/('neureoji'+suffix);tmp=dest.with_suffix(dest.suffix+'.v94.tmp');tmp.write_bytes(data);tmp.replace(dest)
wp=R/'public/neureoji-world.json';w=json.loads(wp.read_text(encoding='utf8'));w.update(revision=f'neureoji-hydrangea-v94{args.to_revision}',navigationFromBlend=target.relative_to(R).as_posix());wp.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
kp=R/'knowledge/sources/neureoji-v94/model.json';k=json.loads(kp.read_text(encoding='utf8'))
k.update(revision=w['revision'],blend=w['navigationFromBlend'],artistRevision=args.to_revision,preservedReviewSource=source.relative_to(R).as_posix(),preservedReviewSourceSha256=sha,
    shadowReview='Sloping path internal faces do not cast shadows. Authored positions, normals and navigation preserved; final surface material changes recorded separately.')
if args.concrete_forest:k['surfaceReview']='Northern railed path uses concrete matching OSM surface=concrete and the 2026 visitor photographs. End boardwalk retains timber.'
k['export'].update(bytes=len(raw),gzipBytes=len(packed),sha256=hashlib.sha256(raw).hexdigest(),gzipSha256=hashlib.sha256(packed).hexdigest());kp.write_text(json.dumps(k,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
print('NEUREOJI_SHADOW_FINAL',json.dumps(k['export']),flush=True)
