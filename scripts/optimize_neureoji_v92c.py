"""Third pass: finish the stairwell notch and bound distant canopy download geometry."""
import bpy,math,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export,surface
O=R/'outputs/neureoji-v92';T=O/'neureoji-v92c.blend'
if T.exists():raise RuntimeError('Preserve saved artist revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'neureoji-v92b.blend'));s=bpy.context.scene;g=Geometry(s);w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'))
D=json.loads((R/'work/neureoji-v92/mesh.json').read_text());colors=['#486446','#52704b','#638451','#748c57','#56754d'];by=[([],[]) for _ in colors]
for o in list(s.objects):
    if o.name.startswith('background_forest_canopy_') or o.name=='walk-floor_top_deck':bpy.data.objects.remove(o,do_unlink=True)
w['solids']=[p for p in w['solids'] if p['name']!='walk-floor_top_deck']
pts=json.loads((R/'work/neureoji-v92/top-floor.json').read_text());deck=g.polygon('walk-floor_top_deck',pts,w['topDeckHeightMetres']-.18,.18,'#bbbdb3');deck['keep_web']=True;surface(deck,'concrete');w['solids']+=g.solids
# Background canopies are broad connected volumes; detailed cutout foliage stays near the tower.
for x,y,z,h,c in D['forest']:
    v,f=by[c];a=len(v);r=h*1.22
    for j in range(5):
        theta=math.pi*j/4;rr=math.sin(theta)*r;yy=y+h*.60+math.cos(theta)*h*.40
        for i in range(8):ang=math.tau*i/8;v.append((x+rr*math.cos(ang),yy,z+rr*math.sin(ang)))
    for j in range(4):
        for i in range(8):q=a+j*8+i;f.append((q,a+j*8+(i+1)%8,a+(j+1)*8+(i+1)%8,q+8))
for c,(v,f) in enumerate(by):
    o=g.mesh('background_forest_canopy_'+str(c),v,f,colors[c],smooth=True);o['keep_web']=True;o['no_shadow']=True
w['revision']='neureoji-v92c';(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(T));report=json.loads((R/'knowledge/sources/neureoji-v92/model.json').read_text(encoding='utf8'));report.update(revision=w['revision'],blend=T.relative_to(R).as_posix(),reviewPasses=3,assumptions=w['limitations'],backgroundCanopies=len(D['forest']));report['export']=export('neureoji',O)
(R/'knowledge/sources/neureoji-v92/model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('NEUREOJI_V92C_COMPLETE',json.dumps(report['export']),flush=True)
