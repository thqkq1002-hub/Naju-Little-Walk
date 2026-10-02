"""Preserve Meshy originals; author reference colors, depth and size in Blender."""
import bpy, json, math, sys, argparse
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/npc-meshy-20261002'
TAG='v4'
CONFIG={'baedoli':1.20,'beodeuri':1.65,'hongdoli':1.05,'teacher':1.72}

def srgb_linear(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def back_color(key,x,z):
    if key=='baedoli':
        if z>.76:return (.96,.55,.10)
        if z>.24 and abs(x)<.3:return (1,.80,.36)
        return (.95,.73,.54)
    if key=='beodeuri':
        if z>.76:return (.075,.065,.055)
        if z<.055:return (.18,.15,.42)
        if z<.40:return (.54,.50,.73)
        if abs(x)>.16 and .51<z<.62:return (.97,.79,.66)
        if .53<z<.57:return (.18,.14,.39)
        return (.91,.47,.64)
    if key=='hongdoli':
        if z<.19:return (.02,.54,.74)
        if z>.6 and x>.24:return (.92,.49,.63)
        return (.94,.95,.98)
    if z>.91:return (.22,.13,.09)
    if z>.79:return (.94,.70,.53)
    if z<.065:return (.26,.16,.10)
    if z<.46 and abs(x)<.2:return (.20,.21,.24)
    if .41<z<.57 and abs(x)>.17:return (.94,.70,.53)
    return (.29,.47,.46)

def material(name):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=.82
    bsdf.inputs['Specular IOR Level'].default_value=.22
    return mat,bsdf

reports={}
parser=argparse.ArgumentParser()
parser.add_argument('--character',required=True,choices=list(CONFIG))
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
for key in [args.character]:
    height=CONFIG[key]
    folder=OUT/key
    blend=folder/f'{key}-colored-{TAG}.blend'
    glb=folder/f'{key}-colored-{TAG}.glb'
    if blend.exists() or glb.exists():raise RuntimeError('Refusing to overwrite '+str(blend))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(folder/'meshy-original.glb'))
    ob=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    ob.name='NPC_'+key
    image=bpy.data.images.load(str(OUT/'references'/f'{key}.png'))
    iw,ih=image.size
    pixels=np.array(image.pixels[:],dtype=np.float32).reshape(ih,iw,4)
    yy,xx=np.where(pixels[:,:,3]>.94)
    if not len(xx):raise RuntimeError('Missing opaque reference silhouette')
    uvbox=(float(xx.min()/iw),float(xx.max()/iw),float(yy.min()/ih),float(yy.max()/ih))
    coords=np.array([v.co[:] for v in ob.data.vertices])
    low=coords.min(axis=0);high=coords.max(axis=0)
    original_depth=float(high[1]-low[1])
    if key=='hongdoli':
        # Thin Meshy reconstruction: expand its existing closed depth; no paid retry.
        middle=(low[1]+high[1])/2
        for v in ob.data.vertices:v.co.y=(v.co.y-middle)*18
        ob.data.update()
    scale=height/(high[2]-low[2])
    center_x=(low[0]+high[0])/2
    for v in ob.data.vertices:
        v.co.x=(v.co.x-center_x)*scale;v.co.y*=scale;v.co.z=(v.co.z-low[2])*scale
    ob.data.update()
    coords=np.array([v.co[:] for v in ob.data.vertices]);low=coords.min(axis=0);high=coords.max(axis=0)
    # Untextured Meshy meshes may still contain an unrelated generated UV layer.
    # Replace it in this derived asset so the reference projection is the active UV.
    for layer in list(ob.data.uv_layers):ob.data.uv_layers.remove(layer)
    uv=ob.data.uv_layers.new(name='ReferenceFrontUV')
    uv.active_render=True
    colors=ob.data.color_attributes.new(name='AuthoredBackColors',type='BYTE_COLOR',domain='CORNER')
    # A new corner attribute reallocates Blender CustomData; reacquire UV handles.
    uv=ob.data.uv_layers['ReferenceFrontUV']
    front,bsdf=material(key+'_reference_front')
    texture=front.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image;texture.interpolation='Linear';texture.extension='EXTEND'
    front.node_tree.links.new(texture.outputs['Color'],bsdf.inputs['Base Color'])
    back,bsdf=material(key+'_authored_back')
    attr=back.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name=colors.name
    back.node_tree.links.new(attr.outputs['Color'],bsdf.inputs['Base Color'])
    ob.data.materials.clear();ob.data.materials.append(front);ob.data.materials.append(back)
    front_count=0
    for poly in ob.data.polygons:
        use_front=poly.normal.y<-.28
        poly.material_index=0 if use_front else 1
        poly.use_smooth=True
        front_count+=use_front
        for li in poly.loop_indices:
            p=ob.data.vertices[ob.data.loops[li].vertex_index].co
            u=(p.x-low[0])/(high[0]-low[0]);v=p.z/height
            uv.data[li].uv=(uvbox[0]+u*(uvbox[1]-uvbox[0]),uvbox[2]+v*(uvbox[3]-uvbox[2]))
            c=(1,1,1) if use_front else back_color(key,p.x/height,v)
            colors.data[li].color=tuple(srgb_linear(q) for q in c)+(1,)
    # Blend the illustrated front smoothly into authored side/rear colors, then
    # bake onto a normal atlas so the exported GLB uses portable PBR materials.
    for poly in ob.data.polygons:
        poly.material_index=0
        for li in poly.loop_indices:
            vertex=ob.data.vertices[ob.data.loops[li].vertex_index]
            c=back_color(key,vertex.co.x/height,vertex.co.z/height)
            weight=max(0.,-vertex.normal.y)**.65
            colors.data[li].color=tuple(srgb_linear(q) for q in c)+(weight,)
    tree=front.node_tree
    attr=tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='AuthoredBackColors'
    explicit_uv=tree.nodes.new('ShaderNodeUVMap');explicit_uv.uv_map='ReferenceFrontUV'
    tree.links.new(explicit_uv.outputs['UV'],texture.inputs['Vector'])
    alpha_mask=tree.nodes.new('ShaderNodeMath');alpha_mask.operation='GREATER_THAN';alpha_mask.inputs[1].default_value=.90
    tree.links.new(texture.outputs['Alpha'],alpha_mask.inputs[0])
    factor=tree.nodes.new('ShaderNodeMath');factor.operation='MULTIPLY'
    tree.links.new(alpha_mask.outputs[0],factor.inputs[0]);tree.links.new(attr.outputs['Alpha'],factor.inputs[1])
    mix=tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX'
    tree.links.new(factor.outputs[0],mix.inputs[0]);tree.links.new(attr.outputs['Color'],mix.inputs[1]);tree.links.new(texture.outputs['Color'],mix.inputs[2])
    tree.links.new(mix.outputs[0],front.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    ob.data.uv_layers.new(name='NpcAtlasUV')
    ob.data.uv_layers.active=ob.data.uv_layers['NpcAtlasUV']
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.data.uv_layers['NpcAtlasUV'].active_render=True
    atlas=bpy.data.images.new(key+'_authored_atlas',width=2048,height=2048,alpha=False)
    target=tree.nodes.new('ShaderNodeTexImage');target.image=atlas;tree.nodes.active=target
    bpy.context.scene.render.engine='CYCLES';bpy.context.scene.cycles.samples=1
    bpy.context.scene.render.bake.use_pass_direct=False;bpy.context.scene.render.bake.use_pass_indirect=False
    bpy.context.scene.render.bake.use_pass_color=True;bpy.context.scene.render.bake.margin=12
    bpy.ops.object.bake(type='DIFFUSE')
    atlas.filepath_raw=str(folder/f'{key}-atlas-{TAG}.png');atlas.file_format='PNG';atlas.save();atlas.pack()
    final,bsdf=material(key+'_authored_atlas_material')
    baked=final.node_tree.nodes.new('ShaderNodeTexImage');baked.image=atlas
    uvnode=final.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='NpcAtlasUV'
    final.node_tree.links.new(uvnode.outputs['UV'],baked.inputs['Vector']);final.node_tree.links.new(baked.outputs['Color'],bsdf.inputs['Base Color'])
    ob.data.materials.clear();ob.data.materials.append(final)
    for poly in ob.data.polygons:poly.material_index=0
    # Colors are baked; remove them so GLB viewers do not multiply them twice.
    ob.data.color_attributes.remove(ob.data.color_attributes['AuthoredBackColors'])
    ob['meshy_task_id']=json.loads((OUT/'tasks.json').read_text(encoding='utf-8'))[key]['task_id']
    ob['npc_character']=key;ob['rigged']=False;ob['authoring_stage']='colored_first_pass'
    ob['estimated_height_m']=height
    image.pack()
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_extras=True)
    # Diagnostic previews are saved after the authoring file, leaving the asset free of lights/cameras.
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=32
    scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new('World');scene.world.color=(.35,.35,.35)
    scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=.0
    target=Vector((0,0,height*.5))
    for name,pos,power in [('Key',(-2,-3,4),500),('Fill',(2,-2,2),300),('Rim',(2,3,3),400)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=power*height*height;ld.size=4*height
        lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=Vector(pos)*height
        lo.rotation_euler=(target-lo.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
    cam.data.type='ORTHO';cam.data.ortho_scale=max(height*1.18,(high[0]-low[0])*1.28)
    for view,pos in [('front',(0,-3,.5)),('three-quarter',(1.3,-3,.65)),('back',(0,3,.5)),('side',(3,-.05,.5))]:
        cam.location=Vector(pos)*height;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(folder/f'colored-{TAG}-{view}.png');bpy.ops.render.render(write_still=True)
    reports[key]={'height_m':height,'vertices':len(ob.data.vertices),'triangles':len(ob.data.polygons),'materials':1,'atlas_resolution':2048,
                  'front_triangles':front_count,'source_depth':original_depth,'final_depth_m':float(high[1]-low[1]),
                  'uv_reference_opaque_bbox':uvbox,'glb_bytes':glb.stat().st_size,'rigged':False,
                  'back_colors':'estimated palette by body region, not supplied rear-view artwork',
                  'hongdoli_depth_repair':key=='hongdoli'}
(OUT/args.character/f'coloring-{TAG}-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('Colored NPC first pass complete')
