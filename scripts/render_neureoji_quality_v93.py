"""Review the authored tower and normal eye-height panorama, never resave the artist file."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'outputs/neureoji-v93'
rev=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'a'
bpy.ops.wm.open_mainfile(filepath=str(O/f'neureoji-quality-v93{rev}.blend'));s=bpy.context.scene
w=json.loads((R/'public/neureoji-world.json').read_text(encoding='utf8'));B=w['spawn']['height'];top=w['topDeckHeightMetres']
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=32
s.view_settings.view_transform='AgX';s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100
world=bpy.data.worlds.new('Review daylight');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.48,.67,.76,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;s.world=world
# The web sky does not cast shadows. EEVEE ignores exported no_shadow extras, so use its same map in the world.
sky=s.objects.get('Neureoji93_original_sky_dome');sky.hide_render=True
tex=world.node_tree.nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(R/'assets/neureoji-v93/sky-original.png'))
world.node_tree.links.new(tex.outputs['Color'],world.node_tree.nodes['Background'].inputs[0])
data=bpy.data.lights.new('Review sun','SUN');data.energy=3
ob=bpy.data.objects.new('Review sun',data);s.collection.objects.link(ob);ob.rotation_euler=(.45,-.4,-.5)
bpy.ops.object.camera_add();c=bpy.context.object;s.camera=c;c.data.clip_end=26000
def render(name,eye,target,lens):
    c.location=(eye[0],-eye[2],eye[1]);c.rotation_euler=(Vector((target[0],-target[2],target[1]))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens
    s.render.filepath=str(O/f'{name}-{rev}.png');bpy.ops.render.render(write_still=True)
render('tower',[-22,B+15,28],[.7,B+7,1],31)
render('entry',[3.2,B+1.72,16],[2.5,B+6,-1],24)
a=w['arrivals']['top'];eye=[a['x'],top+1.72,a['z']];yaw=a['yaw'];pitch=a['pitch']
render('panorama',eye,[eye[0]-math.sin(yaw)*1000,eye[1]+math.tan(pitch)*1000,eye[2]-math.cos(yaw)*1000],36/(2*1.6*math.tan(math.radians(30))))
render('deck',[-.7,top+1.72,-3.5],[.7,top+.9,.1],22)
print('NEUREOJI_REVIEW_'+rev,flush=True)
