"""Derive final floors, columns and guard envelopes from the saved Blender geometry."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/neureoji-v92'
bpy.ops.wm.open_mainfile(filepath=str(O/'neureoji-v92e.blend'));s=bpy.context.scene
p=R/'public/neureoji-world.json';w=json.loads(p.read_text(encoding='utf8'))
w['solids']=[q for q in w['solids'] if not q['name'].startswith('walk-floor') and not q['name'].endswith('_guard') and q['name']!='tower_steel_column']
def solid(name,pts,y,h,collision=False):w['solids'].append(dict(name=name,kind='building',position=[0,y,0],size=[1,h,1],footprint=pts,color='#c4cbbd',collision=collision))
for o in s.objects:
 if o.type!='MESH':continue
 if o.name.startswith('walk-floor') or o.name.startswith('tower_steel_column'):
    face=max((f for f in o.data.polygons if f.normal.z>.9),key=lambda f:f.area)
    vs=[o.matrix_world@o.data.vertices[i].co for i in face.vertices]
    low=min((o.matrix_world@v.co).z for v in o.data.vertices);high=max(v.z for v in vs)
    solid(o.name,[[v.x,-v.y] for v in vs],low,high-low,o.name.startswith('tower_steel_column'))
 if any(o.name.startswith(n) for n in ['tower_stair_handrail','tower_landing_handrail','tower_connector_handrail','tower_round_deck_handrail']):
    v=[o.matrix_world@q.co for q in o.data.vertices];n=len(v)//2;a=sum(v[:n],Vector())/n;b=sum(v[n:],Vector())/n
    dx,dz=b.x-a.x,-b.y+a.y;l=math.hypot(dx,dz)
    if l<.01:continue
    for i in range(math.ceil(l/.65)):
        count=math.ceil(l/.65);aa=a.lerp(b,i/count);bb=a.lerp(b,(i+1)/count);ux,uz=-dz/l*.055,dx/l*.055
        pts=[[aa.x+ux,-aa.y+uz],[bb.x+ux,-bb.y+uz],[bb.x-ux,-bb.y-uz],[aa.x-ux,-aa.y-uz]]
        low=min(aa.z,bb.z)-1;high=max(aa.z,bb.z)+.05
        solid(o.name+'_guard',pts,low,high-low,True)
w['navigationFromBlend']='outputs/neureoji-v92/neureoji-v92e.blend'
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
print('Synced visible floors and guard envelopes:',len(w['solids']),flush=True)
