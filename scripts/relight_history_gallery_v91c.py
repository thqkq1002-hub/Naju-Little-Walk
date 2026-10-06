"""Third review: light the craft cases and boat, preserving all prior revisions."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export
O=R/'outputs/history-gallery-v91';T=O/'yeongsanpo-history-complete-v91c.blend'
if T.exists():raise RuntimeError('Preserve saved artist revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'yeongsanpo-history-complete-v91b.blend'));s=bpy.context.scene;g=Geometry(s)
for o in s.objects:
    if o.type=='LIGHT':o.data.energy*=3
for x,z in [(-4.7,7.8),(-.6,8.3),(1.4,8.3),(3.4,8.3),(0,-7.2)]:
    data=bpy.data.lights.new('v91c_case_and_boat_light','AREA');data.energy=750;data.size=1.6
    ob=bpy.data.objects.new('v91c_case_and_boat_light',data);s.collection.objects.link(ob);ob.location=g.bp(x,3.12,z-1)
    ob.rotation_euler=(Vector(g.bp(x,1.05,z))-ob.location).to_track_quat('-Z','Y').to_euler()
    g.lights.append(dict(position=[x,2.95,z-.7],color='#fff4df',intensity=350,distance=5))
s.view_settings.view_transform='AgX';s.view_settings.exposure=.8
bpy.ops.wm.save_as_mainfile(filepath=str(T))
p=R/'public/yeongsanpo-history-world.json';w=json.loads(p.read_text(encoding='utf8'));w['lights']+=g.lights
for l in w['lights'][:13]:l['intensity']=max(l['intensity'],1100)
w['lighting']['ambient']=1.1;w['galleryRevision']='history-complete-v91c';p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
report=json.loads((R/'knowledge/sources/history-gallery-v91.json').read_text(encoding='utf8'));report.update(editedBlend=T.relative_to(R).as_posix(),revision=w['galleryRevision'],eyeLevelReviewPasses=3)
report['export']=export('yeongsanpo-history',O);(R/'knowledge/sources/history-gallery-v91.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('GALLERY_V91C_COMPLETE',flush=True)
