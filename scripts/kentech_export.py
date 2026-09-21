"""Linear-time export batching; avoids scene-wide operators on 11,000 objects."""
import bpy
def batch_and_export(scene,path):
    graph=bpy.context.evaluated_depsgraph_get();groups={};remove=[]
    for o in list(scene.objects):
        if o.type not in ['MESH','FONT']:continue
        mat=o.data.materials[0] if o.data.materials else None
        if not mat or o.get('campus_landmark'):continue
        alpha=mat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value
        if alpha<.99:continue
        key=(mat.name,bool(o.get('no_shadow')))
        verts,faces,smooth=groups.setdefault(key,([],[],[]))
        evaluated=o.evaluated_get(graph) if o.type=='FONT' else None
        mesh=evaluated.to_mesh() if evaluated else o.data
        offset=len(verts);matrix=o.matrix_world
        verts.extend(tuple(matrix@v.co) for v in mesh.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in mesh.polygons)
        smooth.extend(p.use_smooth for p in mesh.polygons)
        if evaluated:evaluated.to_mesh_clear()
        remove.append(o)
    print('EXPORT read geometry',len(remove),'objects',flush=True)
    bpy.data.batch_remove(ids=remove)
    print('EXPORT removed source objects',flush=True)
    for (material,no_shadow),(verts,faces,smooth) in groups.items():
        mesh=bpy.data.meshes.new('Batch_'+material);mesh.from_pydata(verts,[],faces);mesh.update();mesh.materials.append(bpy.data.materials[material])
        for face,flag in zip(mesh.polygons,smooth):face.use_smooth=flag
        o=bpy.data.objects.new('campus_batch_'+material,mesh);scene.collection.objects.link(o);o['no_shadow']=no_shadow
    print('EXPORT batched',len(scene.objects),'objects',flush=True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
