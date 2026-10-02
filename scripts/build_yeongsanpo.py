"""Build three new editable .blend files and losslessly compressed web models.

Run: blender --background --factory-startup --python scripts/build_yeongsanpo.py -- --render
Only these generated outputs are replaced; existing city .blend files are untouched.
"""
import bpy, sys, json, gzip, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from yeongsanpo_interiors import history,literature
from yeongsanpo_literature_detail import literature
from yeongsanpo_gallery_detail import history
from yeongsanpo_outdoor import outdoor
from compact_glb import compact_glb

for name,builder,views in [
    ('yeongsanpo',outdoor,[('overview',(410,380,480),(0,0,35)),('wharf',(-117,15,162),(-159,-2,117)),('lower-deck',(-149,-4.68,113),(-148,-2.5,129)),('gallery',(112,8,40),(92,2,8)),('literature',(238,11,148),(220,2,108))]),
    ('yeongsanpo-history',history,[('interior',(-3.3,1.8,7.1),(0,1.7,-7)),('exhibition',(2.7,1.8,-4),(4.5,1.5,5))]),
    ('yeongsanpo-literature',literature,[('rooms',(5.9,1.75,4.5),(3.8,1.7,-6)),('library',(-4.2,1.75,3.8),(-5,1.6,-6)),('ceiling',(-1.7,1.75,1.5),(-2.0,4,-4)),('attic',(-7.8,5.1,2.3),(-5.4,4.5,-6))]),
]:
    if '--only' in sys.argv and name!=sys.argv[sys.argv.index('--only')+1]:continue
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
    bpy.context.preferences.filepaths.save_version=0
    g,world=builder(scene)
    if name!='yeongsanpo':world['lighting']=dict(exposure=1.08,ambient=.72,sun=.18)
    (ROOT/'outputs').mkdir(exist_ok=True);(ROOT/'public/models').mkdir(exist_ok=True)
    (ROOT/f'public/{name}-world.json').write_text(json.dumps(world,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    scene.world=bpy.data.worlds.new('Reference_daylight');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.60,.72,.77,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35 if name!='yeongsanpo' else .6
    ld=bpy.data.lights.new('Daylight','SUN');ld.energy=2.2 if name=='yeongsanpo' else .65;ld.angle=math.radians(18)
    lo=bpy.data.objects.new('Daylight',ld);scene.collection.objects.link(lo);lo.rotation_euler=(.45,-.4,-.7)
    cd=bpy.data.cameras.new('Reference_camera');cam=bpy.data.objects.new('Reference_camera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.clip_end=2000;cd.clip_start=.1;cd.lens=24
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    _,eye,target=views[0];cam.location=g.bp(*eye);cam.rotation_euler=(Vector(g.bp(*target))-cam.location).to_track_quat('-Z','Y').to_euler()
    # Omit intentionally hidden construction proxies from GLB as well as renders.
    for o in list(scene.objects):
        if o.hide_render and o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
    model=ROOT/f'public/models/{name}.glb'
    bpy.ops.export_scene.gltf(filepath=str(model),export_format='GLB',use_active_scene=True,export_cameras=False,export_lights=False,export_extras=True,export_apply=True,export_animations=False)
    if name=='yeongsanpo':print(compact_glb(model),flush=True)
    packed=gzip.compress(model.read_bytes(),compresslevel=9,mtime=0);compressed=model.with_suffix('.glb.gz')
    if not compressed.exists() or compressed.read_bytes()!=packed:
        staging=ROOT/'work'/f'{name}-compressed.tmp';staging.parent.mkdir(exist_ok=True)
        staging.write_bytes(packed);staging.replace(compressed)
    # The editable full-scene .blend and renders include both separate boat assets.
    # Browser world GLB remains static; runtime loads the two boats independently.
    for boat in world.get('boats',[]):
        with bpy.data.libraries.load(str(ROOT/f"outputs/{boat['id']}-detail.blend"),link=False) as (source,dest):dest.objects=source.objects
        root=bpy.data.objects.new('Dynamic_'+boat['id'],None);scene.collection.objects.link(root)
        root.location=g.bp(boat['home']['x'],boat['waterY'],boat['home']['z']);root.rotation_euler.z=boat['home']['yaw'];root['dynamic_boat_id']=boat['id']
        for obj in dest.objects:
            if obj and obj.type in ('MESH','FONT'):
                scene.collection.objects.link(obj);obj.parent=root
    output=ROOT/f'outputs/{name}-detail.blend'
    if '--output-blend' in sys.argv:
        if '--only' not in sys.argv:raise ValueError('--output-blend requires --only')
        output=ROOT/sys.argv[sys.argv.index('--output-blend')+1]
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(json.dumps(dict(model=name,objects=len(scene.objects),solids=len(g.solids),bytes=model.stat().st_size,gzipBytes=model.with_suffix('.glb.gz').stat().st_size)),flush=True)
    if '--render' in sys.argv:
        for view,eye,target in views:
            cam.location=g.bp(*eye);cam.rotation_euler=(Vector(g.bp(*target))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/f'outputs/{name}-{view}.png')
            if view=='overview':
                for o in scene.objects:
                    if o.get('hide_in_overview'):o.hide_render=True
            else:
                for o in scene.objects:
                    if o.get('hide_in_overview'):o.hide_render=False
            bpy.ops.render.render(write_still=True)
