"""Compare editable source/candidate geometry and paired tree placements, not screenshots."""
import bpy,json,hashlib,struct,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/quality-v58'
prefixes=('aerial_woodland_canopy','shore_finish_tree','surrounding_path_tree','tree_canopy','woodland_branch')
def protected():
    result={}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or obj.name.startswith(prefixes):continue
        h=hashlib.sha256()
        for row in obj.matrix_world:h.update(struct.pack('<4d',*row))
        for v in obj.data.vertices:h.update(struct.pack('<3d',*v.co))
        for p in obj.data.polygons:h.update(struct.pack('<'+str(len(p.vertices))+'I',*p.vertices))
        result[obj.name]=h.hexdigest()
    return result
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/palette-v51/bitgaram-park-color-v51.blend'))
before=protected()
bpy.ops.wm.open_mainfile(filepath=str(O/'bitgaram-park-crowns-v58.blend'))
after=protected();assert before==after,'Protected ground, trunks or architecture changed'
trees={}
for obj in bpy.context.scene.objects:
    lod=obj.get('vegetation_lod')
    if not lod:continue
    trees.setdefault(obj['tree_source_trunk'],{})[lod]=obj
assert len(trees)==2422
for pair in trees.values():
    assert set(pair)=={'near','far'}
    assert pair['near'].matrix_world==pair['far'].matrix_world
    assert pair['near']['vegetation_distance']==pair['far']['vegetation_distance']
raw=(O/'bitgaram-park-v58.glb').read_bytes()
assert gzip.decompress(Path(str(O/'bitgaram-park-v58.glb')+'.gz').read_bytes())==raw
assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
doc=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
leaf=next(m for m in doc['materials'] if m['name']=='Park_leaf_spray_cutout')
assert leaf['alphaMode']=='MASK' and leaf['doubleSided']
assert all('bufferView' in im for im in doc['images'])
result=dict(protected_meshes=len(before),protected_geometry_and_transforms_identical=True,paired_trees=len(trees),paired_transforms_identical=True,embedded_images=len(doc['images']),alpha_mode=leaf['alphaMode'],gzip_exact=True,glb_bytes=len(raw),gzip_bytes=Path(str(O/'bitgaram-park-v58.glb')+'.gz').stat().st_size,source='outputs/palette-v51/bitgaram-park-color-v51.blend',candidate='outputs/quality-v58/bitgaram-park-crowns-v58.blend',note='Botanical spray atlas is an original procedural drawing, not a photograph. Individual tree species remain estimated.')
(R/'knowledge/sources/bitgaram/park-quality-v58-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('VERIFIED',json.dumps(result),flush=True)
