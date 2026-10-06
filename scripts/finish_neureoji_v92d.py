"""Final circulation pass: alternating adjacent flights, grounded leaf crowns."""
import bpy,math,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from scene_export_v91 import export
O=R/'outputs/neureoji-v92';T=O/'neureoji-v92e.blend'
if T.exists():raise RuntimeError('Preserve saved artist revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'neureoji-v92c.blend'));s=bpy.context.scene;w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'));B=w['spawn']['height']
def flight(y):return max(0,min(2,int((y-B-.001)/3.6)))
def xform(name,y):
    if name.startswith(('walk-floor_stair_','tower_stair_','tower_tread_')):
        floor_y=y-(.52 if 'timber_baluster' in name else 1.08 if 'handrail' in name else .605 if 'guard' in name else 0)
        k=flight(floor_y);center=4.2 if k==1 else 2.5
        return lambda x:center+(x-3.2)*(.648148148)
    if name.startswith(('walk-floor_landing_','tower_landing_')):return lambda x:3.35+(x-3.2)*(3.85/2.7)
    if name.startswith(('walk-floor_top_connector_','tower_connector_')):return lambda x:1.2+(x-1.2)*.65
    if name.startswith(('tower_steel_column','tower_column_baseplate','tower_anchor_bolt','tower_diagonal_tension_brace')):return lambda x:x+(-.45 if x<3.2 else .75)
    return None
for o in s.objects:
    if o.type!='MESH':continue
    if o.name.startswith('v79_layered_leaf_canopies'):o.location.z+=B-2;continue
    yy=sum(v.co.z for v in o.data.vertices)/max(1,len(o.data.vertices));f=xform(o.name,yy)
    if f:
        for v in o.data.vertices:v.co.x=f(v.co.x)
for p in w['solids']:
    y=p['position'][1]+p['size'][1]/2;f=xform(p['name'],y)
    if f and p.get('footprint'):
        for q in p['footprint']:q[0]=f(q[0])
# Keep background simplified crowns away from the authored near-tree leaf detail.
for o in list(s.objects):
    if o.name.startswith('background_forest_canopy_'):
        for v in o.data.vertices:
            if math.hypot(v.co.x,v.co.y)<55:v.co.z-=15
route=[[3.2,14,B],[2.5,6,B],[2.5,5.6,B]]
for k in range(3):
    x=4.2 if k==1 else 2.5;y=B+k*3.6;start=5.6 if k%2==0 else -1.6;end=-1.6 if k%2==0 else 5.6
    for i in range(20):route.append([x,start+(end-start)*(i+.5)/20,y+(i+1)*.18])
    landing=-2.4 if k%2==0 else 6.4;route.append([x,landing,y+3.6])
    if k<2:
        nx=4.2 if k==0 else 2.5;route.extend([[nx,landing,y+3.6],[nx,end,y+3.6]])
for i in range(8):route.append([1.2+(3.2-(i+.5)*.25-1.2)*.65,-2.4,B+10.8+(i+1)*.15])
route.extend([[1.1,-2.4,B+12],[0,-2.4,B+12],[-1.6,-3,B+12]])
w['walkRoute']=route;w['revision']='neureoji-v92e';w['limitations'].append('상하 계단의 충돌을 피하는 병렬 계단 폭은 사진 기반 추정. 실측 구조도 아님.')
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(T));r=json.loads((R/'knowledge/sources/neureoji-v92/model.json').read_text(encoding='utf8'));r.update(revision=w['revision'],blend=T.relative_to(R).as_posix(),reviewPasses=5,assumptions=w['limitations']);r['export']=export('neureoji',O)
(R/'knowledge/sources/neureoji-v92/model.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('NEUREOJI_V92D_COMPLETE',json.dumps(r['export']),flush=True)
