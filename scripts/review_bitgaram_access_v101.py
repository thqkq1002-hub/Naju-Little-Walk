"""Read-only Blender review; never save over an authoring source."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/bitgaram-v101';O.mkdir(parents=True,exist_ok=True)
after='--after' in sys.argv
source=R/json.loads((R/'public/bitgaram-park-world.json').read_text(encoding='utf8'))['navigationFromBlend'] if after else R/'outputs/terrain-v89/bitgaram-park-glo30-terrain-v89d.blend'
if '--overview' in sys.argv:source=R/json.loads((R/'knowledge/sources/bitgaram/access-v101/overview.json').read_text())['output']
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene
if not after:
 info=[]
 for o in s.objects:
  if o.type=='MESH' and any(t in o.name for t in ('slide','monorail','forest','station')):
   vv=[o.matrix_world@Vector(p) for p in o.bound_box]
   info.append(dict(name=o.name,vertices=len(o.data.vertices),bounds=[[min(p[k] for p in vv),max(p[k] for p in vv)] for k in range(3)]))
 (O/'source-inventory.json').write_text(json.dumps(info,indent=2),encoding='utf8')
for o in list(s.objects):
 if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.data.energy=2.3;sun.data.angle=.13;sun.rotation_euler=(.5,-.6,-.7)
s.world=bpy.data.worlds.new('Access review daylight');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.58,.73,.8,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.lens=40;cam.data.clip_end=2500
profiles=json.loads((R/('knowledge/sources/bitgaram/access-v101/navigation-profiles.json' if after else 'knowledge/sources/bitgaram/terrain-v89/navigation-profiles.json')).read_text())
st=profiles['stairs_route'];fo=profiles['forest_route']
views=[('aerial',(105,-175,130),(2,-55,42)),('gallery',(st[80][0],-st[80][2],st[80][1]+1.7),(st[110][0],-st[110][2],st[110][1]+1))]
if '--overview' in sys.argv:views=[('overview',(-170,-270,175),(0,-40,42))]
if '--aerial-only' in sys.argv:views=views[:1]
for name,pos,aim in views:
 cam.location=pos;cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler()
 for o in s.objects:
  lod=o.get('vegetation_lod')
  if lod:o.hide_render=(lod=='near')!=((o.location-cam.location).length<o.get('vegetation_distance',64))
 s.render.filepath=str(O/(name+('-after' if after else '-before')+'.png'));bpy.ops.render.render(write_still=True)
 print('REVIEW',name,flush=True)
