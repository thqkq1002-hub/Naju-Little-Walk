"""Restore the authored timber section lost by v99's whole-path material replacement."""
import bpy,json,sys,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
from neureoji_glb_materials import preserve_foliage_materials
O=R/'outputs/neureoji-v102';O.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/neureoji-v102';K.mkdir(parents=True,exist_ok=True)
S=R/'outputs/neureoji-v100/neureoji-close-detail-v100.blend';target=O/'neureoji-boardwalk-v102.blend'
if target.exists():raise RuntimeError('Preserve existing artist revision')
sha=hashlib.sha256(S.read_bytes()).hexdigest()
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
nav=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
shutil.copy2(R/'public/models/neureoji.glb',O/'before.glb')
shutil.copy2(R/'public/neureoji-world.json',O/'world-before.json')
bpy.ops.wm.open_mainfile(filepath=str(S))
ob=bpy.context.scene.objects['walk-floor_hydrangea_woodland-hydrangea']
mat=bpy.data.materials.new('Neureoji102_boardwalk_timber');mat.use_nodes=True;mat.diffuse_color=(1,1,1,1)
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9
tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(str(R/'assets/neureoji-v94/path-wood-original.png'),check_existing=True)
mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
ob.data.materials.append(mat);slot=len(ob.data.materials)-1;count=0
# Restore v94's original section boundary. This is an inferred material transition,
# not a new survey. Keep every vertex, face, custom normal and walking plane intact.
for face in ob.data.polygons:
 points=[ob.matrix_world@ob.data.vertices[i].co for i in face.vertices]
 if -sum(p.y for p in points)/len(points)<-190:
  face.material_index=slot;count+=1
  for li in face.loop_indices:
   p=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co
   ob.data.uv_layers.active.data[li].uv=(p.x*.8,-p.y*.8)
assert count>50
bpy.context.scene['boardwalk_v102']='Restore v94 timber section (z < -190) lost in v99 material unification; no geometry/navigation changes.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target))
stats=export('neureoji',O,publish=False)
raw,mats=preserve_foliage_materials((O/'neureoji-web-v91.glb').read_bytes(),{m.name:list(m.diffuse_color) for m in bpy.data.materials})
raw,norm=compact_normals(raw);(O/'neureoji.glb').write_bytes(raw)
d=dict(revision='neureoji-boardwalk-v102',blend=target.relative_to(R).as_posix(),preservedSource=S.relative_to(R).as_posix(),preservedSourceSha256=sha,navigationSolidsSha256=nav,navigationChanged=False,restoredTimberFaces=count,sectionBoundaryZ=-190,sectionBoundarySurveyed=False,restoredCutoutMaterials=mats,normalStorage=norm,export=stats)
(K/'model.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8').replace('knowledge/sources/neureoji-v95/model.json','knowledge/sources/neureoji-v102/model.json').replace("('Neureoji95_',","('Neureoji100_', 'Neureoji97_', 'Neureoji93_near_trunks_and_branches', 'Neureoji95_',").replace("p=R/'public/models/neureoji.glb'","p=R/'outputs/neureoji-v102/neureoji.glb'").replace("dest=R/'public/models'/","dest=R/'outputs/neureoji-v102'/").replace('print(json.dumps(d,ensure_ascii=False,indent=2))',"print('PACKED',d['export']['gzipBytes'])")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
assert hashlib.sha256(S.read_bytes()).hexdigest()==sha
for name in ['neureoji.glb','neureoji.glb.gz']:shutil.copy2(O/name,R/'public/models'/name)
w.update(revision='neureoji-boardwalk-v102',navigationFromBlend=target.relative_to(R).as_posix())
w['limitations'].append('v102: 이전 재질 통합으로 지워진 숲길 끝 목재 데크 표현을 복원. 전환 위치·판재 치수는 기존 사진 해석이며 실측 아님. 지형·계단·보행면·충돌·식재 좌표 유지.')
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print('V102_RESTORED',count,flush=True)
