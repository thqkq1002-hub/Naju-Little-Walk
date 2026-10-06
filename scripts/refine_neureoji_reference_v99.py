import bpy,json,sys,hashlib,shutil,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
from neureoji_glb_materials import preserve_foliage_materials
O=R/'outputs/neureoji-v99';O.mkdir(parents=True,exist_ok=True);K=R/'knowledge/sources/neureoji-v99';K.mkdir(parents=True,exist_ok=True)
S=R/'outputs/neureoji-polish-v98/neureoji-polish-v98.blend';target=O/'neureoji-reference-v99.blend'
if target.exists():raise RuntimeError('Preserve authored revision')
sha=hashlib.sha256(S.read_bytes()).hexdigest();w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'));nav=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
shutil.copy2(R/'public/models/neureoji.glb',O/'before.glb');shutil.copy2(R/'public/neureoji-world.json',O/'world-before.json')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
# Match the smaller texture to the far view while preserving the authored crown geometry.
original=next(n.image for n in bpy.data.materials['Neureoji93_crown_0'].node_tree.nodes if n.type=='TEX_IMAGE');crown=original.copy();crown.name='Neureoji99_far_crown';crown.scale(256,256)
for m in bpy.data.materials:
 if m.name.startswith('Neureoji93_crown_'):
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':n.image=crown
# Muted leaf colors retain the blue/pink masses seen in the July 2026 photographs.
tints=[(.54,.70,.43,1),(.66,.78,.50,1),(.44,.60,.33,1)]
for i,tint in enumerate(tints):
 m=bpy.data.materials['Neureoji95_leaf_'+str(i)];m.diffuse_color=tint
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
 mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint
 m.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.94
 m['photo_color_interpretation']='v99 subdued living foliage; inferred from 2024 and 2026 photos'
# Connected 14-vertex lacecap cores are shallow cupped flower heads, not perfectly flat disks.
domes=0
for ob in s.objects:
 if not ob.name.startswith('Neureoji95_bloom_core_'):continue
 vs=ob.data.vertices;parent=list(range(len(vs)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for f in ob.data.polygons:
  a=root(f.vertices[0])
  for i in f.vertices[1:]:parent[root(i)]=a
 groups={}
 for i in range(len(vs)):groups.setdefault(root(i),[]).append(i)
 for ids in groups.values():
  if len(ids)!=14:continue
  center=vs[min(ids)].co;cx,cy=center.x,center.y;low=min(vs[i].co.z for i in ids)
  for i in ids:
   v=vs[i];r=math.hypot(v.co.x-cx,v.co.y-cy);v.co.x=cx+(v.co.x-cx)*.93;v.co.y=cy+(v.co.y-cy)*.93
   if r<.001:v.co.z=low+.072
  domes+=1
 ob.data.update()
# Planar UV authoring changes only shading; walking positions and slopes are unchanged.
path=bpy.data.materials.new('Neureoji99_path_aggregate');path.use_nodes=True;path.diffuse_color=(1,1,1,1)
bs=next(n for n in path.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.96
tex=path.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'work/neureoji-v99/path-aggregate.png'));path.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
paths=[]
for ob in s.objects:
 if not ob.name.startswith('walk-floor_hydrangea_'):continue
 ob.data.materials.clear();ob.data.materials.append(path)
 uv=ob.data.uv_layers.active or ob.data.uv_layers.new(name='Pavement grain')
 for li,loop in enumerate(ob.data.loops):
  p=ob.matrix_world@ob.data.vertices[loop.vertex_index].co;uv.data[li].uv=(p.x/1.3,p.y/1.3)
 for p in ob.data.polygons:p.material_index=0
 paths.append(ob.name)
steel=bpy.data.materials.get('Neureoji93_coated_steel')
if steel:
 bs=next(n for n in steel.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=.65;bs.inputs['Metallic'].default_value=.12
s['v99_reference']='2026-07-10 localm photographs and 2024-07-08 visitor photographs: matte tower paint, aggregate trail, leafy colored flower masses. Detailed dimensions interpreted.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));stats=export('neureoji',O,publish=False)
raw,mats=preserve_foliage_materials((O/'neureoji-web-v91.glb').read_bytes(),{m.name:list(m.diffuse_color) for m in bpy.data.materials});raw,norm=compact_normals(raw);(O/'neureoji.glb').write_bytes(raw)
d=dict(revision='neureoji-reference-v99',blend=target.relative_to(R).as_posix(),preservedSource=S.relative_to(R).as_posix(),preservedSourceSha256=sha,navigationSolidsSha256=nav,navigationChanged=False,lacecapCoresShaped=domes,pathMaterials=paths,leafTints=tints,farCrownTexturePixels=256,restoredCutoutMaterials=mats,export=stats,normalStorage=norm)
(K/'model.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8').replace('knowledge/sources/neureoji-v95/model.json','knowledge/sources/neureoji-v99/model.json').replace("('Neureoji95_',","('Neureoji97_', 'Neureoji93_near_trunks_and_branches', 'Neureoji95_',").replace("p=R/'public/models/neureoji.glb'","p=R/'outputs/neureoji-v99/neureoji.glb'").replace("dest=R/'public/models'/","dest=R/'outputs/neureoji-v99'/").replace('print(json.dumps(d,ensure_ascii=False,indent=2))',"print('PACKED',d['export']['gzipBytes'])")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
assert hashlib.sha256(S.read_bytes()).hexdigest()==sha
for name in ['neureoji.glb','neureoji.glb.gz']:shutil.copy2(O/name,R/'public/models'/name)
w.update(revision=d['revision'],navigationFromBlend=d['blend']);w['limitations'].append('v99: 2024·2026 사진 참고 식생 색·꽃 중심부 곡면·포장 재질 조정. 보행 지형과 충돌 및 전망대 높이 유지. 식생 세부는 추정.')
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');print('V99_COMPLETE',domes,paths,flush=True)
