import bpy,json,collections
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
out=R/'outputs/yeongsanpo-v79';out.mkdir(exist_ok=True)
all=[]
for key in ['yeongsanpo','yeongsanpo-history','yeongsanpo-literature','najuho','wanggeonho']:
    bpy.ops.wm.open_mainfile(filepath=str(R/f'outputs/palette-v51/{key}-color-v51.blend'))
    obs=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        pts=[o.matrix_world@Vector(v) for v in o.bound_box]
        obs.append(dict(name=o.name,vertices=len(o.data.vertices),faces=len(o.data.polygons),materials=[m.name if m else None for m in o.data.materials],bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]))
    mats=[]
    for m in bpy.data.materials:
        bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        mats.append(dict(name=m.name,color=list(m.diffuse_color),base=list(bs.inputs['Base Color'].default_value) if bs else None,textures=[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.use_nodes else []))
    data=dict(key=key,objects=obs,materials=mats,images=[dict(name=i.name,size=list(i.size)) for i in bpy.data.images]);all.append(data)
    print(key,len(obs),sum(o['vertices'] for o in obs),len(mats),flush=True)
(out/'baseline-audit.json').write_text(json.dumps(all,ensure_ascii=False,indent=2),encoding='utf-8')
