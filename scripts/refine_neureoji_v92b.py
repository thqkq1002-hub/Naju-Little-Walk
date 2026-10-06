"""Second authored pass: clear stair entry, correct geographic UVs, fuller wooded banks."""
import bpy,json,sys,math,random
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from yeongsanpo_geometry import Geometry
from scene_export_v91 import helpers,export,surface
O=R/'outputs/neureoji-v92';T=O/'neureoji-v92b.blend'
if T.exists():raise RuntimeError('Preserve saved source revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'neureoji-v92a.blend'));s=bpy.context.scene;g=Geometry(s);w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'));B=w['spawn']['height']
D=json.loads((R/'work/neureoji-v92/mesh.json').read_text());rng=random.Random(9222)
# Shorten the inner connector guard by one landing width so it cannot block the final flight.
removed=0
for o in list(s.objects):
    if o.name.startswith(('tower_connector_','background_forest_canopy_','near_deciduous_tree','v79_layered_leaf_canopies')):
        bpy.data.objects.remove(o,do_unlink=True);removed+=1
w['solids']=[p for p in w['solids'] if not p['name'].startswith('tower_connector_guard')]
for z in [-3.24,-1.56]:
    a,b=(2.45,z),(1.2,z);ya,yb=B+11.25,B+12
    g.tube('tower_connector_handrail',(a[0],ya+1.08,a[1]),(b[0],yb+1.08,b[1]),.045,'#63482d')
    for i in range(7):
        t=i/6;x=a[0]+(b[0]-a[0])*t;y=ya+(yb-ya)*t;g.box('tower_connector_baluster',x,y+.52,z,.055,1.04,.055,'#78583a',record=False)
    g.collider('tower_connector_guard',[[1.2,z-.06],[2.45,z-.06],[2.45,z+.06],[1.2,z+.06]],B+11.15,1.85)
# The terrain texture is georeferenced with north at the image's top, matching actual polygons.
ob=s.objects['ground_native_DSM_interpreted'];im=bpy.data.images.load(str(R/'work/neureoji-v92/original-landcover.png'),check_existing=False);im.pack()
for n in ob.data.materials[0].node_tree.nodes:
    if n.type=='TEX_IMAGE':n.image=im
for li,l in enumerate(ob.data.loops):
    v=ob.data.vertices[l.vertex_index].co;ob.data.uv_layers.active.data[li].uv=((v.x+3100)/6200,(2300+v.y)/5000)
colors=['#486446','#52704b','#638451','#748c57','#56754d'];batches=[([],[]) for _ in colors]
for x,y,z,h,c in D['forest']:
    verts,faces=batches[c];a=len(verts);r=h*1.22
    for j in range(7):
        theta=math.pi*j/6;rr=math.sin(theta)*r;yy=y+h*.60+math.cos(theta)*h*.40
        for i in range(12):
            angle=math.tau*i/12;rough=1+.08*math.sin(i*2.1+j+x*.01);verts.append((x+rr*math.cos(angle)*rough,yy,z+rr*math.sin(angle)*rough))
    for j in range(6):
        for i in range(12):q=a+j*12+i;faces.append((q,a+j*12+(i+1)%12,a+(j+1)*12+(i+1)%12,q+12))
for c,(verts,faces) in enumerate(batches):
    o=g.mesh('background_forest_canopy_'+str(c),verts,faces,colors[c],smooth=True);o['keep_web']=True;o['no_shadow']=True
for i in range(32):
    a=i*math.tau/32;rr=rng.uniform(13,30);x=math.cos(a)*rr;z=math.sin(a)*rr
    if z>5 and abs(x-3.2)<4:continue
    tree=Geometry(s);tree.tree('near_deciduous_tree',x,z,rng.uniform(1.7,2.4),i+920)
    for ob in tree.groups['02_Photo_Interior'].objects:ob.location.z+=B-2
bpy.context.view_layer.update();vegetation=helpers['vegetation']()
for o in s.objects:
    if o.type=='MESH' and 'connector_' in o.name:surface(o,'wood')
w['solids']+=g.solids;w['revision']='neureoji-v92b';w['limitations'].append('강둑 수림과 개별 수목은 사진·지형 참고 추정, 개별 나무 실측 아님.')
(R/'public/neureoji-world.json').write_text(json.dumps(w,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(T));report=json.loads((R/'knowledge/sources/neureoji-v92/model.json').read_text(encoding='utf8'));report.update(revision=w['revision'],blend=T.relative_to(R).as_posix(),reviewPasses=2,nearVegetation=vegetation,assumptions=w['limitations'])
report['export']=export('neureoji',O) if '--export-intermediate' in sys.argv else dict(skipped=True,reason='Dense intermediate geometry; use the optimized final export')
(R/'knowledge/sources/neureoji-v92/model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('NEUREOJI_V92B_COMPLETE',json.dumps(report['export']),flush=True)
