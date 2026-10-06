"""Second eye-level pass: illumination, clean headings and original exhibit artwork."""
import bpy,math,json,sys,random
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import export
O=R/'outputs/history-gallery-v91';S=O/'yeongsanpo-history-complete-v91.blend';T=O/'yeongsanpo-history-complete-v91b.blend'
if '--export-only' not in sys.argv:
    if T.exists():raise RuntimeError('Preserve existing artist revision; use a fresh output filename')
    bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
    w=json.loads((R/'public/yeongsanpo-history-world.json').read_text(encoding='utf8'))
    titles=['영산포의 유래','홍어와 사람들','포구의 맛','옹기와 살림']
    for o in list(s.objects):
        if o.name in ['label_'+t for t in titles] or o.name.startswith(('v91_scene_hill','v91_scene_water')):bpy.data.objects.remove(o,do_unlink=True)
    w['signs']=[p for p in w['signs'] if p['text'] not in titles]
    # Do not brighten the black ceiling: aim individual warm lights at the wall displays.
    for o in s.objects:
        if o.type=='LIGHT':o.data.energy*=5
    for light in w['lights']:light['intensity']*=3.2
    g=Geometry(s)
    for x in [-4.3,4.3]:
        for z in [-6,-2,2,6]:
            data=bpy.data.lights.new('v91b_display_spot','AREA');data.energy=190;data.size=1.5
            ob=bpy.data.objects.new('v91b_display_spot',data);s.collection.objects.link(ob);ob.location=g.bp(x,2.96,z)
            from mathutils import Vector
            ob.rotation_euler=(Vector(g.bp(math.copysign(5.75,x),1.6,z))-ob.location).to_track_quat('-Z','Y').to_euler()
    # Original continuous mountains instead of disconnected rectangular hill placeholders.
    front=Geometry(s,(1.45,9.29),math.pi)
    circles=[(-2.36,2.40,.44),(-1.37,2.32,.52),(-1.9,1.26,.50),(.72,2.4,.40),(1.68,2.42,.39),(2.47,1.79,.43),(.85,1.32,.37),(1.64,1.31,.36)]
    for k,(x,y,r) in enumerate(circles):
        for j,color in enumerate(['#a0b2a8','#7e9a91','#557d70']):
            points=[(x-r*.86,y-r*.12+j*r*.04,.092+j*.006)]
            for n in range(25):
                u=n/24;xx=x+(u-.5)*r*1.72;yy=y+r*(.07+j*.05+.10*math.sin(u*17+k)+.05*math.cos(u*39+j))
                points.append((xx,yy,.092+j*.006))
            points.append((x+r*.86,y-r*.12+j*r*.04,.092+j*.006))
            front.mesh('v91b_continuous_landscape',points,[tuple(range(len(points)))],color)
        front.box('v91b_landscape_water',x,y-r*.25,.12,r*1.50,r*.20,.010,'#759a9a',record=False)
    s.view_settings.view_transform='AgX'
    bpy.ops.wm.save_as_mainfile(filepath=str(T));w['galleryRevision']='history-complete-v91b'
    (R/'public/yeongsanpo-history-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
else:bpy.ops.wm.open_mainfile(filepath=str(T))
report=json.loads((R/'knowledge/sources/history-gallery-v91.json').read_text(encoding='utf8'));report['editedBlend']=T.relative_to(R).as_posix();report['revision']='history-complete-v91b';report['eyeLevelReviewPasses']=2
report['export']=export('yeongsanpo-history',O)
(R/'knowledge/sources/history-gallery-v91.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('V91B_COMPLETE',json.dumps(report['export']),flush=True)
