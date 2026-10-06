"""Render review views of the saved copy, without changing its editable source."""
from pathlib import Path
import bpy,json,math,sys,xml.etree.ElementTree as ET
from mathutils import Vector
root=Path(__file__).resolve().parents[1];out=root/'outputs/geumseonggwan-v78'
bpy.ops.wm.open_mainfile(filepath=str(out/'geumseonggwan-v78.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=950;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
world=json.loads((root/'public/city-world.json').read_text(encoding='utf-8'))
lat,lon=world['origin']['lat'],world['origin']['lon'];mx=111320*math.cos(math.radians(lat))
xml=ET.parse(root/'knowledge/sources/geumseonggwan.osm').getroot()
nodes={n.attrib['id']:((float(n.attrib['lon'])-lon)*mx,-(float(n.attrib['lat'])-lat)*111320) for n in xml.findall('node')}
way=next(w for w in xml.findall('way') if w.attrib['id']=='832423358')
pts=[nodes[n.attrib['ref']] for n in way.findall('nd')];a,b=pts[1:3];w=math.dist(a,b)
u=((b[0]-a[0])/w,(b[1]-a[1])/w);v=(u[1],-u[0]);c=world['architecture']['center']
def point(x,y,z):return Vector((a[0]+u[0]*x+v[0]*z,-a[1]-u[1]*x-v[1]*z,y))
cam=scene.camera
shots=[('front',point(c,8,-39),point(c,4.7,10),29),
       ('ikgong-detail',point(c-6,4.95,-6.5),point(c-6,6.2,2.4),45),
       ('ceiling',point(c,3.3,7.6),point(c,7.6,11),22),
       ('interior',point(c,2.6,6.2),point(c,5.3,15),23)]
if '--' in sys.argv:
    requested=set(sys.argv[sys.argv.index('--')+1:]);shots=[shot for shot in shots if shot[0] in requested]
for name,eye,target,lens in shots:
    inside=name in ['ceiling','interior']
    scene.view_settings.exposure=2.2 if inside else .4
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=2.0 if inside else .65
    cam.location=eye;cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=lens
    scene.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
    print('REVIEW_RENDERED',name,flush=True)
