"""Wrap a clearly labelled video-reference composite outside the empty viewing room."""
import bpy,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'outputs/bitgaram/bitgaram-observatory-panorama-v3.blend'
if out.exists():raise RuntimeError('Existing revision preserved')
bpy.ops.wm.open_mainfile(filepath=str(root/'outputs/bitgaram/bitgaram-observatory-empty.blend'))
for o in list(bpy.data.objects):
    if o.name.startswith(('context_','lake_osm_','photo_wrap_')):bpy.data.objects.remove(o,do_unlink=True)
# Photo remains bright and unlit rather than being tinted by the scene lights.
mat=bpy.data.materials.new('Video_reference_composite_NOT_documentary');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear()
outnode=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage')
tex.image=bpy.data.images.load(str(root/'public/panoramas/bitgaram-reference-composite.png'));tex.image.pack();tex.extension='EXTEND'
mat.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],outnode.inputs['Surface'])
vs=[];fs=[];cols=192;rows=64
for j in range(rows+1):
    phi=math.pi*j/rows
    for i in range(cols+1):
        a=math.tau*i/cols
        vs.append((500*math.sin(phi)*math.cos(a),500*math.sin(phi)*math.sin(a),1.65+500*math.cos(phi)))
for j in range(rows):
    for i in range(cols):
        a=j*(cols+1)+i;fs.append((a,a+1,a+cols+2,a+cols+1))
m=bpy.data.meshes.new('photo_panorama');m.from_pydata(vs,[],fs);m.update();uv=m.uv_layers.new(name='PanoramaUV')
for p in m.polygons:
    for li in p.loop_indices:
        idx=m.loops[li].vertex_index;j,i=divmod(idx,cols+1);uv.data[li].uv=(i/cols,min(1,max(0,.55+(.5-j/rows)*2)))
o=bpy.data.objects.new('photo_panorama',m);bpy.context.scene.collection.objects.link(o);m.materials.append(mat);o['photo_panorama']=True;o['reference_category']='Video-reference AI composite; unobserved directions synthesized'
# Thin clear glazing reveals the backdrop without the old blue-grey veil.
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('panoramic_glazing'):
        for old in o.data.materials:
            if old and old.use_nodes:
                bs=old.node_tree.nodes.get('Principled BSDF')
                if bs:bs.inputs['Alpha'].default_value=.06;bs.inputs['Roughness'].default_value=.2
p=root/'public/bitgaram-observatory-world.json';w=json.loads(p.read_text(encoding='utf-8'))
w['solids']=[s for s in w['solids'] if not s['name'].startswith(('context_','lake_osm_'))]
w['limitations']=['Empty interior; exterior is an AI-generated panorama referencing user video frames, not a documentary 360-degree photograph. Unobserved directions synthesized.']
p.write_text(json.dumps(w,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/bitgaram-observatory.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
bpy.context.scene.render.filepath=str(root/'outputs/bitgaram/observatory-panorama-review.png');bpy.ops.render.render(write_still=True)
