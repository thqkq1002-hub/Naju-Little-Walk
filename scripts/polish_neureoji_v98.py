import bpy,json,sys,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
from neureoji_glb_materials import preserve_foliage_materials
O=R/'outputs/neureoji-polish-v98';O.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/neureoji-polish-v98';K.mkdir(parents=True,exist_ok=True)
S=R/'outputs/quality-v97/neureoji-canopy-v97b.blend';target=O/'neureoji-polish-v98.blend'
if target.exists():raise RuntimeError('Preserve authored revision')
sha=hashlib.sha256(S.read_bytes()).hexdigest();w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
nav=hashlib.sha256(json.dumps(w['solids'],sort_keys=True).encode()).hexdigest()
shutil.copy2(R/'public/models/neureoji.glb',O/'before.glb');shutil.copy2(R/'public/neureoji-world.json',O/'world-before.json')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;dep=bpy.context.evaluated_depsgraph_get()
lands=[(o,BVHTree.FromObject(o,dep)) for o in s.objects if o.name in ['ground_native_DSM_interpreted','Neureoji94_graded_woodland_banks']]
def ground(x,z):
 ys=[]
 for ob,bvh in lands:
  inv=ob.matrix_world.inverted();hit=bvh.ray_cast(inv@Vector((x,-z,200)),(inv.to_3x3()@Vector((0,0,-1))).normalized(),500)[0]
  if hit is not None:ys.append((ob.matrix_world@hit).z)
 return max(ys) if ys else None
rows=[];count=0
for ob in s.objects:
 if not ob.name.startswith('Neureoji93_woodland_crowns_'):continue
 vertices=list(ob.data.vertices);assert len(vertices)%12==0;inv=ob.matrix_world.inverted()
 for i in range(0,len(vertices),12):
  vs=vertices[i:i+12];pts=[ob.matrix_world@v.co for v in vs]
  x=sum(p.x for p in pts)/12;z=-sum(p.y for p in pts)/12;base=min(p.z for p in pts);dy=0
  if math.hypot(x,z)<480:
   h=ground(x,z)
   if h is not None:dy=h-base;rows.append(dict(x=x,z=z,before=base,ground=h,shift=dy))
  for v,p in zip(vs,pts):p.x=x+(p.x-x)*.72;p.y=-z+(p.y+z)*.72;p.z+=dy;v.co=inv@p
  count+=1
 ob.data.update();ob['canopy_width_revision']='v98 0.72x photographic shape interpretation'
img=bpy.data.images.load(str(R/'work/neureoji-polish-v98/woodland-crown-v98.png'),check_existing=False)
for m in bpy.data.materials:
 if not m.name.startswith('Neureoji93_crown_'):continue
 for node in m.node_tree.nodes:
  if node.type=='TEX_IMAGE':node.image=img
 m.diffuse_color=(1,1,1,1);bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=1
 for node in m.node_tree.nodes:
  if node.type=='TEX_IMAGE':m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
# Source geometry of the tower, river and all walking surfaces remains untouched.
s['elevation_audit']='v98 same modeled base 45.76368m and deck 57.76368m; not surveyed; water plane not an observed datum.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(target));stats=export('neureoji',O,publish=False)
raw,mats=preserve_foliage_materials((O/'neureoji-web-v91.glb').read_bytes(),{m.name:list(m.diffuse_color) for m in bpy.data.materials});raw,norm=compact_normals(raw);(O/'neureoji.glb').write_bytes(raw)
d=dict(revision='neureoji-polish-v98',blend=target.relative_to(R).as_posix(),preservedSource=S.relative_to(R).as_posix(),preservedSourceSha256=sha,navigationSolidsSha256=nav,navigationChanged=False,crowns=count,groundedCrowns=rows,widthScale=.72,restoredCutoutMaterials=mats,export=stats,normalStorage=norm)
(K/'model.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8').replace("knowledge/sources/neureoji-v95/model.json","knowledge/sources/neureoji-polish-v98/model.json").replace("('Neureoji95_',","('Neureoji97_', 'Neureoji93_near_trunks_and_branches', 'Neureoji95_',").replace("p=R/'public/models/neureoji.glb'","p=R/'outputs/neureoji-polish-v98/neureoji.glb'").replace("dest=R/'public/models'/","dest=R/'outputs/neureoji-polish-v98'/")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
assert hashlib.sha256(S.read_bytes()).hexdigest()==sha
for name in ['neureoji.glb','neureoji.glb.gz']:shutil.copy2(O/name,R/'public/models'/name)
w.update(revision=d['revision'],navigationFromBlend=d['blend']);w['elevationAudit']=dict(checked='2026-10-05',base=w['spawn']['height'],topDeck=w['topDeckHeightMetres'],totalStructureHeight=w['towerHeightMetres'],datum='Modeled DEM elevation; water plane not an observed water-level datum',surveyed=False,evidence='knowledge/sources/neureoji-polish-v98/elevation-check.json')
w['limitations'].append('v98: 표고 재검토 후 기존 바닥 높이 유지. 원경 수관 폭·색·윤곽은 사진 참고 추정, 반경 480m 안 식재 높이는 표시 지형에 정렬.')
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');print('V98_COMPLETE',count,len(rows),flush=True)
