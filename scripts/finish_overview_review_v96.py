"""Retain GLB vertex colours in the editable Blender review, without changing geometry."""
import bpy,json,struct
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/relief-v96'
target=O/'bitgaram-overview-relief-v96b.blend'
if target.exists():raise RuntimeError('Preserve saved review revision')
bpy.ops.wm.open_mainfile(filepath=str(O/'bitgaram-overview-relief-v96.blend'))
for key in ['bitgaram-overview','bitgaram-overview-part2']:
    raw=(O/(key+'-before.glb')).read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);b=raw[28+n:]
    for node in g['nodes']:
        if 'mesh' not in node:continue
        for pi,p in enumerate(g['meshes'][node['mesh']]['primitives']):
            if 'COLOR_0' not in p['attributes']:continue
            ob=bpy.context.scene.objects[f"{key}:{node['name']}:{pi}"];a=g['accessors'][p['attributes']['COLOR_0']];v=g['bufferViews'][a['bufferView']]
            size=4 if a['type']=='VEC4' else 3;dt={5121:'u1',5123:'<u2',5126:'<f4'}[a['componentType']];bs=np.dtype(dt).itemsize
            cols=np.ndarray((a['count'],size),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',size*bs),bs)).astype(np.float32)
            if a.get('normalized'):cols/=255 if a['componentType']==5121 else 65535
            if size==3:cols=np.c_[cols,np.ones(len(cols))]
            layer=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');layer.data.foreach_set('color',cols.ravel())
            mat=ob.data.materials[0].copy();ob.data.materials[0]=mat
            shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Color'
            mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=mat.diffuse_color
            mat.node_tree.links.new(vc.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(mix.outputs[0],shader.inputs['Base Color'])
bpy.ops.wm.save_as_mainfile(filepath=str(target))
k=R/'knowledge/sources/observatory-relief-v96/overview-model.json';d=json.loads(k.read_text(encoding='utf8'));d['sourceBlender']=target.relative_to(R).as_posix();d['vertexColorsRetained']=True;k.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Use the same fixed camera as the previous review.
s=bpy.context.scene
for engine in ['BLENDER_EEVEE','BLENDER_EEVEE_NEXT']:
    try:s.render.engine=engine;break
    except TypeError:pass
s.render.resolution_x=1200;s.render.resolution_y=760;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
w=bpy.data.worlds.new('Review');w.use_nodes=True;bg=next(n for n in w.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.55,.70,.8,1);bg.inputs[1].default_value=.7;s.world=w
bpy.ops.object.light_add(type='SUN');bpy.context.object.data.energy=2.3;bpy.context.object.rotation_euler=(.5,-.6,-.7)
from mathutils import Vector
bpy.ops.object.camera_add();c=bpy.context.object;s.camera=c;c.data.lens=38;c.location=(-170,-270,175);c.rotation_euler=(Vector((0,-40,42))-c.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(O/'bitgaram-overview-after.png');bpy.ops.render.render(write_still=True)
