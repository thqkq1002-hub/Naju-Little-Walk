"""Restore the unsupported 8m canopy deduction locally, preserving the v95 artist file."""
import bpy, json, math, sys, hashlib, gzip
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
from neureoji_glb_normals import compact_normals
from neureoji_glb_materials import preserve_foliage_materials
O=R/'outputs/relief-v96';O.mkdir(parents=True,exist_ok=True)
K=R/'knowledge/sources/observatory-relief-v96'
S=R/'outputs/neureoji-v95/neureoji-hydrangea-v95c.blend'
TARGET=O/'neureoji-relief-v96.blend'
if TARGET.exists():raise RuntimeError('Preserve existing authored revision')
source_sha=hashlib.sha256(S.read_bytes()).hexdigest()
world_path=R/'public/neureoji-world.json';w=json.loads(world_path.read_text(encoding='utf8'))
(O/'neureoji-world-before.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf8')
geo=json.loads((R/'knowledge/sources/neureoji-v92/geography.json').read_text(encoding='utf8'))
shore=[]
for poly in geo['water']:
    for ring in [poly['points'],*poly['holes']]:
        for a,b in zip(ring,ring[1:]+ring[:1]):
            n=max(1,math.ceil(math.dist(a,b)/3))
            shore.extend((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n,0) for i in range(n))
kd=KDTree(len(shore))
for i,p in enumerate(shore):kd.insert(p,i)
kd.balance()
def delta(x,z,shore_blend=False):
    t=max(0,min(1,(math.hypot(x,z)-280)/200));f=1-t*t*(3-2*t)
    if shore_blend:f*=min(1,kd.find((x,z,0))[2]/22)
    return 8*f
bpy.ops.wm.open_mainfile(filepath=str(S));scene=bpy.context.scene
changed=[]
for ob in scene.objects:
    if ob.type not in {'MESH','FONT'}:continue
    if ob.name.startswith(('mapped_river_water','Neureoji93_original_sky','Neureoji93_native_distant')):continue
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    far=max(math.hypot(p.x,p.y) for p in pts)
    if far<280:
        ob.location.z+=8;changed.append(ob.name)
    elif ob.type=='MESH':
        # Local relief joins the original distant DEM at 480m. Water vertices are never changed.
        inv=ob.matrix_world.inverted();count=0
        for v in ob.data.vertices:
            p=ob.matrix_world@v.co;d=delta(p.x,-p.y,ob.name=='ground_native_DSM_interpreted')
            if d>0.000001:p.z+=d;v.co=inv@p;count+=1
        if count:ob.data.update();changed.append(ob.name)
for q in w['solids']:
    q['position'][1]+=8
    if 'floorPlane' in q:q['floorPlane'][2]+=8
for a in [w['spawn'],*w['arrivals'].values()]:a['height']+=8
for q in w['places']:q['arrivalHeight']+=8
for q in w['signs']:q['position'][1]+=8
for q in w['architectureViews']:q['center'][1]+=8
for p in w['walkRoute']:p[2]+=8
for route in w['hydrangeaRoutes'].values():
    for p in route:p[2]+=8
for p in w['hydrangeaConnector']:p[2]+=8
w['topDeckHeightMetres']+=8
w['revision']='neureoji-relief-v96';w['navigationFromBlend']=TARGET.relative_to(R).as_posix()
w['reliefInterpretation']=dict(towerBaseMetres=w['spawn']['height'],topDeckMetres=w['topDeckHeightMetres'],
    canopyDeductionMetres=0,previousCanopyDeductionMetres=8,transitionRadiiMetres=[280,480],
    evidence='knowledge/sources/observatory-relief-v96/independent-terrain.json',surveyed=False)
w['limitations'].append('v96: 전망대 위치 GLO-30 45.76m와 독립 Terrarium 45.67m를 대조. 근거 없는 8m 수관 차감을 근거리에서 철회한 지면 해석이며, 지면 실측이 아님. 280–480m에서 기존 원경에 연결.')
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
stats=export('neureoji',O,publish=False)
raw,_=preserve_foliage_materials((O/'neureoji-web-v91.glb').read_bytes(),{m.name:list(m.diffuse_color) for m in bpy.data.materials})
raw,normals=compact_normals(raw)
(R/'public/models/neureoji.glb').write_bytes(raw)
report=dict(revision=w['revision'],blend=TARGET.relative_to(R).as_posix(),preservedSource=S.relative_to(R).as_posix(),
    preservedSourceSha256=source_sha,changedObjects=len(changed),relief=w['reliefInterpretation'],export=stats,normalStorage=normals)
(K/'neureoji-model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Reuse the established display-only plant compression without rewriting its historical report.
code=(R/'scripts/compact_neureoji_plants_v95.py').read_text(encoding='utf8')
code=code.replace("knowledge/sources/neureoji-v95/model.json","knowledge/sources/observatory-relief-v96/neureoji-model.json")
exec(compile(code,str(R/'scripts/compact_neureoji_plants_v95.py'),'exec'),{'__file__':str(R/'scripts/compact_neureoji_plants_v95.py')})
assert hashlib.sha256(S.read_bytes()).hexdigest()==source_sha
world_path.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print('NEUREOJI_RELIEF_V96_COMPLETE',flush=True)
