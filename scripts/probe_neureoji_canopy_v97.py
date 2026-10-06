import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'outputs/relief-v96/neureoji-relief-v96.blend'))
roots=[]
for ob in bpy.context.scene.objects:
    if not ob.name.startswith('Neureoji93_woodland_crowns_'):continue
    assert len(ob.data.vertices)%12==0
    vertices=list(ob.data.vertices)
    for i in range(0,len(vertices),12):
        pts=[ob.matrix_world@v.co for v in vertices[i:i+12]]
        x=sum(v.x for v in pts)/12;z=-sum(v.y for v in pts)/12
        if 42<math.hypot(x,z)<240:
            roots.append(dict(x=x,z=z,base=min(v.z for v in pts),height=max(v.z for v in pts)-min(v.z for v in pts)))
O=R/'knowledge/sources/observatory-quality-v97';O.mkdir(parents=True,exist_ok=True)
(O/'candidate-roots.json').write_text(json.dumps(roots,indent=2),encoding='utf8')
print('NEAR_CANOPY_CANDIDATES',len(roots),flush=True)
