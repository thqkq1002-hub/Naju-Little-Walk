"""Reimport the exported candidate GLB and verify/render the delivered asset."""
import bpy, argparse, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/npc-meshy-20261002'
parser=argparse.ArgumentParser();parser.add_argument('--character',required=True,choices=['baedoli','beodeuri','hongdoli','teacher'])
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);key=args.character;folder=OUT/key
glb=folder/f'{key}-colored-v4.glb';blend=folder/f'{key}-colored-v4.blend'
assert glb.exists() and blend.exists()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
ob=meshes[0];assert ob.get('npc_character')==key
assert len(ob.data.materials)==1
assert len(ob.data.uv_layers)>=1
points=[ob.matrix_world@v.co for v in ob.data.vertices]
assert all(math.isfinite(value) for p in points for value in p)
height=max(p.z for p in points)-min(p.z for p in points)
assert abs(height-ob['estimated_height_m'])<.0001
assert abs(min(p.z for p in points))<.0001
material=ob.data.materials[0]
textures=[n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
assert textures and textures[0].size[0]==2048
assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
report={'character':key,'glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'glb_bytes':glb.stat().st_size,
        'blend_bytes':blend.stat().st_size,'vertices':len(ob.data.vertices),'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),
        'height_m':height,'depth_m':max(p.y for p in points)-min(p.y for p in points),
        'materials':len(ob.data.materials),'embedded_atlas':list(textures[0].size),'rigged':False,'checks_passed':True}
(folder/'asset-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=32
scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.67,.69,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
target=Vector((0,0,height*.5))
for name,pos,power in [('Key',(-2,-3,4),280),('Fill',(2,-2,2),180),('Rim',(2,3,3),250)]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power*height*height;ld.size=4*height
    lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=Vector(pos)*height
    lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=max(height*1.18,(max(p.x for p in points)-min(p.x for p in points))*1.28)
for view,pos in [('front',(0,-3,.5)),('three-quarter',(1.3,-3,.65)),('back',(0,3,.5)),('side',(3,-.05,.5))]:
    cam.location=Vector(pos)*height;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(folder/f'preview-{view}.png');bpy.ops.render.render(write_still=True)
print(json.dumps(report))
