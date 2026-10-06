"""Review the newly authored copy; never alter the saved editable scene."""
from pathlib import Path
import bpy,json,math,xml.etree.ElementTree as ET
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
out=root/'outputs/geumseonggwan-exclusive-v76'
bpy.ops.wm.open_mainfile(filepath=str(out/'geumseonggwan-exclusive-v76.blend'))
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
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
shots=[('overview',Vector((45,-145,125)),Vector((-10,27,0)),200),
       ('front',point(c,9,-48),point(c,4.7,10),None),
       ('roof-detail',point(c+10,13,-8),point(c,8.5,10),None),
       ('interior',point(c,2.6,6.2),point(c,5.3,15),None)]
for name,eye,target,ortho in shots:
    scene.view_settings.exposure=2.7 if name=='interior' else .4
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=2.0 if name=='interior' else .65
    cam.location=eye;cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO' if ortho else 'PERSP';cam.data.ortho_scale=ortho or 200;cam.data.lens=26 if name=='front' else 23
    scene.render.filepath=str(out/f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('REVIEW_RENDERED',name,flush=True)
